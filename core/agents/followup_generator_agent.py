from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from core.models import FollowUp, ConversationEntry, AnswerEvaluation

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


def evaluate_answer(question: str, answer: str, context: list[ConversationEntry], client=None) -> AnswerEvaluation:
    client = _get_client(client)
    context_text = _serialize_context(context)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": """You are an expert technical interviewer.
Classify a candidate's answer into one of three categories:
1) "needs_followup" - the answer is vague, incomplete, or off-topic and would benefit from a followup question
2) "acceptable" - the answer is good enough to move on to the next question
3) "candidate_doesnt_know" - the answer indicates the candidate does not know the topic at all
Always respond with valid JSON only. No explanation, no markdown, no extra text.
Return ONLY this format: {\"evaluation\": \"needs_followup\" or \"acceptable\" or \"candidate_doesnt_know\"}"""
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
    evaluation_str = parsed.get("evaluation", "acceptable")
    return AnswerEvaluation(evaluation_str)



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


# Fix the test block to use new function
if __name__ == "__main__":
    question = "Can you describe your experience with Python?"
    answer = "I have used Python for various projects."
    context = [
        ConversationEntry(
            question="What programming languages are you proficient in?",
            answer="I am proficient in Python, JavaScript, and Java."
        )
    ]
    
    evaluation = evaluate_answer(question, answer, context)
    print(f"Evaluation: {evaluation.value}")
    
    if evaluation == AnswerEvaluation.NEEDS_FOLLOWUP:
        followup = generate_followup(question, answer, context)
        print(f"Followup question: {followup}")
    elif evaluation == AnswerEvaluation.CANDIDATE_DOESNT_KNOW:
        print("Candidate doesn't know — moving to next question")
    else:
        print("Answer acceptable — moving to next question")
