# services/rag_retriever.py
import os
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from config import (
    POLICY_DOCS_PATH,
    MILVUS_HOST,        # 新增配置，如 "localhost"
    MILVUS_PORT,        # 如 19530
    MILVUS_COLLECTION_NAME  # 如 "policy_rag"
)

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
            # 初始化 Milvus 连接
            connections.connect(
                alias="default",
                host=MILVUS_HOST or "localhost",
                port=MILVUS_PORT or "19530"
            )

            self.collection_name = MILVUS_COLLECTION_NAME or "policy_rag"
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

            # 加载原始文档（用于 TF-IDF 和 fallback）
            self.docs = np.load(POLICY_DOCS_PATH, allow_pickle=True)
            doc_texts = [doc.item()["content"] for doc in self.docs]

            # 构建 TF-IDF（关键词召回）
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2),
                max_features=10000
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_texts)

            # 确保 Milvus 集合存在
            self._ensure_collection_exists()

            self._initialized = True

    def _ensure_collection_exists(self):
        """确保 Milvus 集合已创建（仅用于检查，不负责插入数据）"""
        if not utility.has_collection(self.collection_name):
            raise RuntimeError(
                f"Milvus collection '{self.collection_name}' not found. "
                "Please run a script to build and insert policy embeddings into Milvus."
            )
        self.collection = Collection(self.collection_name)
        self.collection.load()  # 加载到内存以加速查询

    def _matches_metadata(self, doc: dict, filters: dict) -> bool:
        """Python 层面兜底过滤（Milvus 已支持下推，此函数可保留作兼容）"""
        for key, required_value in filters.items():
            if key in doc:
                if key == "min_app_version":
                    if doc[key] > required_value:
                        continue
                elif doc[key] != required_value:
                    return False
        return True

    def _hybrid_fusion(self, vector_results, keyword_results, top_k):
        """RRF 融合"""
        rrf_scores = {}
        k = 60
        for rank, item in enumerate(vector_results, start=1):
            rrf_scores[item["doc_id"]] = rrf_scores.get(item["doc_id"], 0) + 1.0 / (k + rank)
        for rank, item in enumerate(keyword_results, start=1):
            rrf_scores[item["doc_id"]] = rrf_scores.get(item["doc_id"], 0) + 1.0 / (k + rank)

        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        seen = set()
        final = []
        doc_map = {item["doc_id"]: item for item in (vector_results + keyword_results)}
        for doc_id, _ in fused:
            if doc_id not in seen and doc_id in doc_map:
                final.append(doc_map[doc_id])
                seen.add(doc_id)
                if len(final) >= top_k:
                    break
        return final

    def retrieve(self, query: str, top_k: int = 1, metadata_filter: dict = None, threshold: float = 0.75):
        try:
            # === 1. 向量检索（Milvus）===
            query_emb = self.model.encode([query]).tolist()[0]

            # 构建 Milvus 查询表达式（支持元数据过滤下推！）
            expr = None
            if metadata_filter:
                conditions = []
                for key, val in metadata_filter.items():
                    if key == "min_app_version":
                        # 注意：Milvus 不直接支持版本比较，需存为数值或字符串比较
                        # 此处简化为字符串前缀匹配或忽略，建议存 version_int
                        continue  # 或按业务逻辑处理
                    elif isinstance(val, str):
                        conditions.append(f'{key} == "{val}"')
                    else:
                        conditions.append(f'{key} == {val}')
                if conditions:
                    expr = " && ".join(conditions)

            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_emb],
                anns_field="embedding",
                param=search_params,
                limit=top_k * 3,
                expr=expr,  # ⬅️ 关键：过滤下推到 Milvus
                output_fields=["doc_id", "content", "deep_link"]
            )

            vector_candidates = []
            for hit in results[0]:
                score = hit.distance
                if score < threshold:
                    continue
                entity = hit.entity
                vector_candidates.append({
                    "text": entity.get("content", ""),
                    "score": float(score),
                    "deep_link": entity.get("deep_link", ""),
                    "doc_id": entity.get("doc_id", "")
                })

            # === 2. 关键词召回（TF-IDF）===
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
                    "score": score,
                    "deep_link": doc.get("deep_link", ""),
                    "doc_id": doc["id"]
                })

            # === 3. 融合 ===
            fused_results = self._hybrid_fusion(vector_candidates, keyword_candidates, top_k)

            logger.info(f"Hybrid RAG (Milvus+TFIDF) retrieved {len(fused_results)} results for: {query}")
            return fused_results

        except Exception as e:
            logger.error(f"Milvus hybrid retrieval error: {e}", exc_info=True)
            return []