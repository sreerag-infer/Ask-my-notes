# study_crew.py - a team of AI agents that makes a study plan from your notes
import json
import urllib.request
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv("../backend/.env")            # reuse the same GROQ_API_KEY
llm = LLM(model="groq/openai/gpt-oss-120b", temperature=0.3)

@tool("Ask My Notes")
def ask_my_notes(question: str) -> str:
    """Ask the student's notes a question. Our Day 2 backend must be running."""
    body = json.dumps({"question": question}).encode()
    request = urllib.request.Request(
        "http://localhost:8000/ask", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())["answer"]

researcher = Agent(
    role="Notes Researcher",
    goal="Find the most important facts about {topic} in the student's notes",
    backstory="You are careful. You only report what the notes really say.",
    tools=[ask_my_notes],
    llm=llm,
    verbose=True,
)

coach = Agent(
    role="Study Coach",
    goal="Turn the research into a simple study plan and a short quiz",
    backstory="You are a kind teacher who explains things in simple words.",
    llm=llm,
    verbose=True,
)

research_task = Task(
    description="Use Ask My Notes 2 or 3 times to collect the key points about {topic}.",
    expected_output="A bullet list of 5 to 8 key points from the notes.",
    agent=researcher,
)

plan_task = Task(
    description="Using the research, write a 3-day study plan for {topic} "
                "and a 5-question quiz with answers.",
    expected_output="Markdown with Day 1, Day 2, Day 3 sections, then the quiz.",
    agent=coach,
    context=[research_task],          # the coach reads the researcher's work
    output_file="study_plan.md",
)

crew = Crew(
    agents=[researcher, coach],
    tasks=[research_task, plan_task],
    process=Process.sequential,       # one after the other
    max_rpm=3,                        # stay inside Groq's free limits
    verbose=True,
)

if __name__ == "__main__":
    topic = input("What topic should we study? ")
    result = crew.kickoff(inputs={"topic": topic})
    print("\n✅ Done! Open study_plan.md to see your plan.\n")
    print(result)

