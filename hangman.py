from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI()

assistant_message = "Let's play Hangman! I'm thinking of a word. Guess a letter!"
user_input = input(f"\nAssistant: {assistant_message}\n\nUser: ")

history = [
    {"role": "developer", "content": "You are the game show host for the classic word game Hangman."},
    {"role": "assistant", "content": assistant_message},
    {"role": "user", "content": user_input}
]

while user_input != "exit":
    response = llm.responses.create(
        model="gpt-4.1-mini",
        temperature=0,
        max_output_tokens=1000,
        input=history,
    )

    llm_response_text = f"\nAssistant: {response.output_text}"
    print(llm_response_text)

    user_input = input("\nUser: ")
    history += [
        {"role": "assistant", "content": response.output_text},
        {"role": "user", "content": user_input}
    ]
