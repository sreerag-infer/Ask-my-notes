# agent_langchain.py - the same agent in a few lines, with LangChain
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from tools import SYSTEM_PROMPT, search_notes, calculate, today, add_task

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

agent = create_agent(
    model=llm,
    tools=[search_notes, calculate, today, add_task],
    system_prompt=SYSTEM_PROMPT,
)

def ask_agent(question):
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    messages = result["messages"]
    # Collect the names of the tools the agent used, in order
    steps = [call["name"] for m in messages for call in getattr(m, "tool_calls", [])]
    return messages[-1].content, steps

if __name__ == "__main__":
    while True:
        question = input("\nYou: ")
        if question.lower() in ("quit", "exit"):
            break
        answer, steps = ask_agent(question)
        print("  🛠  tools used:", steps or "none")
        print("Agent:", answer)
