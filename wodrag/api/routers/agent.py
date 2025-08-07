"""Master agent endpoint for Litestar API."""

from litestar import Controller, Request, post
from litestar.response import Response
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS,
)

from wodrag.agents.master import MasterAgent
from wodrag.api.models.responses import AgentQueryResponse, APIResponse
from wodrag.api.models.workouts import AgentQueryRequest
from wodrag.conversation import ConversationValidationError, get_conversation_service


class AgentController(Controller):
    """Master agent controller."""

    path = "/api/v1/agent"

    @post("/query")
    async def query_agent(
        self,
        data: AgentQueryRequest,
        master_agent: MasterAgent,
        request: Request,
    ) -> Response[APIResponse[AgentQueryResponse]]:
        """Query the master agent with natural language and conversation context.

        Args:
            data: Request with natural language query and optional conversation_id
            master_agent: Injected MasterAgent

        Returns:
            APIResponse with agent's answer, conversation_id, and optional
            reasoning trace
        """
        try:
            # Get client identifier for rate limiting
            client_ip = request.client.host if request.client else "unknown"

            # Get conversation service
            conversation_service = get_conversation_service()

            # Get or create conversation with rate limiting
            conversation = conversation_service.get_or_create_conversation(
                data.conversation_id, client_identifier=client_ip
            )

            # Add user message to conversation with sanitization
            conversation_service.add_user_message(
                conversation.id, data.question, client_identifier=client_ip
            )

            # Get conversation context for the agent
            conversation_context = conversation_service.get_conversation_context(
                conversation.id
            )

            if data.verbose:
                # Get answer with reasoning trace
                answer, trace = master_agent.forward_verbose(
                    data.question, conversation_context=conversation_context
                )
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
                response_data = AgentQueryResponse(
                    question=data.question,
                    answer=answer,
                    verbose=False,
                    conversation_id=conversation.id,
                )

            # Add assistant message to conversation
            conversation_service.add_assistant_message(
                conversation.id, answer, client_identifier=client_ip
            )

            return Response(
                APIResponse(success=True, data=response_data), status_code=HTTP_200_OK
            )
        except ConversationValidationError as e:
            # Handle validation and security errors
            status_code = (
                HTTP_429_TOO_MANY_REQUESTS
                if "rate limit" in str(e).lower()
                else HTTP_400_BAD_REQUEST
            )

            return Response(
                APIResponse(success=False, data=None, error=str(e)),
                status_code=status_code,
            )
        except Exception as e:
            # Log the full error for debugging
            import traceback

            print(f"Agent query error: {e}")  # noqa: T201
            print(f"Traceback: {traceback.format_exc()}")  # noqa: T201

            return Response(
                APIResponse(success=False, data=None, error=str(e)),
                status_code=HTTP_400_BAD_REQUEST,
            )


# Export route handlers for main app
route_handlers = [AgentController]
