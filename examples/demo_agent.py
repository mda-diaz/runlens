"""
RunLens Demo — The Case of the Expensive Agent
================================================
A support bot that answers customer questions.
Two versions of the same agent. Same task. Very different behavior.

Run this script, then go to runlens-api.onrender.com to see the comparison.

Requirements:
    pip install runlens-sdk
"""

import os
import time

from runlens import start_run as sdk_start_run, record_step, end_run as sdk_end_run

API = os.getenv("RUNLENS_API", "http://localhost:8000")


# ── helpers ────────────────────────────────────────────────────────────────

def start_run(task, context):
    handle = sdk_start_run(task=task, context=context, api_url=API)
    return handle.id

def step(run_id, name, step_type, inp, out, cost, tokens):
    record_step(run_id=run_id, name=name, step_type=step_type,
                input=inp, output=out, cost=cost, tokens=tokens)
    time.sleep(0.05)  # makes the timeline feel real

def end_run(run_id, cost, tokens, duration_ms):
    sdk_end_run(run_id)


# ── scenario ───────────────────────────────────────────────────────────────

TASK = "customer support: refund request"
QUESTION = "Hi, I ordered the wrong size. Can I get a refund?"

print("\n🎬  RunLens Demo — The Case of the Expensive Agent")
print("=" * 52)
print(f"\nScenario: A customer support agent answering —")
print(f'  "{QUESTION}"')
print("\nWe'll run two versions and compare what happened.\n")


# ── Run A: the over-engineered agent ───────────────────────────────────────

print("▶  Run A  |  gpt-4o  |  prompt v1  (the original)")

run_a = start_run(TASK, {
    "model": "gpt-4o",
    "prompt_version": "v1",
    "temperature": 0.8,
    "tools": ["search_orders", "check_policy", "search_knowledge_base", "draft_response"],
    "agent_version": "1.0.0",
})

step(run_a, "classify intent",   "llm_call",
     {"message": QUESTION},
     {"intent": "refund_request", "confidence": 0.97},
     cost=0.004, tokens=310)

step(run_a, "search_orders",     "tool_call",
     {"customer_id": "cust_9182", "query": "recent orders"},
     {"orders": [{"id": "ORD-441", "item": "Blue Hoodie M", "status": "delivered"}]},
     cost=0.0, tokens=0)

step(run_a, "check_policy",      "tool_call",
     {"policy_type": "returns"},
     {"window_days": 30, "condition": "unworn with tags"},
     cost=0.0, tokens=0)

step(run_a, "search_knowledge_base", "tool_call",
     {"query": "refund process wrong size"},
     {"result": "Customers may return items within 30 days for a full refund."},
     cost=0.0, tokens=0)

# The agent gets confused and re-checks the policy
step(run_a, "check_policy (retry)", "tool_call",
     {"policy_type": "returns", "detail": "size exchange vs refund"},
     {"window_days": 30, "refund": True, "exchange": True},
     cost=0.0, tokens=0)

step(run_a, "draft response",    "llm_call",
     {"context": "ORD-441, policy: 30d refund, customer eligible"},
     {"draft": "Hi! I've looked into your order ORD-441..."},
     cost=0.006, tokens=480)

# Another LLM call to review its own draft — completely unnecessary
step(run_a, "review draft",      "llm_call",
     {"draft": "Hi! I've looked into your order ORD-441..."},
     {"approved": True, "note": "response looks good"},
     cost=0.005, tokens=400)

step(run_a, "send response",     "tool_call",
     {"channel": "email"},
     {"status": "sent", "message_id": "msg_773"},
     cost=0.0, tokens=0)

end_run(run_a, cost=0.015, tokens=1190, duration_ms=4200)
print(f"   ✓  Done  |  cost: $0.015  |  8 steps  |  4.2s\n")


# ── Run B: the lean agent ───────────────────────────────────────────────────

print("▶  Run B  |  gpt-4o-mini  |  prompt v2  (optimized)")

run_b = start_run(TASK, {
    "model": "gpt-4o-mini",
    "prompt_version": "v2",
    "temperature": 0.3,
    "tools": ["search_orders", "check_policy", "draft_response"],
    "agent_version": "1.1.0",
})

step(run_b, "classify + fetch context", "llm_call",
     {"message": QUESTION},
     {"intent": "refund_request", "order_id": "ORD-441", "policy": "30d refund"},
     cost=0.001, tokens=210)

step(run_b, "search_orders",     "tool_call",
     {"customer_id": "cust_9182"},
     {"orders": [{"id": "ORD-441", "item": "Blue Hoodie M", "status": "delivered"}]},
     cost=0.0, tokens=0)

step(run_b, "draft response",    "llm_call",
     {"context": "ORD-441, policy: 30d refund, customer eligible"},
     {"draft": "Hi! I've looked into your order ORD-441..."},
     cost=0.002, tokens=180)

step(run_b, "send response",     "tool_call",
     {"channel": "email"},
     {"status": "sent", "message_id": "msg_774"},
     cost=0.0, tokens=0)

end_run(run_b, cost=0.003, tokens=390, duration_ms=1100)
print(f"   ✓  Done  |  cost: $0.003  |  4 steps  |  1.1s\n")


# ── summary ────────────────────────────────────────────────────────────────

print("=" * 52)
print("📊  Results")
print(f"   Run A: $0.015  |  1190 tokens  |  8 steps  |  4.2s")
print(f"   Run B: $0.003  |   390 tokens  |  4 steps  |  1.1s")
print(f"\n   Run B is 5x cheaper and 4x faster.")
print(f"   Same output. Same customer. Same answer.")
print()
print("🔍  What changed?")
print("   • model: gpt-4o → gpt-4o-mini")
print("   • prompt_version: v1 → v2 (merged classify+fetch into one call)")
print("   • removed: search_knowledge_base (redundant with check_policy)")
print("   • removed: review draft (self-review added cost, no value)")
print()
print("➡  Open apps/web/index.html to see this in RunLens.")
print(f"   Select both runs and click Compare.\n")
