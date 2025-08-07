"""Master agent endpoint for Litestar API."""

from litestar import Controller, post
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST

from wodrag.agents.master import MasterAgent
from wodrag.api.models.responses import AgentQueryResponse, APIResponse
from wodrag.api.models.workouts import AgentQueryRequest
from wodrag.conversation import get_conversation_service


class AgentController(Controller):
    """Master agent controller."""

    path = "/api/v1/agent"

    @post("/query")
    async def query_agent(
        self,
        data: AgentQueryRequest,
        master_agent: MasterAgent,
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
            # Get conversation service
            conversation_service = get_conversation_service()

            # Get or create conversation
            conversation = conversation_service.get_or_create_conversation(
                data.conversation_id
            )

            # Add user message to conversation
            conversation_service.add_user_message(conversation.id, data.question)

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
            conversation_service.add_assistant_message(conversation.id, answer)

            return Response(
                APIResponse(success=True, data=response_data), status_code=HTTP_200_OK
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
