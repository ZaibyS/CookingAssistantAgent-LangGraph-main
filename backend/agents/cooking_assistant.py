"""Cooking Assistant App with LangGraph and FastAPI"""

import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langchain.chat_models import init_chat_model
from langchain.callbacks.tracers import LangChainTracer
from langchain_core.messages import AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from prompts import (
    system_prompt_classifier,
    react_template,
    system_prompt_researcher,
)
from logger import setup_logger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Setup
logger = setup_logger()
load_dotenv()
langsmith_tracer = LangChainTracer()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILT_API_KEY = os.getenv("TAVILT_API_KEY")
llm = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=OPENAI_API_KEY)
tools = [TavilySearchResults(max_results=3, tavily_api_key=TAVILT_API_KEY)]


# LangGraph State
class State(TypedDict):
    messages: Annotated[list, add_messages]


# LangGraph Nodes
def classifier_agent(state: State, system_prompt=system_prompt_classifier):
    system_message = SystemMessage(content=system_prompt)
    messages_with_system = [system_message] + state["messages"]
    logger.critical(messages_with_system)
    response_classifier = llm.invoke(messages_with_system)
    logger.critical(response_classifier)
    return {"messages": [response_classifier]}


def refusal(state: State):
    return {"messages": [AIMessage(content="Your Query is not related to Cooking.")]}


prompt = system_prompt_researcher + react_template
researcher_prompt = PromptTemplate.from_template(prompt)
react_agent = create_react_agent(llm, tools, researcher_prompt)
agent_executor_researcher = AgentExecutor(
    agent=react_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)


def researcher_agent(state: State):
    user_input = state["messages"][-2].content
    response = agent_executor_researcher.invoke(
        {"input": user_input, "chat_history": ""}
    )
    return {"messages": [AIMessage(content=response["output"])]}


def decide_next_node(state: State):
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        if last_message.content.lower() == "relevant":
            return "researcher_agent"
        elif last_message.content.lower() == "irrelevant":
            return "refusal"
    return "refusal"


# LangGraph Construction
graph_builder = StateGraph(State)
graph_builder.add_node("classifier_agent", classifier_agent)
graph_builder.add_node("refusal", refusal)
graph_builder.add_node("researcher_agent", researcher_agent)
graph_builder.add_edge(START, "classifier_agent")
graph_builder.add_conditional_edges(
    "classifier_agent",
    decide_next_node,
    {
        "researcher_agent": "researcher_agent",
        "refusal": "refusal",
    },
)
graph_builder.add_edge("researcher_agent", END)
graph_builder.add_edge("refusal", END)
graph = graph_builder.compile()

# FastAPI Setup
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


# Run the App
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
