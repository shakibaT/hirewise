# hirewise

Autonomous AI interviewer that reads resumes, conducts adaptive interviews, and ranks candidates.

MVP goal: Paste resume text → paste job description text → interview starts → report generated.

## Purpose
Provide a simple MVP that lets HR/recruiters and candidates run AI-driven interviews, produce a final report, and rank candidates relative to a job description.

## Primary users
- Interviewees (candidates) — main interactive users who take the interviews.
- HR managers / Recruiters — admins who upload job descriptions, upload or paste resumes, view results, and run ranking.

## Version 1 (V1) scope — what will be delivered
Minimum end-to-end flow implemented and testable:
1. HR/recruiter pastes a job description.
2. HR/recruiter pastes a single resume (or a small set of resumes for ranking).
3. System stores resume(s) and job description.
4. System runs a match/score baseline and flags candidates meeting minimal skill criteria.
5. System generates an interview link for candidates that pass the baseline.
6. Candidate follows the link and completes an adaptive interview:
   - Interviewer (AI) asks context-aware questions based on resume + job description.
   - Interviewer asks follow-up questions based on candidate answers.
7. After interview completion, system generates a concise report:
   - Summary of candidate fit vs job description.
   - Key strengths, gaps, notable answers.
   - Final score / rank (if multiple resumes were provided).
8. HR can view and download the report from an admin panel.

Core acceptance criteria (“done” for V1)
- Given pasted resume text and job description text, the interview can be started and completed.
- The AI asks follow-up questions conditioned on resume content and prior answers.
- A human-readable report is created automatically after the interview ends.
- Basic ranking function produces an ordered list when given multiple resumes.
- Admin UI pages exist to paste/upload JD and resumes, start interview sessions, and view reports.

## Functional requirements (V1)
- Inputs:
  - Plain-text resume paste/upload.
  - Plain-text job description paste/upload.
- Storage:
  - Persist resumes, job descriptions, interview sessions, and reports.
- Matching & ranking:
  - Simple skill extraction from JD and resume.
  - Compute a compatibility score and rank candidates.
- Interview engine:
  - Question templates + resume-driven prompts.
  - Follow-up logic that adapts to candidate answers.
  - Session state persisted so interviews can be resumed.
- Report generation:
  - Structured summary, strengths/gaps, notable answers, and numeric score.
- Admin UI:
  - JD/resume input, list of candidates, start interview, view/download report.
- Minimal security & privacy:
  - Local storage acceptable for MVP; document privacy assumptions.

## Non-functional constraints (V1)
- Fast interaction for a single interview (target < 5s response for AI turn).
- Simple deployment (local or single small cloud instance).
- Clear manual instructions for HR to operate the system.

## Out of scope for V1
- Multi-language support.
- Real-time voice interview.
- Complex bias mitigation pipelines or legal compliance audits.
- Large-scale distributed ranking / heavy analytics dashboards.
- Automated scheduling and calendar integration.

## Data model (minimal)
- JobDescription { id, text, extracted_skills }
- Resume { id, text, extracted_skills, candidate_name? }
- InterviewSession { id, resume_id, jd_id, state, transcript, Q/A }
- Report { id, session_id, summary, score, created_at }

## Next steps / roadmap after V1
- Improve ranking model and calibration with labeled data.
- Add candidate invitations / scheduling and authentication.
- Add CSV/batch resume upload and bulk ranking.
- Add export formats (PDF) and richer admin analytics.

## Success metrics for MVP
- End-to-end demo: paste resume + JD → start interview → complete → report generated.
- HR user can rank at least 3 resumes and get consistent ordering.
- Candidate completes interview with coherent follow-up questions > 80% of the time.
