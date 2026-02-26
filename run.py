#!/usr/bin/env python3
"""CLI entrypoint for crisis simulations."""

import argparse
import sys
from pathlib import Path

from src.models import ClaudeModel, GeminiModel, OpenAIModel
from src.runner import run_simulation
from src.evaluator import evaluate_transcript


SCENARIOS = {
    "debt": "scenarios/sovereign_debt_domino.yaml",
    "rare-earth": "scenarios/rare_earth_embargo.yaml",
    "displacement": "scenarios/slow_displacement.yaml",
}


def cmd_run(args):
    """Run a crisis simulation."""
    scenario_path = SCENARIOS.get(args.scenario)
    if not scenario_path:
        print(f"Unknown scenario: {args.scenario}")
        print(f"Available: {', '.join(SCENARIOS.keys())}")
        sys.exit(1)

    # Build model list
    models = []

    if args.claude_model:
        models.append(ClaudeModel(model=args.claude_model))
    else:
        models.append(ClaudeModel())

    if args.gemini_model:
        models.append(GeminiModel(model=args.gemini_model))
    else:
        models.append(GeminiModel())

    if args.openai_model:
        models.append(OpenAIModel(model=args.openai_model))
    else:
        models.append(OpenAIModel())

    print(f"Running scenario: {args.scenario}")
    print(f"Models: {', '.join(f'{m.label} ({m.model})' for m in models)}")
    print()

    transcript = run_simulation(scenario_path, models, verbose=not args.quiet)
    output_file = transcript.save()
    print(f"\nTranscript saved to: {output_file}")


def cmd_evaluate(args):
    """Evaluate a transcript."""
    if not Path(args.transcript).exists():
        print(f"Transcript not found: {args.transcript}")
        sys.exit(1)

    evaluate_transcript(args.transcript)


def cmd_list(args):
    """List available scenarios."""
    for key, path in SCENARIOS.items():
        print(f"  {key:<15} {path}")


def main():
    parser = argparse.ArgumentParser(description="Crisis Simulation Bench")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a crisis simulation")
    run_parser.add_argument("scenario", choices=list(SCENARIOS.keys()), help="Scenario to run")
    run_parser.add_argument("--claude-model", default=None, help="Claude model ID")
    run_parser.add_argument("--gemini-model", default=None, help="Gemini model ID")
    run_parser.add_argument("--openai-model", default=None, help="OpenAI model ID")
    run_parser.add_argument("--quiet", action="store_true", help="Suppress live output")
    run_parser.set_defaults(func=cmd_run)

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a transcript")
    eval_parser.add_argument("transcript", help="Path to transcript JSON file")
    eval_parser.set_defaults(func=cmd_evaluate)

    # List command
    list_parser = subparsers.add_parser("list", help="List available scenarios")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
