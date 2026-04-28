# script that gets a JD and returns 5 related questions
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Get job description from user
jd = input("Please paste the job description: ")

completion = client.chat.completions.create(
  model="openai/gpt-oss-120b:free",
  messages=[
    {
      "role": "system",
      "content": "You are an expert technical interviewer. Your job is to generate relevant interview questions based on job descriptions."
    },
    {
      "role": "user",
      "content": f"Based on the following job description, generate exactly 5 interview questions that assess the candidate's fit for this role.\n\nJob Description:\n{jd}"
    }
  ]
)

print("\n--- Interview Questions ---\n")
print(completion.choices[0].message.content)
