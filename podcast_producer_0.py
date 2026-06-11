import os
import json
from datetime import date
from dotenv import load_dotenv
from langfuse.openai import openai
from langfuse import observe, get_client
from podcast_tools import generate_image, write_to_file, create_audio, TOOLS

load_dotenv()
llm = openai
langfuse = get_client()

@observe()
def llm_response(history):
    response = llm.responses.create(
        model="gpt-4.1-mini",
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

        for tool_call in tool_calls:
            function_name = tool_call.name
            args = json.loads(tool_call.arguments)

            if function_name == "generate_image":
                result = {"generate_image": generate_image(**args)}
            elif function_name == "write_to_file":
                result = {"write_to_file": write_to_file(**args)}
            elif function_name == "create_audio":
                result = {"create_audio": create_audio(**args)}

            history += [{"type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(result)}]
    return response

def system_prompt():
    return f"""<overview>
    You are a podcast producer. A user will describe the nature of the podcast they want you to create,
    and you will create a podcast, including the transcript, an mp3 audio file, and a cover image.
    </overview>

    <instructions>
    Here are the steps you'll follow to create the podcast. Follow each step in this sequence:

    1. Ask a couple of clarifying questions to the user, one at a time, to be sure you understand what the user
    wants. Be sure to learn the desired length of the podcast.
    2. If the user wants a podcast that requires web research (such as if they want a podcast that reports current
    events), you are equipped with the ability to perfom web research.
    3. Next, generate the text of the podcast transcript.
    4. Next, use your write_to_file tool to create a transcript text file.
    5. Next, use your create_audio tool to create the podcast audio mp3 file.
    6. Next, use your generate_image tool to create an appropriate cover image for the podcast.
    
    Additional instructions: 
    * Inform the user what you are doing before each step.
    * Whenever you create a file, tell the user the filename.
    </instructions>
    
    <useful_information>
    Today's date is {date.today().strftime("%B %d, %Y")}.
    </useful_information>

    Go!"""

assistant_message = "Let me help you create your next podcast! Describe what you're looking for."
user_input = input(f"\nAssistant: {assistant_message}\n\nUser: ")

history = [
    {"role": "developer", "content": system_prompt()},
    {"role": "assistant", "content": assistant_message},
    {"role": "user", "content": user_input}
]

with langfuse.start_as_current_observation(as_type="span", name="podcast-conversation") as span:
    while user_input != "exit":
        response = agent_loop(history)
                
        print(f"\nAssistant: {response.output_text}")

        user_input = input("\nUser: ")
        history += [
            {"role": "assistant", "content": response.output_text},
            {"role": "user", "content": user_input}
        ]
    
    span.update(output="Conversation complete")

langfuse.flush()

print("****HISTORY****")
print(history)