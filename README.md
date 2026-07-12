# AELM — Advanced Employment & Labor Model

## Overview

AELM is a modular, local-first Python CLI that analyzes resumes and job
descriptions, estimates ATS compatibility, generates truthful resume
rewrites, evaluates job risks, detects common scam indicators, prepares
interview questions, and produces a strategic dashboard.

Everything runs locally. No account, API key, or network access is
required. An optional LLM chat feature can be enabled with an
environment variable (see below).

## Features

- Resume parsing (.txt, .md, .pdf, .docx)
- Job description parsing
- Semantic resume/job matching
- ATS scoring
- Truthful resume rewriting
- Hire probability estimation (heuristic)
- Job risk intelligence
- Fraud detection
- Entry barrier analysis
- Market opportunity recommendations
- Cover letter generation
- Interview preparation
- Strategic dashboard
- Export to TXT, Markdown, and JSON

## Installation

```bash
pip install -r requirements.txt
```

PDF and DOCX support require `pypdf` and `python-docx`. The program
still runs without them for plain-text and Markdown files.

## Run

The repository folder is the `aelm` package. From the directory that
contains it (rename the folder to `aelm` if needed):

```bash
python -m aelm
```

Then use `help` inside the CLI to see all commands.

## Optional LLM chat

The `chat` command is disabled by default. To enable it, set:

```bash
export AELM_HF_TOKEN=<your Hugging Face token>
```

Related settings (all optional): `AELM_API_URL`, `AELM_MODEL`,
`AELM_TEMPERATURE`, `AELM_MAX_TOKENS`, `AELM_TIMEOUT`,
`AELM_MAX_HISTORY`, `AELM_EXPORT_DIR`.

## Project Structure

- `__main__.py` — entry point (`python -m aelm`)
- `cli.py` — interactive command loop
- `config.py` — central configuration
- `session.py` — in-memory session state
- `pipeline.py` — runs the full analysis pipeline
- `export.py` — TXT / Markdown / JSON export
- `parsing/` — file loading, resume parser, job parser
- `engines/` — matching, ATS, rewriting, risk, fraud, barriers,
  market, cover letter, interview, dashboard
- `llm/` — optional LLM chat router and system prompt
- `tests/`, `docs/`, `examples/`, `plugins/` — scaffolding

## Commands

help, load resume, load job, analyze, dashboard, ats, rewrite,
coverletter, interview, market, risk, export, status, clear, config,
version, chat, exit

## Design Principles

- Never fabricate qualifications.
- Use heuristic estimates where appropriate.
- Keep resume optimizations truthful.
- Ask for missing information rather than guessing.
