import json
import sys
import asyncio
import re
import time
from flask import Flask, jsonify, Response
from flask_cors import CORS
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv

# Fix asyncio event loop issue on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)


def extract_info(text):
    """Extract relevant details from the agent's execution history."""
    evaluation_pattern = r"evaluation_previous_goal='(.*?)'"
    memory_pattern = r"memory='(.*?)'"
    next_goal_pattern = r"next_goal='(.*?)'"
    result_pattern = r"extracted_content=\"(.*?)\""

    evaluation_matches = re.findall(evaluation_pattern, text)
    memory_matches = re.findall(memory_pattern, text)
    next_goal_matches = re.findall(next_goal_pattern, text)
    result_matches = re.findall(result_pattern, text, re.DOTALL)

    max_length = max(len(evaluation_matches), len(memory_matches), len(next_goal_matches), len(result_matches))

    extracted_results = []
    for i in range(max_length):
        evaluation = evaluation_matches[i] if i < len(evaluation_matches) else "N/A"
        memory = memory_matches[i] if i < len(memory_matches) else "N/A"
        next_goal = next_goal_matches[i] if i < len(next_goal_matches) else "N/A"
        extracted_content = result_matches[0] if result_matches else "N/A"  # Extracted content appears once

        # Ensure consistent step formatting
        memory = re.sub(r"(\d)/(\d+ steps?)", r"\1 / \2", memory)

        extracted_results.append({
            "step_number": i + 1,
            "evaluation_previous_goal": evaluation,
            "memory": memory,
            "next_goal": next_goal,
            "result": extracted_content if i == max_length - 1 else "N/A"
        })

    return extracted_results


@app.route("/run-test/<test_id>", methods=["GET"])
def run_test_case(test_id):
    """Run a test case based on the provided test_id."""
    def generate():
        with open("test_cases.json", "r") as f:
            test_cases = json.load(f)

        test_steps = test_cases.get(test_id, {}).get("steps", [])

        if not test_steps:
            yield f"data: {json.dumps({'error': f'Test case {test_id} not found'})}\n\n"
            return

        task_string = "\n".join(test_steps)
        yield f"data: {json.dumps({'step': f'Starting test case {test_id}'})}\n\n"

        async def execute_agent():
            agent = Agent(task=task_string, llm=llm)
            return await agent.run()

        # Run the agent and get execution history
        history = asyncio.run(execute_agent())

        # Convert history to text for regex processing
        result_text = "\n".join([str(message) for message in history])
        filtered_results = extract_info(result_text)

        # Stream each step result
        for step in filtered_results:
            yield f"data: {json.dumps({'step': step})}\n\n"
            time.sleep(1)

        yield f"data: {json.dumps({'result': '✅ Test execution completed'})}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
    })


if __name__ == "__main__":
    app.run(debug=True)
