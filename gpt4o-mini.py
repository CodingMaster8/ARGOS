from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

with open("context.txt", 'r') as file:
  context = file.read()


## Set the API key and model name
MODEL="gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

completion = client.chat.completions.create(
  model=MODEL,
  messages=[
    {"role": "system", "content": "You are a assistant"}, # <-- This is the system message that provides context to the model
    {"role": "user", "content": f"What day is today?"}  # <-- This is the user message for which the model will generate a response
  ]
)

print("Assistant: " + completion.choices[0].message.content)
print(completion)
print(completion.choices)
print(completion.usage.total_tokens)