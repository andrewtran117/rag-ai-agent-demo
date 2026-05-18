"""Ingest PDFs from docs/ into ChromaDB."""

import os
from pypdf import PdfReader
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

DOCS_DIR = "docs"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def ingest():
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Created {DOCS_DIR}/ — drop your PDFs there and run again.")
        return

    pdf_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDFs found in {DOCS_DIR}/. Add some and run again.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_fn = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=embedding_fn
    )

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filename in pdf_files:
        filepath = os.path.join(DOCS_DIR, filename)
        print(f"Processing: {filename}")
        text = extract_text_from_pdf(filepath)
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({"source": filename, "chunk_index": i})

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.upsert(
            ids=all_ids[i : i + batch_size],
            documents=all_chunks[i : i + batch_size],
            metadatas=all_metadata[i : i + batch_size],
        )

    print(f"Ingested {len(all_chunks)} chunks from {len(pdf_files)} PDF(s).")


if __name__ == "__main__":
    ingest()
