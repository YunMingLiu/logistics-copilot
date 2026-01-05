# scripts/build_policy_index_milvus.py
import numpy as np
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection, utility
)
from config import POLICY_DOCS_PATH, MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME

def main():
    # 加载文档
    docs = np.load(POLICY_DOCS_PATH, allow_pickle=True)
    print(f"Loaded {len(docs)} policy documents.")

    # 连接 Milvus
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

    collection_name = MILVUS_COLLECTION_NAME
    if utility.has_collection(collection_name):
        print(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)

    # 定义 Schema（根据你的文档字段调整）
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="deep_link", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="region", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="min_app_version", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)  # MiniLM-L12 输出 384 维
    ]
    schema = CollectionSchema(fields, description="Policy RAG Collection")
    collection = Collection(collection_name, schema)

    # 创建 HNSW 索引（高效近似搜索）
    collection.create_index(
        field_name="embedding",
        index_params={
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 8, "efConstruction": 64}
        }
    )

    # 编码并插入
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    contents = [d.item()["content"] for d in docs]
    embeddings = model.encode(contents, show_progress_bar=True)

    entities = [
        [d.item()["id"] for d in docs],
        [d.item()["content"] for d in docs],
        [d.item().get("deep_link", "") for d in docs],
        [d.item().get("region", "") for d in docs],
        [d.item().get("min_app_version", "") for d in docs],
        embeddings.tolist()
    ]

    batch_size = 1000
    total = len(docs)
    for i in range(0, total, batch_size):
        batch_entities = [e[i:i+batch_size] for e in entities]
        collection.insert(batch_entities)
        print(f"Inserted {min(i+batch_size, total)}/{total}")

    collection.flush()
    print(f"✅ Successfully built Milvus collection '{collection_name}' with {total} policies.")

if __name__ == "__main__":
    main()