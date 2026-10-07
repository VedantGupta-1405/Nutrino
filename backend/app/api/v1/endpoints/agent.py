"""
FastAPI router for the LangGraph agent chat endpoint.
Provides the conversational gateway to Nutrino's agentic reasoning and controlled tool layer.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agent.runtime import AgentRuntimeContext
from app.agent.schemas import AgentChatRequest, AgentChatResponse
from app.agent.service import agent_service
from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.exceptions.base import AppException
from app.llm.exceptions import (
    LLMParsingError,
    OllamaConnectionError,
    OllamaResponseError,
    OllamaTimeoutError,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the Nutrino AI Nutrition Agent",
    description=(
        "Sends a natural-language message to the LangGraph-orchestrated AI nutrition agent. "
        "The agent inspects context, calls controlled application tools deterministically, "
        "and responds with grounded nutritional feedback."
    ),
)
async def chat_with_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AgentChatResponse:
    """
    Executes the LangGraph nutrition agent within the authenticated user context.
    """
    runtime_context = AgentRuntimeContext(db=db, user=current_user)

    try:
        return await agent_service.chat(
            message=payload.message,
            runtime_context=runtime_context,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except OllamaConnectionError as exc:
        logger.error("Agent chat failed - Ollama connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please verify that the local Ollama server is running.",
        )
    except OllamaTimeoutError as exc:
        logger.error("Agent chat failed - Ollama timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timed out while processing the agent request.",
        )
    except (OllamaResponseError, LLMParsingError) as exc:
        logger.error("Agent chat failed - model response error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to process model response: {exc}",
        )
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in agent chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during agent reasoning.",
        )
