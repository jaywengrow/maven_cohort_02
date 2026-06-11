import json
import os
from dotenv import load_dotenv
from langfuse.openai import openai
from langfuse import observe, get_client
import sqlite3
import yagmail
import re
import uuid

load_dotenv()
llm = openai
langfuse = get_client()

# The database ID of the current user:
logged_in_user = 10
# Store sensitive PII in this dictionary:
pii = {}


def extract_and_strip_pii(user_input): # strip phone number data
    phone_regex = r"(\+?\d[\d\-\s]{7,}\d)"
    phone_matches = re.findall(phone_regex, user_input)
    for match in phone_matches:
        uid = str(uuid.uuid4())
        phone_number = match.strip()
        pii[f"PII:{uid}"] = phone_number
        user_input = re.sub(match, f"PII:{uid}", user_input)

    return user_input

@observe()
def llm_response(prompt):
    response = llm.responses.create(
        model="gpt-4.1-mini",
        temperature=0,
        tools=TOOLS,
        input=prompt
    )
    return response

@observe()
def display_user_info():
    conn = sqlite3.connect("gross.db")
    cursor = conn.cursor()
    query = f"""SELECT first_name, last_name, email, phone_number 
            FROM Users WHERE user_id = {logged_in_user};"""
    data = cursor.execute(query).fetchall()
    conn.close()
    print(f"""Your profile info:\n
        Name: {data[0][0]} {data[0][1]}\n
        Email: {data[0][2]}\n
        Phone: {data[0][3]}""")
    return "User info has been displayed!"

@observe()
def retrieve_orders():
    conn = sqlite3.connect("gross.db")
    cursor = conn.cursor()
    query = f"""SELECT u.user_id, o.order_id, o.order_date, 
    o.total_amount, o.status, o.payment_method,
    p.product_id, p.product_name, p.description, p.price
    FROM Users u
    JOIN Orders o ON u.user_id = o.user_id
    JOIN Products p ON o.product_id = p.product_id
    WHERE u.user_id = {logged_in_user}
    ORDER BY o.order_date DESC;"""
    data = cursor.execute(query).fetchall()
    conn.close()
    return data

@observe()
def update_phone_number(pii_code):
    new_phone_number = pii.get(pii_code)
    conn = sqlite3.connect("gross.db")
    cursor = conn.cursor()
    query = f"""UPDATE Users SET phone_number = '{new_phone_number}'\n
            WHERE user_id = {logged_in_user};"""
    cursor.execute(query)
    conn.commit()
    data = {"rows_affected": cursor.rowcount}
    
    return data

@observe()
def request_refund(summary):
    yag = yagmail.SMTP(os.getenv("GMAIL_ACCOUNT"), oauth2_file="oauth.json")
    yag.send(to='jay@commonsensedev.com', 
            subject=f"Refund request: User ID #{logged_in_user}",
            contents=summary)
    
TOOLS = [
    {
        "type": "function",
        "name": "display_user_info",
        "description": """Displays user profile info, including customer name,
        email address, and phone number.""",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "retrieve_orders",
        "description": """Looks up orders in the database. For each order, 
        returns user id, order id, order date, total payment, order status, 
        payment method, product id, product name, product description, product
        price""",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "update_phone_number",
        "description": "Updates the user's phone number in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "pii_code": {
                    "type": "string",
                    "description": """The code to reference the user's 
                    updated phone number""",
                },
            },
            "required": ["pii_code"],
        },
    },
    {
        "type": "function",
        "name": "request_refund",
        "description": """Sends an email containing details of a request refund
        to a human customer support agent.""",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": """A summary of the user's conversation
                    asking for a refund.""",
                },
            },
            "required": ["summary"],
        },
    },
]

@observe()
def agent_loop(history):
    while True:
        response = llm_response(history)
        history += response.output

        tool_calls = [obj for obj in response.output if getattr(obj, "type", None) == "function_call"]
        text_messages = [obj for obj in response.output if getattr(obj, "type", None) == "message"]

        if not tool_calls:
            break

        if text_messages:
            print(f"\nAssistant: {response.output_text}")

        for tool_call in tool_calls:
            function_name = tool_call.name
            args = json.loads(tool_call.arguments)

            if function_name == "display_user_info":
                result = {"display_user_info": display_user_info(**args)}
            elif function_name == "retrieve_orders":
                result = {"retrieve_orders": retrieve_orders(**args)}
            elif function_name == "update_phone_number":
                result = {"update_phone_number": update_phone_number(**args)}
            elif function_name == "request_refund":
                result = {"request_refund": request_refund(**args)}


            history += [{"type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(result)}]
    return response


print(f"Assistant: How can I help you today?\n")
user_input = extract_and_strip_pii(input("User: "))
history = [
    {"role": "developer", "content": f"""You are a customer support specialist
    for GROSS, a software product company. Through specific tools, you can
    access certain parts of the company's database.

    You may only manage data relating to the currently
    logged-in user, whose database ID is: {logged_in_user}. 
    Providing or updating info relating to any other 
    customer would be a MAJOR PRIVACY BREACH!

    You have access to several specialized tools. Here are your tools:
    <tools>
    * Your display_user_info tool allows you to display info of the user 
    currently logged in, including the user name, email, and phone number.
    You as the LLM will not see the info, but it will be displayed to the user.
    * Your retrieve_orders tool allows you to look up orders for the user 
    currently logged in.
    * Your update_phone_number tool allows you to update the phone number of the
    user currently logged in. As an LLM, you will not see the number yourself;
    it will appear as a code, such as PII:f47ca10b-58cc-4372-a567-0e02b2c3d479.
    Send this code (including the "PII:") as the parameter to the 
    update_phone_number tool.
    * Use the request_refund tool when a user requests a refund. You do not have the authority to issue a refund yourself as an AI bot, but this tool will send an email to an authorized human.
    Include, as a parameter, a summary of your conversation with the user, specifically highlighting why they want a refund. Before using this tool, please make sure you understand from the user all the details of their request, including which software product they want refunded, and why they want the refund.
    </tools>
    """},
    {"role": "assistant", "content": "How can I help you today?"},
    {"role": "user", "content": user_input}
]

with langfuse.start_as_current_observation(as_type="span", name="account-manager") as span:
    while user_input != "exit":
        response = agent_loop(history)

        print(f"\nAssistant: {response.output_text}")

        user_input = extract_and_strip_pii(input("\nUser: "))
        history += [{"role": "user", "content": user_input}]

    span.update(output="Conversation complete")

langfuse.flush()
print("***PII***")
print(pii)