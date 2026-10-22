"""RAGAS evaluation for the college FAQ chatbot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from config.settings import EVAL_DIR, Settings, get_settings
from src.embeddings import build_embeddings
from src.factory import create_chatbot



# Ground-truth Q&A pairs derived from the shipped template knowledge base.
# Replace them with facts from your own document when you swap the .docx.
EVAL_QUESTIONS: list[dict[str, str | list[str]]] = [
    {
        "question": "When was the college established?",
        "ground_truth": "The college was established in 2001.",
        "reference_contexts": [
            "Sample College of Engineering is an autonomous engineering college established in 2001 under the Example Education Trust.",
        ],
    },
    {
        "question": "What NAAC grade does the college hold?",
        "ground_truth": "The college is NAAC accredited with Grade 'B+' (2021).",
        "reference_contexts": [
            "NAAC: Accredited with Grade 'B+' (2021).",
        ],
    },
    {
        "question": "Which university is the college affiliated to?",
        "ground_truth": "The college is affiliated to Example State University.",
        "reference_contexts": [
            "Affiliated to Example State University.",
        ],
    },
    {
        "question": "What is the vision of the college?",
        "ground_truth": "To be a centre of academic excellence in engineering education, producing graduates with strong technical depth, ethical grounding and research inclination.",
        "reference_contexts": [
            "To be a centre of academic excellence in engineering education, producing graduates with strong technical depth, ethical grounding and research inclination.",
        ],
    },
    {
        "question": "How many faculty members are in the CSE department?",
        "ground_truth": "The CSE department has 42 faculty members.",
        "reference_contexts": [
            "Computer Science & Engineering (CSE) | 42 | Dr. A. Sharma",
        ],
    },
    {
        "question": "What is the college contact email?",
        "ground_truth": "The college contact email is principal@example.edu.",
        "reference_contexts": [
            "Email: principal@example.edu",
        ],
    },
    {
        "question": "Does the college offer an MBA programme?",
        "ground_truth": "No MBA programme is mentioned in the knowledge base.",
        "reference_contexts": [],
    },
    {
        "question": "What is the highest placement package mentioned?",
        "ground_truth": "The highest mentioned package is 35.0 LPA from Globex Technologies.",
        "reference_contexts": [
            "35.0",
            "Globex Technologies",
        ],
    },
]


def _collect_responses(
    settings: Settings,
) -> tuple[list[str], list[list[str]], list[str]]:
    """Run every eval question through the *production* chatbot pipeline.

    Uses ``create_chatbot(settings)`` -- the exact same factory that the
    Streamlit UI calls -- so retrieval (hybrid BM25 + MMR), query
    normalisation, query rewriting, and answer generation are all
    identical to what a real user experiences.

    Returns
    -------
    questions : list[str]
    contexts  : list[list[str]]   -- page_content of every retrieved chunk
    answers   : list[str]
    """
    chatbot = create_chatbot(settings)

    questions: list[str] = []
    contexts: list[list[str]] = []
    answers: list[str] = []

    for item in EVAL_QUESTIONS:
        question = str(item["question"])
        questions.append(question)

        response = chatbot.ask(question)
        answers.append(response.answer)

        if response.retrieval and response.retrieval.documents:
            contexts.append(
                [doc.page_content for doc in response.retrieval.documents]
            )
        else:
            contexts.append([])

    return questions, contexts, answers


def run_ragas_evaluation(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()

    # Collect responses via the production pipeline (identical to the UI).
    questions, contexts, answers = _collect_responses(settings)

    eval_data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": [str(item["ground_truth"]) for item in EVAL_QUESTIONS],
    }
    dataset = Dataset.from_dict(eval_data)

    # Build the RAGAS judge LLM and embeddings using the same credentials.
    embeddings = build_embeddings(settings)
    ragas_llm = ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        default_headers=settings.openrouter_headers,
        temperature=0.0,
    )

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ragas_llm,
        embeddings=embeddings,
    )

    df = result.to_pandas()
    return df


def save_evaluation_results(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or EVAL_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"ragas_results_{timestamp}.csv"
    json_path = output_dir / f"ragas_results_{timestamp}.json"
    html_path = output_dir / f"ragas_dashboard_{timestamp}.html"

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    build_dashboard(df).write_html(str(html_path))

    summary = {
        "timestamp": timestamp,
        "metrics": {col: float(df[col].mean()) for col in df.columns if col not in {"question"}},
        "files": {
            "csv": str(csv_path),
            "json": str(json_path),
            "dashboard": str(html_path),
        },
    }
    (output_dir / f"ragas_summary_{timestamp}.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return csv_path


def build_dashboard(df: pd.DataFrame) -> go.Figure:
    metric_cols = [
        col
        for col in df.columns
        if col not in {"question", "contexts", "ground_truth", "answer"}
    ]

    if not metric_cols:
        fig = go.Figure()
        fig.update_layout(title="No RAGAS metrics available")
        return fig

    melted = df.melt(
        id_vars=["question"],
        value_vars=metric_cols,
        var_name="metric",
        value_name="score",
    )

    fig = px.bar(
        melted,
        x="question",
        y="score",
        color="metric",
        barmode="group",
        title="RAGAS Evaluation - Per Question Scores",
        labels={"score": "Score", "question": "Question"},
        range_y=[0, 1],
    )
    fig.update_layout(xaxis_tickangle=-35, height=600, template="plotly_white")
    return fig
