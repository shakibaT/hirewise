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

from core.models import FollowUp, InterviewSession, InterviewStage, ConversationEntry
from question_generator_agent import generate_questions
from followup_generator_agent import is_answer_vague
from report_generator_agent import generate_report
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
    # handle_asking_questions  → owns: saving answer, deciding if vague, moving to next question

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
    is_vague = is_answer_vague(current_question, user_answer, recent_context)

    # Step 4 - If vague and under MAX_FOLLOWUPS limit
    if is_vague:
        logger.info(f"Answer is vague for question '{current_question}' in session {session.session_id}")
        session.stage = InterviewStage.FOLLOWUP
        session.followup_count += 1
        return {
            "response": "Can you please elaborate on your previous answer?",  # TODO: replace with LLM-generated followup
            "stage": session.stage
        }

    # Step 5 - Answer is complete, move to next question
    return _go_to_next_question(session)



def handle_followup(session: InterviewSession, user_answer: str) -> dict:
    # handle_followup  → owns: saving followup answer, deciding if ANOTHER followup needed, circuit breaker
    # Step 1 - Save followup answer to conversation history
    current_question = session.questions[session.current_question_index]
    last_entry = session.conversation_history[-1]
    last_entry.followups.append(FollowUp(
        question=f"Followup to: {current_question}",
        answer=user_answer
    ))
    logger.info(f"Recorded followup answer for question {session.current_question_index} in session {session.session_id}")
    # Step 2 - Build context from last 5 conversation entries
    recent_context = session.conversation_history[-5:]
    # Step 3 - Decide if answer is still vague
    is_still_vague = is_answer_vague(current_question, user_answer, recent_context)
    # Step 4 - If still vague and under MAX_FOLLOWUPS limit, ask another followup
    if is_still_vague and session.followup_count < MAX_FOLLOWUPS:
        logger.info(f"Answer still deemed vague for question '{current_question}' in session {session.session_id}")
        session.followup_count += 1
        return {
            "response": "I still need more details. Can you please elaborate further?",  # TODO: replace with LLM-generated followup
            "stage": session.stage
        }
    # Step 5 - Move back to ASKING_QUESTIONS stage to either next question or end interview
    return _go_to_next_question(session)


def _go_to_next_question(session: InterviewSession) -> dict:
    """Helper - moves to next question or ends interview if finished"""
    session.current_question_index += 1
    session.followup_count = 0
    session.stage = InterviewStage.ASKING_QUESTIONS

    if session.current_question_index >= len(session.questions):
        session.stage = InterviewStage.GENERATING_REPORT
        return {
            "response": "Thank you for your answers. Generating report...",
            "stage": session.stage
        }

    return {
        "response": session.questions[session.current_question_index],
        "stage": session.stage
    }


def handle_generating_report(session: InterviewSession) -> dict:
    # handle_generating_report → owns: generating report based on conversation history, JD, resume
    logger.info(f"Generating report for session {session.session_id}")
    report = generate_report(session.jd, session.resume, session.conversation_history)
    session.report = report
    session.stage = InterviewStage.COMPLETED
    logger.info(f"Completed report generation for session {session.session_id}")
    return {
        "response": report,
        "stage": session.stage
    }