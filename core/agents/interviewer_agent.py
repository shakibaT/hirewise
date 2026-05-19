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

from core.models import FollowUp, InterviewSession, InterviewStage, ConversationEntry, AnswerEvaluation
from core.agents.question_generator_agent import generate_questions
from core.agents.followup_generator_agent import evaluate_answer, generate_followup
from core.agents.report_generator_agent import generate_report
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

    # Step 3 - Evaluate answer
    evaluation = evaluate_answer(current_question, user_answer, recent_context)
    logger.info(f"Answer evaluation: {evaluation.value} for question {session.current_question_index}")

    # Step 4 - Route based on evaluation
    if evaluation == AnswerEvaluation.NEEDS_FOLLOWUP:
        session.stage = InterviewStage.FOLLOWUP
        session.followup_count += 1
        session.conversation_history[-1].evaluation = evaluation.value
        return {
            "response": generate_followup(current_question, user_answer, recent_context),
            "stage": session.stage
        }

    elif evaluation == AnswerEvaluation.CANDIDATE_DOESNT_KNOW:
        session.conversation_history[-1].evaluation = evaluation.value
        return _go_to_next_question(session)

    else:  # ACCEPTABLE
        session.conversation_history[-1].evaluation = evaluation.value
        return _go_to_next_question(session)


def handle_followup(session: InterviewSession, user_answer: str) -> dict:
    # handle_followup → owns: saving followup answer, deciding if ANOTHER followup needed, circuit breaker

    # Step 1 - Save followup answer to last ConversationEntry
    current_question = session.questions[session.current_question_index]
    last_entry = session.conversation_history[-1]
    last_followup_question = last_entry.followups[-1].question if last_entry.followups else current_question
    last_entry.followups.append(FollowUp(
        question=last_followup_question,
        answer=user_answer
    ))
    logger.info(f"Recorded followup answer for question {session.current_question_index} in session {session.session_id}")

    # Step 2 - Build context from last 5 conversation entries
    recent_context = session.conversation_history[-5:]

    # Step 3 - Evaluate followup answer
    evaluation = evaluate_answer(current_question, user_answer, recent_context)

    # Step 4 - Circuit breaker first
    if session.followup_count >= MAX_FOLLOWUPS:
        logger.info(f"Max followups reached for question {session.current_question_index}")
        return _go_to_next_question(session)

    # Step 5 - Still needs followup?
    if evaluation == AnswerEvaluation.NEEDS_FOLLOWUP:
        session.followup_count += 1
        return {
            "response": generate_followup(current_question, user_answer, recent_context),
            "stage": session.stage
        }

    # Step 6 - Acceptable or doesn't know
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
