from openai import OpenAI
from dotenv import load_dotenv
from core.models import ConversationEntry
import os
import json
from datetime import datetime

load_dotenv()

def _get_client(client=None) -> OpenAI:
    if client is None:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return client

def _serialize_conversation(conversation: list[ConversationEntry]) -> str:
    result = []
    for i, entry in enumerate(conversation, 1):
        result.append(f"Q{i}: {entry.question}")
        result.append(f"A{i}: {entry.answer}")
        for j, followup in enumerate(entry.followups, 1):
            result.append(f"  Followup {j}: {followup.question}")
            result.append(f"  Followup Answer {j}: {followup.answer}")
    return "\n".join(result)

def generate_report(jd: str, resume: str, conversation: list[ConversationEntry], client=None) -> dict:
    client = _get_client(client)
    conversation_text = _serialize_conversation(conversation)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": """You are an expert technical interviewer.
                                Generate a comprehensive interview report based on the job description, candidate resume, and conversation history.
                                Always respond with valid JSON only. No explanation, no markdown, no extra text.
                                Return ONLY this exact JSON format:
                                {
                                    "candidate_name": "string",
                                    "role": "string",
                                    "date": "string",
                                    "overall_score": 0.0,
                                    "overall_justification": "string",
                                    "recommendation": "Strong Yes or Yes or Maybe or No",
                                    "skill_assessment": {
                                        "skill_name": 0.0
                                    },
                                    "strengths": ["string"],
                                    "weaknesses": ["string"],
                                    "question_evaluations": [
                                        {
                                            "question": "string",
                                            "answer_summary": "string",
                                            "score": 0.0,
                                            "needed_followup": true,
                                            "followup_count": 0
                                        }
                                    ]
                                }"""
                                            },
                                            {
                                                "role": "user",
                                                "content": f"""Generate the interview report.

                                Job Description:
                                {jd}

                                Candidate Resume:
                                {resume}

                                Conversation history:
                                {conversation_text}"""
                                            }
                                        ]
                                    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    report = json.loads(raw)

    for i, evaluation in enumerate(report["question_evaluations"]):
        if i < len(conversation):
            actual_followup_count = len(conversation[i].followups)
            evaluation["followup_count"] = actual_followup_count
            evaluation["needed_followup"] = actual_followup_count > 0

    # Add interview date if LLM didn't include it
    if not report.get("date"):
        report["date"] = datetime.now().strftime("%Y-%m-%d")

    return report


if __name__ == "__main__":
    from core.models import ConversationEntry, FollowUp

    jd = "We need a Python developer with experience in AI and machine learning."
    resume = "John Doe - 5 years Python experience, worked on NLP models at TechCorp."

    conversation = [
        ConversationEntry(
            question="Tell me about your Python experience.",
            answer="I have used Python for 5 years mostly for data science.",
            followups=[
                FollowUp(
                    question="Can you give a specific example?",
                    answer="I built an NLP pipeline at TechCorp using spaCy."
                )
            ]
        ),
        ConversationEntry(
            question="What ML frameworks have you used?",
            answer="I have used TensorFlow and PyTorch extensively."
        )
    ]

    report = generate_report(jd, resume, conversation)
    print(json.dumps(report, indent=2))
