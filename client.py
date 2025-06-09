#pip install openai
from openai import OpenAI
client = OpenAI(
    api_key = "Your open ai api key Paste It here"
)


completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "system", "content":"You are a virtual assistant named jarvis, skilled in general tasks like Alexa and Google Cloud"},
    {"role": "user", "content": "write a poem about ai"}
  ]
)

print(completion.choices[0].message.content)











