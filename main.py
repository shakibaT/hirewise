import typer
from core.models import InterviewSession, InterviewStage
from core.agents.interviewer_agent import execute
import json
from pathlib import Path

app = typer.Typer()

def load_text(path_or_text: str) -> str:
    if Path(path_or_text).exists():
        return Path(path_or_text).read_text()
    return path_or_text  # treat as raw text if not a file


@app.command()
def interview(
    jd: str = typer.Option(..., help="Job description - file path or text"),
    resume: str = typer.Option(..., help="Candidate resume - file path or text"),
    name: str = typer.Option(..., help="Candidate name"),
    output: str = typer.Option(None, help="Output path for report JSON")
):
    # Step 1 - Load JD and resume
    jd_text = load_text(jd)
    resume_text = load_text(resume)

    # Step 2 - Create session
    session = InterviewSession(
        jd=jd_text,
        resume=resume_text,
        candidate_name=name
    )

    # Step 3 - Welcome message
    typer.echo(f"\n{'='*50}")
    typer.echo("Welcome to HireWise Interview System")
    typer.echo(f"Candidate: {name}")
    typer.echo(f"{'='*50}\n")

    # Step 4 - First execute call, no user answer yet
    result = execute(session)
    typer.echo(f"\nInterviewer: {result['response']}")

    # Step 5 - Interview loop
    while session.stage != InterviewStage.COMPLETED:

        if session.stage == InterviewStage.GENERATING_REPORT:
            typer.echo("\nGenerating your report, please wait...")
            result = execute(session)

        else:
            user_answer = typer.prompt("\nYour answer")
            result = execute(session, user_answer)
            typer.echo(f"\nInterviewer: {result['response']}")

    # Step 6 - Handle report
    report = result['response']
    report_json = json.dumps(report, indent=2, ensure_ascii=False)

    if output:
        Path(output).write_text(report_json)
        typer.echo(f"\nReport saved to {output}")
    else:
        typer.echo("\n--- Interview Report ---\n")
        typer.echo(report_json)


if __name__ == "__main__":
    app()
