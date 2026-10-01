import os
import chromadb
from chromadb.utils import embedding_functions
from core.config import POLICY_MD_PATH, CHROMA_PERSIST_DIR

chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
default_ef = embedding_functions.DefaultEmbeddingFunction()

def get_or_create_collection():
    """Retrieve or create the vector collection for policy knowledge chunks."""
    return chroma_client.get_or_create_collection(
        name="policy_knowledge",
        embedding_function=default_ef
    )

def parse_policy_markdown(file_path: str = POLICY_MD_PATH):
    """
    Parses the 20-page Markdown file using a robust line-by-line state machine.
    Handles any OS line endings (CRLF/LF) and variable spacing.
    """
    if not os.path.exists(file_path):
        print(f"❌ File does not exist at: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_meta = {}
    current_body = []
    in_yaml = False

    for line in lines:
        stripped = line.strip()

        # Detect YAML boundary
        if stripped == "---":
            if not in_yaml:
                # If we were previously collecting body clauses, save previous chunk
                if current_meta and current_body:
                    chunks.append({
                        "id": f"chunk_page_{current_meta.get('page_number', len(chunks) + 1)}",
                        "text": "\n".join(current_body).strip(),
                        "metadata": current_meta
                    })
                    current_meta = {}
                    current_body = []
                in_yaml = True
            else:
                # Exiting YAML block
                in_yaml = False
            continue

        if in_yaml:
            if ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"\'')
                if key in ["page_number", "sla_hours", "effective_year"]:
                    try:
                        current_meta[key] = int(val)
                    except ValueError:
                        current_meta[key] = val
                else:
                    current_meta[key] = val
        else:
            if current_meta:
                current_body.append(line.rstrip())

    # Save the final chunk at the end of file
    if current_meta and current_body:
        chunks.append({
            "id": f"chunk_page_{current_meta.get('page_number', len(chunks) + 1)}",
            "text": "\n".join(current_body).strip(),
            "metadata": current_meta
        })

    return chunks

def ingest_policy_to_chroma():
    """Batch insets and embeds parsed policy chunks into the ChromaDB collection."""
    collection = get_or_create_collection()
    
    chunks = parse_policy_markdown()
    if not chunks:
        print("No chunks parsed from markdown file. Please verify file path or formatting.")
        return 0

    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✓ Successfully ingested {len(ids)} policy chunks into ChromaDB!")
    return collection.count()

def query_policy(query_text: str, category_filter: str = None, n_results: int = 2):
    """
    Queries the vector store for semantic matches, applying category metadata filters if specified.
    """
    collection = get_or_create_collection()
    
    where_clause = None
    if category_filter and category_filter != "general":
        where_clause = {"category": category_filter}

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_clause
    )
    return results

if __name__ == "__main__":
    count = ingest_policy_to_chroma()
    print(f"Total entries in vector store: {count}")
    
    if count > 0:
        test_res = query_policy("Can I return an opened perfume?", category_filter="returns", n_results=1)
        print("\n=== Vector Search Test Result ===")
        if test_res["metadatas"] and test_res["metadatas"][0]:
            print("Matched Section:", test_res["metadatas"][0][0].get("section_title"))
            print("Snippet:", test_res["documents"][0][0][:180], "...")