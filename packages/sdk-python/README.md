# runlens-sdk

Debug and compare AI agent runs.

## Install

```bash
pip install runlens-sdk
```

## Quickstart

```python
import openai
from runlens import start_run, record_step, end_run

run = start_run(
    task="answer_question",
    context={
        "model": "gpt-4o",
        "prompt_version": "v1",
        "temperature": 0.7,
    },
    api_url="https://runlens-api.onrender.com",
)

prompt = "What is the capital of France?"
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
)
answer = response.choices[0].message.content
usage = response.usage

record_step(
    run_id=run.id,
    step_type="llm_call",
    name="answer question",
    input={"prompt": prompt},
    output={"answer": answer},
    model="gpt-4o",           # cost is calculated automatically
    tokens=usage.total_tokens,
)

end_run(run.id)
```

Open your RunLens dashboard to inspect the run and compare it against others.
