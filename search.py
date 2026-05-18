"""Search ChromaDB for relevant document chunks."""

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "documents"


def search_docs(query: str, top_k: int = 5) -> list[dict]:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_fn = DefaultEmbeddingFunction()
    collection = client.get_collection(
        name=COLLECTION_NAME, embedding_function=embedding_fn
    )

    results = collection.query(query_texts=[query], n_results=top_k)

    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
            }
        )
    return formatted


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "What is this document about?"
    results = search_docs(query)
    for r in results:
        print(f"\n[{r['source']} chunk {r['chunk_index']}]")
        print(r["text"][:200] + "...")
