import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from rank_bm25 import BM25Okapi
import cohere
from app.state import AgentState

# Initialize external clients
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize local Vector Store (ChromaDB)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="research_cache")

def process_and_store_documents(scraped_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chunks scraped text and stores it in ChromaDB."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    all_chunks = []
    
    for item in scraped_data:
        text = item.get("extracted_content_preview", "")
        if not text or text == "Failed to fetch text":
            continue
            
        chunks = text_splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                "id": f"{item['url']}_chunk_{i}",
                "text": chunk,
                "metadata": {"url": item["url"], "title": item["title"]}
            }
            all_chunks.append(chunk_doc)
            
            # Add to ChromaDB
            collection.add(
                documents=[chunk],
                metadatas=[{"url": item["url"], "title": item["title"]}],
                ids=[chunk_doc["id"]]
            )
            
    return all_chunks

def rag_retriever_node(state: AgentState) -> Dict[str, Any]:
    """Chunks scraped data, stores it, and retrieves the most relevant context."""
    print("\n[RAG Agent] Initializing chunking and vector storage...")
    
    scraped_data = state.get("scraped_raw_data", [])
    if not scraped_data:
        print("[RAG Agent] No data to process.")
        return {"vector_store_status": "failed"}

    # 1. Chunk and Store
    all_chunks = process_and_store_documents(scraped_data)
    print(f"[RAG Agent] Stored {len(all_chunks)} chunks in ChromaDB.")
    
    # Safely get current sub-question
    plan = state.get("plan", {})
    idx = state.get("current_sub_question_index", 0)
    if idx >= len(plan.get("sub_questions", [])):
        return {"vector_store_status": "completed"}
        
    query = plan["sub_questions"][idx]
    
    # 2. Semantic Search (ChromaDB)
    print(f"[RAG Agent] Performing hybrid retrieval for: '{query}'")
    semantic_results = collection.query(
        query_texts=[query],
        n_results=10
    )
    retrieved_texts = semantic_results['documents'][0] if semantic_results['documents'] else []
    
    # 3. Keyword Search (BM25)
    tokenized_corpus = [chunk["text"].split(" ") for chunk in all_chunks]
    if tokenized_corpus:
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.split(" ")
        bm25_top_n = bm25.get_top_n(tokenized_query, [c["text"] for c in all_chunks], n=5)
        
        # Combine and deduplicate
        combined_texts = list(set(retrieved_texts + bm25_top_n))
    else:
        combined_texts = retrieved_texts

    # 4. Cohere Reranking
    if not combined_texts:
         return {"vector_store_status": "completed", "retrieved_context": []}
         
    try:
        rerank_hits = cohere_client.rerank(
            query=query,
            documents=combined_texts,
            top_n=5,
            model='rerank-english-v3.0'
        )
        
        final_context = [combined_texts[hit.index] for hit in rerank_hits.results]
        print(f"[RAG Agent] Successfully isolated the top {len(final_context)} most relevant context chunks.")
        
        return {
            "vector_store_status": "completed",
            # We store this specifically so the Writer Agent can access it next
            "current_context": final_context 
        }
    except Exception as e:
        print(f"[Error] Cohere Reranking failed: {e}")
        return {"vector_store_status": "completed", "current_context": combined_texts[:5]}