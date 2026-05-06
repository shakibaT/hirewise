from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

def generate_questions(jd: str, resume: str, client=None) -> list[str]:
    if client is None:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": """You are an expert technical interviewer. 
Generate relevant interview questions based on job descriptions and candidate resumes.
Always respond with valid JSON only. No explanation, no markdown, no extra text."""
            },
            {
                "role": "user",
                "content": f"""Generate exactly 5 interview questions for this role.

                                Job Description:
                                {jd}

                                Candidate Resume:
                                {resume}

                                Requirements:
                                - Questions must be open-ended
                                - Assess experience, skills, and cultural fit
                                - Return ONLY a JSON object in this exact format:
                                {{
                                    "questions": [
                                        "question 1",
                                        "question 2",
                                        "question 3",
                                        "question 4",
                                        "question 5"
                                    ]
                                }}"""
            }
        ]
    )

    raw = response.choices[0].message.content.strip()
    
    # Clean markdown fences if LLM adds them anyway
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    parsed = json.loads(raw)
    questions = parsed["questions"]

    if not questions or len(questions) != 5:
        raise ValueError(f"Expected 5 questions, got {len(questions)}")

    return questions

if __name__ == "__main__":
    # Example usage
    jd = input("Please paste the job description: ")
    resume = input("Please paste the candidate resume: ")
    questions = generate_questions(jd, resume)
    print("\n--- Generated Interview Questions ---\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")