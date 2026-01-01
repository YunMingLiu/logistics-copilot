# services/rag_retriever.py
import os
import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
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
            
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.index = faiss.read_index(POLICY_INDEX_PATH)
            self.docs = np.load(POLICY_DOCS_PATH, allow_pickle=True)
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

    def retrieve(self, query: str, top_k: int = 1, metadata_filter: dict = None, threshold: float = 0.75):
        """
        返回匹配的政策片段
        :param query: 用户问题
        :param top_k: 返回 top k 个
        :param metadata_filter: 如 {"region": "north", "min_app_version": "2.3.0"}
        :param threshold: 相似度阈值（余弦）
        :return: [{"text", "score", "deep_link", "doc_id"}, ...]
        """
        try:
            emb = self.model.encode([query])
            faiss.normalize_L2(emb)
            D, I = self.index.search(emb.astype('float32'), k=top_k * 3)  # 多召回后过滤

            results = []
            for score, idx in zip(D[0], I[0]):
                if score < threshold:
                    continue
                doc = self.docs[idx].item()  # np.object_ → dict
                
                if metadata_filter and not self._matches_metadata(doc, metadata_filter):
                    continue

                results.append({
                    "text": doc["content"],
                    "score": float(score),
                    "deep_link": doc.get("deep_link", ""),
                    "doc_id": doc["id"]
                })
                if len(results) >= top_k:
                    break

            logger.info(f"RAG retrieved {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}", exc_info=True)
            return []