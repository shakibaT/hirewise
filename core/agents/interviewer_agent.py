# Conducts AI-powered interviews based on JD and resume.

# Inputs:
# - job description (str)
# - candidate resume (str)
# - candidate answer (str | None)
# - conversation history (list[ConversationEntry])

# Outputs:
# - next question or followup (str)
# - updated interview stage (InterviewStage)

# State machine:
# NOT_STARTED → GENERATING_QUESTIONS → ASKING_QUESTIONS ⇄ FOLLOWUP
# → GENERATING_REPORT → COMPLETED

from core.models import InterviewSession, InterviewStage, ConversationEntry
from question_generator_agent import generate_questions
import logging

logger = logging.getLogger(__name__)


MAX_FOLLOWUPS = 2

def execute(session: InterviewSession, user_answer: str = None) -> dict:
    """
    Main entry point. Routes to correct handler based on session stage.
    Returns: {"response": str, "stage": InterviewStage}
    """
    if session.stage == InterviewStage.NOT_STARTED:
        return handle_not_started(session)
    
    elif session.stage == InterviewStage.ASKING_QUESTIONS:
        return handle_asking_questions(session, user_answer)
    
    elif session.stage == InterviewStage.FOLLOWUP:
        return handle_followup(session, user_answer)
    
    elif session.stage == InterviewStage.GENERATING_REPORT:
        return handle_generating_report(session)


def handle_not_started(session: InterviewSession) -> dict:
    logger.info(f"Generating questions for session {session.session_id}")
    session.stage = InterviewStage.GENERATING_QUESTIONS
    questions = generate_questions(session.jd, session.resume)

    if not questions:
        raise ValueError("Question generator returned no questions")
    
    session.questions = questions
    logger.info(f"Generated {len(questions)} questions for session {session.session_id}")
    session.stage = InterviewStage.ASKING_QUESTIONS
    
    return {
        "response": session.questions[0],
        "stage": session.stage
    }


def handle_asking_questions(session: InterviewSession, user_answer: str) -> dict:
    # Step 1 - Save Q&A to conversation history
    current_question = session.questions[session.current_question_index]
    session.conversation_history.append(ConversationEntry(
        question=current_question,
        answer=user_answer
    ))
    logger.info(f"Recorded answer for question {session.current_question_index} in session {session.session_id}")

    # Step 2 - Build context from last 5 conversation entries
    recent_context = session.conversation_history[-5:]

    # Step 3 - Decide if answer is vague
    # TODO: add this LLM-based function  
    is_vague = if_answer_is_vague(current_question, user_answer, recent_context)

    # Step 4 - If vague and under MAX_FOLLOWUPS limit
    if is_vague and session.followup_count < MAX_FOLLOWUPS:
        logger.info(f"Answer deemed vague for question '{current_question}' in session {session.session_id}")
        session.stage = InterviewStage.FOLLOWUP
        session.followup_count += 1
        return {
            "response": "Can you please elaborate on your previous answer?",  # TODO: replace with LLM-generated followup
            "stage": session.stage
        }

    # Step 5 - Answer is complete, move to next question
    session.current_question_index += 1
    session.followup_count = 0

    # Step 6 - Check if interview is finished
    if session.current_question_index >= len(session.questions):
        session.stage = InterviewStage.GENERATING_REPORT
        return {
            "response": "Thank you for your answers. Generating report...",
            "stage": session.stage
        }

    # Step 7 - Return next question
    session.stage = InterviewStage.ASKING_QUESTIONS
    return {
        "response": session.questions[session.current_question_index],
        "stage": session.stage
    }


def handle_followup(session: InterviewSession, user_answer: str) -> dict:
    pass

def handle_generating_report(session: InterviewSession) -> dict:
    pass