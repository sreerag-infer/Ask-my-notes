# agent_graph.py - draw the agent loop yourself, as a LangGraph graph
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from tools import SYSTEM_PROMPT, search_notes, calculate, today, add_task

load_dotenv()
tools = [search_notes, calculate, today, add_task]
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0).bind_tools(tools)


def think(state: MessagesState):
    # Node 1: the AI reads the whole chat and decides what to do next
    reply = llm.invoke([SystemMessage(SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [reply]}

graph = StateGraph(MessagesState)
graph.add_node("think", think)
graph.add_node("tools", ToolNode(tools))         # Node 2: runs the tools
graph.add_edge(START, "think")                   # always start by thinking
graph.add_conditional_edges("think", tools_condition)  # tool? else END
graph.add_edge("tools", "think")                 # after a tool, think again
study_graph = graph.compile(checkpointer=InMemorySaver())  # with memory

if __name__ == "__main__":
    chat = {"configurable": {"thread_id": "student-1"}}   # one memory per chat
    while True:
        question = input("\nYou: ")
        if question.lower() in ("quit", "exit"):
            break
        user_msg = {"messages": [{"role": "user", "content": question}]}
        for event in study_graph.stream(user_msg, chat, stream_mode="updates"):

            for node, update in event.items():
                last = update["messages"][-1]
                if node == "tools":
                    print(f"  👀 [tools] {last.content[:80]}")
                elif last.tool_calls:
                    print("  🛠  [think] wants:", [c["name"] for c in last.tool_calls])
                else:
                    print("Agent:", last.content)

