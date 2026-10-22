"""Synthetic resumes with skills, experience and a hiring label."""
import re

import numpy as np

SKILLS = [
    "python", "sql", "pandas", "flask", "docker", "git", "javascript",
    "react", "testing", "linux", "rest", "typescript",
]

JOB_DESCRIPTION = (
    "We need a junior backend developer with Python, SQL, REST APIs and testing. "
    "Flask, Docker and Git experience are a plus."
)

NAMES = [f"Candidate {index:02d}" for index in range(64)]


def make_resume(index, seed=0, skills=None):
    """A resume, as the text a person would send.

    The hiring label comes from what the resume shows about the work and the
    studies, not from the skills: the skills are what the model has to learn
    from the text, so the label may not be a function of them.
    """
    rng = np.random.default_rng(seed + index)
    if skills is None:
        chosen = list(rng.choice(SKILLS, size=int(rng.integers(3, 8)), replace=False))
    else:
        chosen = list(skills)
    years = int(rng.integers(0, 8))
    education = str(rng.choice(["diploma", "bachelor", "master"]))
    projects = int(rng.integers(0, 5))
    summary = (
        f"{NAMES[index]} has {years} years of experience and a {education} degree. "
        f"Recent work used {', '.join(chosen[:3])}. "
        f"Completed {projects} portfolio projects and collaborated in small teams."
    )

    # The panel scores the work, the studies and the experience, and not the
    # skills: the label is what the model has to predict from the text.
    panel = 0.9 * projects + 1.4 * years + (1.0 if education == "master" else 0.0)
    label = int(panel + rng.normal(0, 1.2) >= 5.5)
    if rng.random() < 0.08:
        label = 1 - label  # a little label noise
    return {
        "name": NAMES[index],
        "text": summary,
        "skills": chosen,
        "years": years,
        "education": education,
        "projects": projects,
        "label": label,
    }


def parse_resume(text):
    """Read a resume and pull the facts out of it.

    The parser works on the text of the resume, the way a real one would: the
    years of experience, the degree, the number of the projects and the
    skills that are mentioned.
    """
    lowered = text.lower()

    years = 0
    match = re.search(r"has (\d+) years of experience", lowered)
    if match:
        years = int(match.group(1))

    education = ""
    match = re.search(r"a (diploma|bachelor|master) degree", lowered)
    if match:
        education = match.group(1)

    projects = 0
    match = re.search(r"completed (\d+) portfolio projects", lowered)
    if match:
        projects = int(match.group(1))

    mentioned = [skill for skill in SKILLS if skill in lowered]

    return {
        "years": years,
        "education": education,
        "projects": projects,
        "skills": mentioned,
    }


def load_data(seed=42, quick=False):
    count = 16 if quick else 24
    resumes = [make_resume(index, seed) for index in range(count)]
    split = int(count * 0.7)
    return {
        "train": resumes[:split],
        "test": resumes[split:],
        "job_description": JOB_DESCRIPTION,
        "skills": SKILLS,
    }
