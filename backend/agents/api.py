# backend/agents/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .langgraph_utils import create_langgraph

graph = create_langgraph()
app = FastAPI()


class Query(BaseModel):
    query: str


@app.post("/api/cooking")
async def cooking_endpoint(query: Query):
    try:
        result = graph.invoke({"messages": [{"role": "user", "content": query.query}]})
        return {"response": result["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
