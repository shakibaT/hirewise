from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class InterviewStage(Enum):
    NOT_STARTED = 'not_started'
    GENERATING_QUESTIONS = 'generating_questions'
    ASKING_QUESTIONS = 'asking_questions'
    FOLLOWUP = 'followup'
    GENERATING_REPORT = 'generating_report'
    COMPLETED = 'completed'

@dataclass
class FollowUp:
    question: str
    answer: str


@dataclass
class ConversationEntry:
    question: str
    answer: str
    followups: list[FollowUp] = field(default_factory=list)


@dataclass
class InterviewSession:
    jd: str
    resume: str
    candidate_name: str # who is being interviewed
    stage: InterviewStage = InterviewStage.NOT_STARTED # enum
    questions: list[str] = field(default_factory=list)
    conversation_history: list[ConversationEntry] = field(default_factory=list) # {question, answer, followups}
    report: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())) # unique id per interview, needed when you add DB
    current_question_index: int = 0 # where are we in the questions list
    followup_count: int = 0 # circuit breaker - max followups per question
    created_at: str = field(default_factory=lambda: datetime.now().isoformat()) # timestamp, useful for reports
