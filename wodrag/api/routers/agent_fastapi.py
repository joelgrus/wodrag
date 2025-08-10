"""Master agent endpoint for FastAPI."""

import logging
from typing import Any

import dspy  # type: ignore
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

# Import singleton getters
from wodrag.api.main_fastapi import (
    get_conversation_service,
    get_global_rate_limiter,
    get_master_agent,
    get_rate_limiter,
)
from wodrag.api.models.responses import AgentQueryResponse, APIResponse
from wodrag.api.models.workouts import AgentQueryRequest
from wodrag.conversation import ConversationValidationError
from wodrag.conversation.security import RateLimiter
from wodrag.conversation.service import ConversationService

router = APIRouter(tags=["agent"])


def _get_client_identifier(request: Request) -> str:
    """Derive a stable client identifier using proxy headers if present.

    Preference order:
    - X-Forwarded-For: first IP in the list
    - X-Real-IP
    - request.client.host
    """
    try:
        # Standard proxy header, may contain comma-separated list
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # Take the left-most (original client)
            return xff.split(",")[0].strip()

        # Some proxies set X-Real-IP
        xri = request.headers.get("x-real-ip")
        if xri:
            return xri.strip()
    except Exception:
        # Fall through to FastAPI client if any parsing fails
        pass

    return request.client.host if request.client else "unknown"


@router.post("/agent/query", response_model=APIResponse[AgentQueryResponse])
async def query_agent(
    data: AgentQueryRequest,
    request: Request,
    master_agent: Any = Depends(get_master_agent),  # noqa: B008
    conversation_service: ConversationService = Depends(get_conversation_service),  # noqa: B008
    global_rate_limiter: RateLimiter = Depends(get_global_rate_limiter),  # noqa: B008
    per_client_rate_limiter: RateLimiter = Depends(get_rate_limiter),  # noqa: B008
) -> Any:
    """Query the master agent with natural language and conversation context.

    Args:
        data: Request with natural language query and optional conversation_id
        master_agent: Injected MasterAgent (singleton)
        conversation_service: Injected ConversationService (singleton)

    Returns:
        APIResponse with agent's answer, conversation_id, and optional
        reasoning trace
    """
    try:
        # Get client identifier for rate limiting (proxy-aware)
        client_ip = _get_client_identifier(request)

        # Log the incoming request
        logging.info(
            "Agent query request - Question: '%s...', Conversation ID: %s, Client: %s",
            data.question[:50],
            data.conversation_id,
            client_ip,
        )

        # Check global daily rate limit first
        if not global_rate_limiter.is_allowed("global"):
            raise ConversationValidationError(
                "We've reached our daily query limit to keep costs "
                "manageable. Please try again tomorrow (resets at "
                "midnight UTC). Thanks for understanding!"
            )

        # Check per-client hourly limit once per interaction
        if not per_client_rate_limiter.is_allowed(client_ip):
            raise ConversationValidationError(
                "You're sending requests too quickly. Please wait a bit "
                "and try again (per-client rate limit)."
            )

        # Get or create conversation (rate limiting handled above)
        conversation = conversation_service.get_or_create_conversation(
            data.conversation_id, client_identifier=client_ip
        )
        logging.debug(
            "Retrieved conversation: %s, Messages: %d",
            conversation.id,
            len(conversation.messages),
        )

        # Add user message to conversation with sanitization
        conversation_service.add_user_message(
            conversation.id, data.question, client_identifier=client_ip
        )

        # Get conversation context for the agent
        conversation_context = conversation_service.get_conversation_context(
            conversation.id
        )
        logging.debug(
            "Conversation context length: %d messages",
            len(conversation_context),
        )

        # Convert conversation context to DSPy History format
        history_messages = []
        for msg in conversation_context:
            # Convert to format expected by dspy.History
            # Each message should have question/answer keys for our signature
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                # For user messages, we'll store as question
                history_messages.append({"question": content, "answer": ""})
            elif role == "assistant" and history_messages:
                # For assistant messages, fill in the answer for the last question
                history_messages[-1]["answer"] = content
        
        history = dspy.History(messages=history_messages)

        logging.debug("Calling master agent with verbose=%s", data.verbose)
        if data.verbose:
            # Get answer with reasoning trace
            answer, trace = master_agent.forward_verbose(
                data.question, history=history
            )
            logging.debug("Got verbose answer: %s...", answer[:50])
            response_data = AgentQueryResponse(
                question=data.question,
                answer=answer,
                reasoning_trace=trace,
                verbose=True,
                conversation_id=conversation.id,
            )
        else:
            # Get simple answer
            answer = master_agent.forward(
                data.question,
                history=history,
            )
            logging.debug("Got answer: %s...", answer[:50])
            response_data = AgentQueryResponse(
                question=data.question,
                answer=answer,
                verbose=False,
                conversation_id=conversation.id,
            )
        logging.debug("Saving assistant response to conversation")

        # Add assistant message to conversation
        conversation_service.add_assistant_message(
            conversation.id, answer, client_identifier=client_ip
        )
        logging.debug("Assistant message saved successfully")

        return APIResponse(success=True, data=response_data)

    except ConversationValidationError as e:
        # Handle validation and security errors
        status_code = (
            429  # Too Many Requests
            if "rate limit" in str(e).lower()
            else 400  # Bad Request
        )

        return JSONResponse(
            content=APIResponse(success=False, data=None, error=str(e)).dict(),
            status_code=status_code,
        )
    except Exception as e:
        # Log the full error for debugging
        logging.error(f"Agent query error: {e}", exc_info=True)

        return JSONResponse(
            content=APIResponse(success=False, data=None, error=str(e)).dict(),
            status_code=500,
        )
