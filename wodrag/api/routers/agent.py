"""Master agent endpoint for Litestar API."""

from litestar import Controller, post
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST

from wodrag.agents.master import MasterAgent
from wodrag.api.models.responses import APIResponse, AgentQueryResponse
from wodrag.api.models.workouts import AgentQueryRequest


class AgentController(Controller):
    """Master agent controller."""

    path = "/api/v1/agent"

    @post("/query")
    async def query_agent(
        self,
        data: AgentQueryRequest,
        master_agent: MasterAgent,
    ) -> Response[APIResponse[AgentQueryResponse]]:
        """Query the master agent with natural language.

        Args:
            data: Request with natural language query
            master_agent: Injected MasterAgent

        Returns:
            APIResponse with agent's answer and optional reasoning trace
        """
        try:
            if data.verbose:
                # Get answer with reasoning trace
                answer, trace = master_agent.forward_verbose(data.question)
                response_data = AgentQueryResponse(
                    question=data.question,
                    answer=answer,
                    reasoning_trace=trace,
                    verbose=True,
                )
            else:
                # Get simple answer
                answer = master_agent.forward(data.question, verbose=False)
                response_data = AgentQueryResponse(
                    question=data.question,
                    answer=answer,
                    verbose=False,
                )

            return Response(
                APIResponse(success=True, data=response_data), status_code=HTTP_200_OK
            )
        except Exception as e:
            return Response(
                APIResponse(success=False, data=None, error=str(e)),
                status_code=HTTP_400_BAD_REQUEST,
            )


# Export route handlers for main app
route_handlers = [AgentController]