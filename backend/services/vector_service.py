"""ChromaDB 向量检索服务：错题语义检索（找同类题 / RAG 上下文）。
向量化复用硅基流动 embeddings 接口（BAAI/bge-m3）；未配置时自动降级为关键词检索。
"""
import logging

logger = logging.getLogger(__name__)

_collection = None
_collection_name = None


def _get_collection():
    global _collection, _collection_name
    from config import settings

    if _collection is not None and _collection_name == settings.chroma_collection:
        return _collection

    import chromadb

    client = chromadb.PersistentClient(path=settings.chroma_dir)
    try:
        _collection = client.get_collection(settings.chroma_collection)
    except Exception:
        _collection = client.create_collection(
            name=settings.chroma_collection, metadata={"hnsw:space": "cosine"}
        )
    _collection_name = settings.chroma_collection
    return _collection


def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用硅基流动 embedding 生成向量；失败时返回空（调用方降级）。"""
    try:
        from openai import OpenAI

        from config import settings

        client = OpenAI(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
        )
        resp = client.embeddings.create(model="BAAI/bge-m3", input=texts)
        return [d.embedding for d in resp.data]
    except Exception as e:
        logger.warning("Embedding 失败：%s", e)
        return []


def upsert(question_id: int, text: str, subject: str = "", kp: str = ""):
    """新增/更新一道错题的向量。"""
    embedding = embed_texts([text])
    if not embedding:
        logger.warning("跳过向量化（embedding 不可用）：#%s", question_id)
        return
    _get_collection().upsert(
        ids=[str(question_id)],
        embeddings=embedding,
        documents=[text],
        metadatas=[{"subject": subject, "knowledge_point": kp}],
    )


def delete(question_id: int):
    try:
        _get_collection().delete(ids=[str(question_id)])
    except Exception:
        pass


def search(text: str, k: int = 3) -> list[dict]:
    """语义搜索相似错题；embedding 不可用时降级为空列表。"""
    embedding = embed_texts([text])
    if not embedding:
        return []
    try:
        res = _get_collection().query(query_embeddings=embedding, n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [
            {"content": doc, "metadata": meta}
            for doc, meta in zip(docs, metas)
        ]
    except Exception as e:
        logger.warning("向量检索失败：%s", e)
        return []
