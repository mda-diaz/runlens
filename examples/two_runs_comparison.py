"""
Example: two runs of the same Q&A agent — one efficient, one wasteful.

Run this script to generate two completed run records saved to runs.json.
The output is suitable for loading into the RunLens comparison view.

Usage:
    cd examples/
    python two_runs_comparison.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "sdk-python"))

from runlens import start_run, record_step, end_run

STORAGE = str(Path(__file__).parent / "runs.json")


def run_efficient_agent():
    """
    Well-tuned agent: 3 focused steps, no redundancy.
    Context: gpt-4o, prompt v3, temperature 0.3
    """
    run = start_run(
        task="answer_question: What are the benefits of transformer models?",
        context={
            "model": "gpt-4o",
            "prompt_version": "v3",
            "tools": ["search"],
            "temperature": 0.3,
            "agent_version": "1.2.0",
            "max_retries": 1,
        },
        storage_path=STORAGE,
    )

    # Step 1: single search query
    record_step(
        run.id,
        step_type="tool_call",
        name="search_web",
        input={"query": "benefits of transformer models in NLP"},
        output={
            "results": [
                "Transformers handle long-range dependencies via self-attention.",
                "Parallelisable training unlike RNNs.",
                "Pre-training + fine-tuning enables transfer learning.",
            ]
        },
        cost=0.001,
        tokens=120,
        duration_ms=340,
    )

    # Step 2: single LLM synthesis
    record_step(
        run.id,
        step_type="llm_call",
        name="synthesize_answer",
        input={
            "system": "You are a helpful assistant. Answer concisely.",
            "user": "Summarise the benefits of transformer models using the search results.",
            "search_results": [
                "Transformers handle long-range dependencies via self-attention.",
                "Parallelisable training unlike RNNs.",
                "Pre-training + fine-tuning enables transfer learning.",
            ],
        },
        output={
            "text": (
                "Transformer models offer three key benefits: (1) self-attention "
                "captures long-range dependencies more effectively than RNNs, "
                "(2) their architecture is fully parallelisable enabling faster training, "
                "and (3) pre-trained models can be fine-tuned for downstream tasks "
                "with minimal data."
            )
        },
        cost=0.018,
        tokens=1800,
        duration_ms=1200,
    )

    # Step 3: format and return
    record_step(
        run.id,
        step_type="tool_call",
        name="format_response",
        input={"text": "Transformer models offer three key benefits..."},
        output={"formatted": True},
        cost=0.0,
        tokens=0,
        duration_ms=5,
    )

    result = end_run(run.id)
    print(f"[efficient]  run_id={result['id'][:8]}  cost=${result['total_cost']:.4f}  "
          f"tokens={result['total_tokens']}  steps={len(result['steps'])}  "
          f"duration={result['duration_ms']}ms")
    return result


def run_wasteful_agent():
    """
    Poorly-tuned agent: redundant searches, re-formatting, retry loops.
    Context: gpt-4o, prompt v1, temperature 0.9
    """
    run = start_run(
        task="answer_question: What are the benefits of transformer models?",
        context={
            "model": "gpt-4o",
            "prompt_version": "v1",
            "tools": ["search"],
            "temperature": 0.9,
            "agent_version": "1.1.0",
            "max_retries": 3,
        },
        storage_path=STORAGE,
    )

    # Step 1: first search (too broad)
    record_step(
        run.id,
        step_type="tool_call",
        name="search_web",
        input={"query": "transformers"},
        output={
            "results": [
                "Transformers are electrical devices used in power distribution.",
                "Transformers (film) is a 2007 science-fiction action film.",
                "Transformer architecture introduced in 'Attention Is All You Need'.",
            ]
        },
        cost=0.001,
        tokens=130,
        duration_ms=420,
    )

    # Step 2: LLM decides results are irrelevant, requests another search
    record_step(
        run.id,
        step_type="llm_call",
        name="evaluate_results",
        input={
            "system": "You are an agent. Decide if search results are relevant.",
            "user": "Are these results relevant to 'benefits of transformer models'?",
            "results": ["Electrical devices...", "2007 film...", "Attention Is All You Need..."],
        },
        output={"decision": "retry_search", "reason": "results too broad"},
        cost=0.012,
        tokens=900,
        duration_ms=980,
    )

    # Step 3: second search (better query, should have been used first)
    record_step(
        run.id,
        step_type="tool_call",
        name="search_web_retry",
        input={"query": "advantages of transformer architecture machine learning"},
        output={
            "results": [
                "Transformers handle long-range dependencies via self-attention.",
                "Parallelisable training unlike RNNs.",
                "Pre-training + fine-tuning enables transfer learning.",
            ]
        },
        cost=0.001,
        tokens=125,
        duration_ms=390,
    )

    # Step 4: LLM generates answer (but with high temperature — verbose and unfocused)
    record_step(
        run.id,
        step_type="llm_call",
        name="generate_answer",
        input={
            "system": "You are a helpful assistant.",
            "user": "Explain the benefits of transformer models in detail.",
            "search_results": [
                "Transformers handle long-range dependencies via self-attention.",
                "Parallelisable training unlike RNNs.",
                "Pre-training + fine-tuning enables transfer learning.",
            ],
        },
        output={
            "text": (
                "Transformer models, which were introduced in the seminal paper "
                "'Attention Is All You Need' by Vaswani et al., have revolutionised "
                "the field of natural language processing and beyond. There are "
                "numerous benefits to consider when evaluating transformer-based "
                "architectures for your machine learning needs. First and foremost, "
                "transformers leverage a mechanism called self-attention, which "
                "allows the model to weigh the importance of different tokens in the "
                "input sequence when producing each output token. This is incredibly "
                "powerful because... [continues for 600 more tokens]"
            )
        },
        cost=0.042,
        tokens=3800,
        duration_ms=3100,
    )

    # Step 5: LLM decides the answer is too long, trims it
    record_step(
        run.id,
        step_type="llm_call",
        name="trim_answer",
        input={
            "system": "Shorten the following answer to under 100 words.",
            "user": "Transformer models, which were introduced...",
        },
        output={
            "text": (
                "Transformers offer three key benefits: self-attention handles "
                "long-range dependencies, the architecture is parallelisable for "
                "fast training, and pre-trained models can be fine-tuned with "
                "minimal data."
            )
        },
        cost=0.021,
        tokens=1950,
        duration_ms=1450,
    )

    # Step 6: formatting (same as efficient run)
    record_step(
        run.id,
        step_type="tool_call",
        name="format_response",
        input={"text": "Transformers offer three key benefits..."},
        output={"formatted": True},
        cost=0.0,
        tokens=0,
        duration_ms=5,
    )

    result = end_run(run.id)
    print(f"[wasteful]   run_id={result['id'][:8]}  cost=${result['total_cost']:.4f}  "
          f"tokens={result['total_tokens']}  steps={len(result['steps'])}  "
          f"duration={result['duration_ms']}ms")
    return result


if __name__ == "__main__":
    print("Simulating two agent runs...\n")
    efficient = run_efficient_agent()
    wasteful = run_wasteful_agent()

    cost_diff = wasteful["total_cost"] - efficient["total_cost"]
    token_diff = wasteful["total_tokens"] - efficient["total_tokens"]

    print(f"\nComparison summary:")
    print(f"  Cost overhead:   +${cost_diff:.4f} ({cost_diff / efficient['total_cost'] * 100:.0f}% more)")
    print(f"  Token overhead:  +{token_diff} tokens ({token_diff / efficient['total_tokens'] * 100:.0f}% more)")
    print(f"  Extra steps:     {len(wasteful['steps']) - len(efficient['steps'])}")
    print(f"\nContext diffs:")
    for key in efficient["context"]:
        v_eff = efficient["context"][key]
        v_wst = wasteful["context"][key]
        if v_eff != v_wst:
            print(f"  {key}: {v_wst!r} -> {v_eff!r}")
    print(f"\nRun data saved to: {STORAGE}")
