"""
FastAPI Router for LunarVision Offline-First AI Chatbot
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.chatbot_service import chatbot_service

router = APIRouter()


class ChatQueryRequest(BaseModel):
    message: str = Field(..., description="User query or question", example="What is RANSAC?")
    is_online: bool = Field(True, description="Flag indicating if client has active internet connectivity")


class ChatQueryResponse(BaseModel):
    answer: str
    mode: str
    source: str
    citations: list
    confidence: float
    timestamp: str
    suggested_questions: list


@router.post("", response_model=ChatQueryResponse)
@router.post("/", response_model=ChatQueryResponse)
async def process_chat_query(payload: ChatQueryRequest):
    """
    Process user query and return chatbot response.
    Routes between local knowledge base and online news/retrieval system based on is_online.
    """
    try:
        res = chatbot_service.process_query(payload.message, payload.is_online)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot engine error: {str(e)}")


@router.get("/status")
async def get_chat_status():
    """
    Returns health, version, last_updated timestamp, and knowledge base metadata.
    """
    kb = chatbot_service.kb_data
    return {
        "status": "online",
        "last_sync": chatbot_service.last_sync_time,
        "kb_version": kb.get("version", "1.0.0"),
        "last_updated": kb.get("last_updated", "2026-09-06T14:18:00Z"),
        "total_faqs": len(kb.get("faqs", [])),
        "total_news_items": len(kb.get("latest_news_cache", []))
    }


@router.get("/sync")
async def sync_knowledge():
    """
    Triggers synchronization mechanism to retrieve latest news and update knowledge cache.
    """
    try:
        sync_result = chatbot_service.sync_latest_knowledge()
        return sync_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge synchronization failed: {str(e)}")


@router.get("/knowledge")
async def get_full_knowledge():
    """
    Returns full offline JSON knowledge base payload for client-side IndexedDB caching.
    """
    return chatbot_service.kb_data
