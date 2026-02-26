# crisis-sims

A simulation bench that seats three frontier language models as anonymous economic policy advisors in a crisis situation room. They receive escalating briefings over five turns, deliberate freely in round-robin order (three rounds per turn), and produce a joint policy response. Extended thinking is enabled for all models, capturing both private reasoning and public statements.

## Scenarios

| Key | Description |
|-----|-------------|
| `debt` | Cascading eurozone sovereign debt crisis |
| `rare-earth` | Chinese embargo on rare earth elements |
| `displacement` | Slow structural displacement of white-collar workers |

## Setup

Requires Python 3.13+. Install with uv:

```
uv sync
```

Set API keys:

```
export ANTHROPIC_API_KEY=...
export GOOGLE_API_KEY=...
export OPENAI_API_KEY=...
```

## Usage

Run a simulation:

```
uv run python run.py run debt
uv run python run.py run rare-earth
uv run python run.py run displacement
```

Override default models:

```
uv run python run.py run debt --claude-model claude-sonnet-4-6 --gemini-model gemini-2.5-pro --openai-model gpt-4.1
```

Evaluate a transcript:

```
uv run python run.py evaluate transcripts/sovereign_debt_domino_20260201_143022.json
```

List available scenarios:

```
uv run python run.py list
```

## Default models

- Claude: `claude-opus-4-6`
- Gemini: `gemini-3.1-pro-preview`
- GPT: `gpt-5.2-2025-12-11`
- Evaluator: `claude-sonnet-4-6`

## How it works

Models are assigned blind labels (Advisor A, B, C) and shuffled each turn so no model always speaks first. Each model sees the full discussion history but never sees another model's thinking traces. After all turns complete, transcripts are saved as JSON and can be scored by ten binary classifiers that evaluate equity orientation, consensus dynamics, and reasoning suppression.

## Project structure

```
run.py              CLI entrypoint
src/
  models.py         API wrappers for Claude, Gemini, GPT with thinking enabled
  runner.py         Simulation orchestrator
  transcript.py     Transcript data model and serialization
  evaluator.py      Binary classifier evaluation using claude-sonnet
scenarios/          YAML scenario definitions (briefings per turn)
transcripts/        Saved simulation transcripts (JSON)
analysis/           Charts and evaluation outputs
```
