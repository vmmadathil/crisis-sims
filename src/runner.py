"""Orchestrates multi-agent crisis simulations."""

import random
import yaml
from typing import List, Dict

from .models import ModelResponse
from .transcript import Transcript

# Blind labels — models see these instead of "Claude", "Gemini", "GPT"
BLIND_LABELS = ["Advisor A", "Advisor B", "Advisor C"]

# Discussion rounds per turn
ROUNDS_PER_TURN = 3


def load_scenario(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_messages_for_model(
    transcript: Transcript,
    model_label: str,
    label_map: Dict[str, str],
) -> List[Dict]:
    """Build message history from a specific model's perspective.

    That model's own prior responses become "assistant" messages.
    Everything else (briefings + other models) become "user" messages.
    Thinking traces are NEVER included — models only see what was "said."
    Real model names are replaced with blind labels.
    """
    messages = []
    for msg in transcript.messages:
        if msg.role == "briefing":
            messages.append({
                "role": "user",
                "content": "[BRIEFING — %s]\n\n%s" % (msg.turn_title, msg.content),
            })
        elif msg.role == model_label:
            messages.append({
                "role": "assistant",
                "content": msg.content,
            })
        else:
            blind = label_map.get(msg.role, msg.role)
            messages.append({
                "role": "user",
                "content": "[%s]: %s" % (blind, msg.content),
            })

    # Merge consecutive same-role messages (some APIs require alternation)
    merged = []
    for msg in messages:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n\n" + msg["content"]
        else:
            merged.append(msg)

    return merged


def run_simulation(scenario_path: str, models: list, verbose: bool = True) -> Transcript:
    """Run a full crisis simulation.

    Args:
        scenario_path: Path to scenario YAML file.
        models: List of model instances (ClaudeModel, GeminiModel, OpenAIModel).
        verbose: Print progress to stdout.
    """
    scenario = load_scenario(scenario_path)
    transcript = Transcript(
        scenario_name=scenario["name"],
        models=["%s (%s)" % (m.label, m.model) for m in models],
    )
    system_prompt = scenario["system_context"]

    # Build blind label mapping
    label_map = {}
    for i, model in enumerate(models):
        label_map[model.label] = BLIND_LABELS[i] if i < len(BLIND_LABELS) else "Advisor %d" % (i + 1)

    for turn_idx, turn in enumerate(scenario["turns"]):
        turn_num = turn_idx + 1
        turn_title = turn["title"]
        briefing = turn["briefing"]

        # Randomize model order for this turn
        turn_order = list(models)
        random.shuffle(turn_order)

        if verbose:
            print("\n" + "=" * 60)
            print("TURN %d: %s" % (turn_num, turn_title))
            print("Speaking order: %s" % " -> ".join(m.label for m in turn_order))
            print("=" * 60)
            print("\n%s\n" % briefing)

        # Post the briefing
        transcript.add_briefing(briefing, turn_num, turn_title)

        # Multiple rounds of discussion per turn
        for round_num in range(1, ROUNDS_PER_TURN + 1):
            if verbose:
                print("\n--- Round %d of %d ---" % (round_num, ROUNDS_PER_TURN))

            for model in turn_order:
                if verbose:
                    print("\n  %s (%s):" % (model.label, label_map[model.label]))

                messages = build_messages_for_model(transcript, model.label, label_map)
                response = model.respond(system_prompt, messages)

                transcript.add_response(
                    model_label=response.model_label,
                    model_id=response.model_id,
                    content=response.content,
                    turn=turn_num,
                    turn_title=turn_title,
                    thinking=response.thinking,
                )

                if verbose:
                    if response.thinking:
                        print("\n  [THINKING]:\n%s" % response.thinking)

                    print("\n  [SAID]:\n%s" % response.content)

    return transcript
