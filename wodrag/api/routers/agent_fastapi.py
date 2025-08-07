"""Master agent endpoint for FastAPI."""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from wodrag.agents.master import MasterAgent
from wodrag.api.models.responses import AgentQueryResponse, APIResponse
from wodrag.api.models.workouts import AgentQueryRequest
from wodrag.conversation import ConversationValidationError
from wodrag.conversation.service import ConversationService

# Import singleton getters
from wodrag.api.main_fastapi import get_master_agent, get_conversation_service

router = APIRouter(tags=["agent"])

@router.post("/agent/query", response_model=APIResponse[AgentQueryResponse])
async def query_agent(
    data: AgentQueryRequest,
    request: Request,
    master_agent: MasterAgent = Depends(get_master_agent),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
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
        # Get client identifier for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Log the incoming request
        logging.info(f"Agent query request - Question: '{data.question[:50]}...', Conversation ID: {data.conversation_id}, Client: {client_ip}")

        # Get or create conversation with rate limiting
        conversation = conversation_service.get_or_create_conversation(
            data.conversation_id, client_identifier=client_ip
        )
        logging.debug(f"Retrieved conversation: {conversation.id}, Messages: {len(conversation.messages)}")

        # Add user message to conversation with sanitization
        conversation_service.add_user_message(
            conversation.id, data.question, client_identifier=client_ip
        )

        # Get conversation context for the agent
        conversation_context = conversation_service.get_conversation_context(
            conversation.id
        )
        logging.debug(f"Conversation context: {len(conversation_context)} messages")

        logging.debug(f"Calling master agent with verbose={data.verbose}")
        if data.verbose:
            # Get answer with reasoning trace
            answer, trace = master_agent.forward_verbose(
                data.question, conversation_context=conversation_context
            )
            logging.debug(f"Got verbose answer: {answer[:50]}...")
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
                conversation_context=conversation_context,
                verbose=False,
            )
            logging.debug(f"Got answer: {answer[:50]}...")
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
            status_code=status_code
        )
    except Exception as e:
        # Log the full error for debugging
        logging.error(f"Agent query error: {e}", exc_info=True)

        return JSONResponse(
            content=APIResponse(success=False, data=None, error=str(e)).dict(),
            status_code=500
        )