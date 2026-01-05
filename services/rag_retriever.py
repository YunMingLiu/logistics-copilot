# services/rag_retriever.py
import os
import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import POLICY_INDEX_PATH, POLICY_DOCS_PATH

logger = logging.getLogger(__name__)

class RAGPolicyRetriever:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            if not os.path.exists(POLICY_INDEX_PATH):
                raise FileNotFoundError("Policy FAISS index not found. Run build_policy_index.py first.")
            
            # 向量模型 & FAISS
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.index = faiss.read_index(POLICY_INDEX_PATH)
            self.docs = np.load(POLICY_DOCS_PATH, allow_pickle=True)

            # 构建 TF-IDF 倒排索引（用于关键词召回）
            doc_texts = [doc.item()["content"] for doc in self.docs]
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2),  # 支持 bi-gram
                max_features=10000
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_texts)

            self._initialized = True

    def _matches_metadata(self, doc: dict, filters: dict) -> bool:
        """根据元数据过滤（如 region, app_version）"""
        for key, required_value in filters.items():
            if key in doc:
                if key == "min_app_version":
                    # 简化版本比较（实际可用 packaging.version）
                    if doc[key] > required_value:
                        continue
                elif doc[key] != required_value:
                    return False
        return True

    def _hybrid_fusion(self, vector_results, keyword_results, top_k):
        """
        使用 Reciprocal Rank Fusion (RRF) 融合两个结果列表
        RRF score = sum(1 / (k + rank))
        这里 k=60 是常用默认值
        """
        rrf_scores = {}
        k = 60

        # 向量结果按顺序赋 rank（从1开始）
        for rank, item in enumerate(vector_results, start=1):
            doc_id = item["doc_id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)

        # 关键词结果
        for rank, item in enumerate(keyword_results, start=1):
            doc_id = item["doc_id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)

        # 按 RRF 分数排序
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        # 取回完整文档信息（去重）
        seen = set()
        final_results = []
        all_results = vector_results + keyword_results
        doc_map = {item["doc_id"]: item for item in all_results}

        for doc_id, _ in fused:
            if doc_id not in seen and doc_id in doc_map:
                final_results.append(doc_map[doc_id])
                seen.add(doc_id)
                if len(final_results) >= top_k:
                    break

        return final_results

    def retrieve(self, query: str, top_k: int = 1, metadata_filter: dict = None, threshold: float = 0.75):
        """
        混合检索：关键词（TF-IDF） + 向量（FAISS）
        """
        try:
            # === 向量召回 ===
            emb = self.model.encode([query])
            faiss.normalize_L2(emb)
            D_vec, I_vec = self.index.search(emb.astype('float32'), k=top_k * 3)

            vector_candidates = []
            for score, idx in zip(D_vec[0], I_vec[0]):
                if score < threshold:
                    continue
                doc = self.docs[idx].item()
                if metadata_filter and not self._matches_metadata(doc, metadata_filter):
                    continue
                vector_candidates.append({
                    "text": doc["content"],
                    "score": float(score),
                    "deep_link": doc.get("deep_link", ""),
                    "doc_id": doc["id"]
                })

            # === 关键词召回（TF-IDF）===
            query_tfidf = self.tfidf_vectorizer.transform([query])
            sim_scores = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()
            top_indices = np.argsort(sim_scores)[::-1][:top_k * 3]

            keyword_candidates = []
            for idx in top_indices:
                score = float(sim_scores[idx])
                if score <= 0:
                    break
                doc = self.docs[idx].item()
                if metadata_filter and not self._matches_metadata(doc, metadata_filter):
                    continue
                keyword_candidates.append({
                    "text": doc["content"],
                    "score": score,  # TF-IDF 相似度（0~1）
                    "deep_link": doc.get("deep_link", ""),
                    "doc_id": doc["id"]
                })

            # === 融合 ===
            fused_results = self._hybrid_fusion(vector_candidates, keyword_candidates, top_k)

            logger.info(f"Hybrid RAG retrieved {len(fused_results)} results for: {query}")
            return fused_results

        except Exception as e:
            logger.error(f"Hybrid RAG retrieval error: {e}", exc_info=True)
            return []