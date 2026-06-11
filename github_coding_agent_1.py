import os
import json
from datetime import date
from dotenv import load_dotenv
from langfuse.openai import openai
from langfuse import observe, get_client

load_dotenv()
llm = openai
langfuse = get_client()

TOOLS = [
    {
        "type": "mcp",
        "server_label": "github",
        "server_url": "https://api.githubcopilot.com/mcp/",
        "authorization": os.getenv("GITHUB_TOKEN"),
        "require_approval": "never",
        "headers": {
            "X-MCP-Toolsets": "context, repos, pull_requests, issues"
        }
    }
]

@observe()
def llm_response(history):
    response = llm.responses.create(
        model="gpt-4.1-mini",
        # model="gpt-5.2-codex", # OpenAI's best coding model!
        temperature=0,
        input=history,
        tools=TOOLS
    )
    return response

@observe()
def agent_loop(history):
    while True:
        response = llm_response(history)
        history += response.output

        tool_calls = [obj for obj in response.output if \
                      getattr(obj, "type", None) == "function_call"]
        text_messages = [obj for obj in response.output if \
                      getattr(obj, "type", None) == "message"]

        if not tool_calls:
            break

        if text_messages:
            print(f"\nAssistant: {response.output_text}")

        # for tool_call in tool_calls:
        #     function_name = tool_call.name
        #     args = json.loads(tool_call.arguments)

            # if function_name == "deploy_site":
            #     result = {"deploy_site": deploy_site(**args)}
            # elif function_name == "read_webpage":
            #     result = {"read_webpage": read_webpage(**args)}

            # history += [{"type": "function_call_output",
            #                 "call_id": tool_call.call_id,
            #                 "output": json.dumps(result)}]
    return response

def system_prompt():
    return f"""You are a senior software developer who works on codebases living in Github repos."""

assistant_message = "How can I help?"
user_input = input(f"\nAssistant: {assistant_message}\n\nUser: ")

history = [
    {"role": "developer", "content": system_prompt()},
    {"role": "assistant", "content": assistant_message},
    {"role": "user", "content": user_input}
]

with langfuse.start_as_current_observation(as_type="span", name="github-coding-agent") as span:
    while user_input != "exit":
        response = agent_loop(history)
                
        print(f"\nAssistant: {response.output_text}")

        user_input = input("\nUser: ")
        history += [{"role": "user", "content": user_input}]
    
    span.update(output="Conversation complete")

langfuse.flush()