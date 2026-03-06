import json
import numpy as np
from fastapi import FastAPI, Query
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import bm25s


courses = []

with open("dtu_courses.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        course = json.loads(line)
        cid = course.get("course_code", "")
        title = course.get("title", "")
        objectives = course.get("learning_objectives", [])

        fields = course.get("fields", {})
        department = fields.get("Department", "")
        course_type = fields.get("Course type", "")
        responsible = fields.get("Responsible", "")
        co_responsible = fields.get("Course co-responsible", "")
        
        # Remove course code from title
        if title and cid and title.startswith(f"{cid} "):
            title = title[len(cid)+1:].strip()
        
        doc_parts = [title]
        doc_parts.extend(objectives)
        if department:
            doc_parts.append(department)
        if course_type:
            doc_parts.append(course_type)
        if responsible:
            doc_parts.append(responsible)
        if co_responsible:
            if isinstance(co_responsible, list):
                doc_parts.extend(co_responsible)
            else:
                doc_parts.append(co_responsible)

        doc_text = "\n".join(doc_parts)
        
        courses.append({
            'id': cid,
            'title': title,
            'document': doc_text
        })

    logger.info(f"Loaded {len(courses)} courses.")
    # logger.info("Course data sample:")
    
    # for i, course in enumerate(courses[::100][:3]):
    #     logger.info(f"  {i+1}. {course['title']} ({course['id']}) - document: {course['document']}...")


# TF-IDF - sparse
sparse_retriever = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
sparse_matrix = sparse_retriever.fit_transform([c['document'] for c in courses])

# BM25 - sparse
docs = [c['document'] for c in courses]
corpus_tokens = bm25s.tokenize(docs)
bm25_retriever = bm25s.BM25()
bm25_retriever.index(corpus_tokens)

# Dense Retrieval
model_name = 'sentence-transformers/distiluse-base-multilingual-cased-v2'
dense_retriever = SentenceTransformer(model_name)
dense_embeddings = dense_retriever.encode([c['document'] for c in courses], convert_to_numpy=True)

logger.info(f"Successfully indexed {len(courses)} courses.")

app = FastAPI(title="DTU Course Information Retrieval API")

def search_courses(query: str, mode: str, alpha: float, top_k: int):
    """Core search logic using the pre-computed indices."""
    dense_scores = np.zeros(len(courses))
    sparse_scores = np.zeros(len(courses))
    
    if mode in ["dense", "hybrid"]:
        query_embedding = dense_retriever.encode([query])
        dense_scores = cosine_similarity(query_embedding, dense_embeddings)[0]
        
    if mode in ["sparse", "hybrid"]:
        query_vec = sparse_retriever.transform([query])
        sparse_scores = cosine_similarity(query_vec, sparse_matrix)[0]

    if mode in ["bm25", "hybrid"]:
        query_tokens = bm25s.tokenize([query])
        results_bm25, scores_bm25 = bm25_retriever.retrieve(query_tokens, k=len(courses))
        bm25_scores = np.zeros(len(courses))
        for i, idx in enumerate(results_bm25[0]):
            bm25_scores[idx] = scores_bm25[0][i]
        sparse_scores = bm25_scores
        
    if mode == "dense":
        final_scores = dense_scores
    elif mode == "sparse":
        final_scores = sparse_scores
    elif mode == "bm25":
        final_scores = sparse_scores
    else:  # hybrid
        final_scores = alpha * dense_scores + (1 - alpha) * sparse_scores
    
    top_indices = np.argsort(final_scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "course_id": courses[idx]['id'],
            "title": courses[idx]['title'],
            "score": float(final_scores[idx])
        })
    
    return results

@app.get("/v1/search")
def search_endpoint(
    query: str, 
    top_k: int = Query(10, description="Number of results to return"), 
    mode: str = Query("sparse", pattern="^(dense|sparse|hybrid|bm25)$"), 
    alpha: float = Query(0.5, ge=0.0, le=1.0)
):
    """Search courses by free text query."""
    results = search_courses(query, mode, alpha, top_k)
    return {
        "query": query,
        "results": results,
        "mode": mode
    }

@app.get("/v1/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "index_sizes": {
            "courses": len(courses)
        }
    }
