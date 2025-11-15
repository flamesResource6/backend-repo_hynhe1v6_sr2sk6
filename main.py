import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Article

app = FastAPI(title="News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "News API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Request models
class ArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    author: str
    category: str
    image_url: Optional[str] = None
    tags: Optional[List[str]] = []


@app.post("/api/articles")
def create_article(payload: ArticleCreate):
    try:
        article = Article(**payload.model_dump())
        inserted_id = create_document("article", article)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
def list_articles(category: Optional[str] = None, limit: int = 20):
    try:
        filter_dict = {"category": category} if category else {}
        docs = get_documents("article", filter_dict=filter_dict, limit=limit)
        # Convert ObjectId to string
        for d in docs:
            if isinstance(d.get("_id"), ObjectId):
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles/{article_id}")
def get_article(article_id: str):
    try:
        from bson import ObjectId
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article id")
        docs = get_documents("article", {"_id": ObjectId(article_id)}, limit=1)
        if not docs:
            raise HTTPException(status_code=404, detail="Article not found")
        doc = docs[0]
        doc["id"] = str(doc.pop("_id"))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
