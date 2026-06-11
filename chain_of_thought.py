from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI()

response = llm.responses.create(
    model="gpt-4.1-nano",
    input="What is 562 * 982? Solve this step by step."
)

print(response.output_text)