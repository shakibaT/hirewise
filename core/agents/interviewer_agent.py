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
    pass

def handle_asking_questions(session: InterviewSession, user_answer: str) -> dict:
    pass

def handle_followup(session: InterviewSession, user_answer: str) -> dict:
    pass

def handle_generating_report(session: InterviewSession) -> dict:
    pass