from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from core.models import FollowUp, ConversationEntry

load_dotenv()

def _get_client(client=None) -> OpenAI:
    if client is None:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return client

def _serialize_context(context: list[ConversationEntry]) -> str:
    return "\n".join([
        f"Q: {entry.question}\nA: {entry.answer}"
        for entry in context
    ])

def is_answer_vague(question: str, answer: str, context: list[ConversationEntry], client=None) -> bool:
    client = _get_client(client)
    context_text = _serialize_context(context)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": """You are an expert technical interviewer.
Classify whether a candidate's answer is vague or incomplete and would benefit from a followup question.
Always respond with valid JSON only. No explanation, no markdown, no extra text.
Return ONLY this format: {\"is_vague\": true or false}"""
            },
            {
                "role": "user",
                "content": f"""Question: {question}
Answer: {answer}
Recent context:
{context_text}"""
            }
        ]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    return parsed.get("is_vague", False)


def generate_followup(question: str, answer: str, context: list[ConversationEntry], client=None) -> str:
    client = _get_client(client)
    context_text = _serialize_context(context)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": """You are an expert technical interviewer.
Generate one concise followup question that digs deeper into the candidate's vague or incomplete answer.
Always respond with valid JSON only. No explanation, no markdown, no extra text.
Return ONLY this format: {\"followup_question\": \"your question here\"}"""
            },
            {
                "role": "user",
                "content": f"""Question: {question}
Answer: {answer}
Recent context:
{context_text}"""
            }
        ]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    return parsed.get("followup_question", "Can you elaborate further?")


if __name__ == "__main__":
    question = "Can you describe your experience with Python?"
    answer = "I have used Python for various projects."
    context = [
        ConversationEntry(
            question="What programming languages are you proficient in?",
            answer="I am proficient in Python, JavaScript, and Java."
        )
    ]
    vague = is_answer_vague(question, answer, context)
    print(f"Is the answer vague? {vague}")
    if vague:
        followup = generate_followup(question, answer, context)
        print(f"Generated followup question: {followup}")
