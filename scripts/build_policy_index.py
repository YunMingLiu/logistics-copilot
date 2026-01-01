# scripts/build_policy_index.py
import json, numpy as np, faiss
from sentence_transformers import SentenceTransformer
from config.settings import settings

def main():
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    docs = []
    texts = []
    with open("data/policy_docs.jsonl") as f:
        for line in f:
            doc = json.loads(line)
            docs.append(doc)
            texts.append(doc["content"])
    
    embeddings = model.encode(texts, show_progress_bar=True)
    faiss.normalize_L2(embeddings)
    
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype('float32'))
    
    faiss.write_index(index, settings.POLICY_INDEX_PATH)
    np.save(settings.POLICY_DOCS_PATH, np.array(docs, dtype=object))
    print(f"✅ Built index with {len(docs)} policies")

if __name__ == "__main__":
    main()