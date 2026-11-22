"""Offline simulator used by --dry-run. It replays each task's reference tool calls
and returns a (sometimes deliberately wrong) answer, with made-up token usage.
Purpose: test the harness and analysis pipeline without spending API credits.
The numbers it produces are NOT real results."""
import json
import random
from types import SimpleNamespace as NS


class FakeClient:
    def __init__(self, tasks):
        self.by_prompt = {t["prompt"]: t for t in tasks}
        self.messages = self

    def create(self, **kw):
        msgs = kw["messages"]
        task = self.by_prompt[msgs[0]["content"]]
        thinking = bool(kw.get("thinking"))
        step = sum(1 for m in msgs if m["role"] == "user" and isinstance(m["content"], list))
        rng = random.Random(f"{task['id']}|{thinking}|{len(msgs)}")
        calls = task["reference_calls"]
        ctx = 400 + 250 * step
        think_tok = rng.randint(300, 1500) if thinking else 0
        if step < len(calls):
            name, args = calls[step]
            content = [NS(type="tool_use", id=f"tu_{step}", name=name, input=args)]
            out = 40 + think_tok
            stop = "tool_use"
        else:
            p_wrong = {1: 0.02, 2: 0.08, 3: 0.40}[task["tier"]] if not thinking else {1: 0.02, 2: 0.04, 3: 0.12}[task["tier"]]
            wrong = random.Random(f"w|{task['id']}|{thinking}").random() < p_wrong
            exp = task["expected"]
            ans = "0" if wrong else (", ".join(exp) if isinstance(exp, list) else str(exp))
            content = [NS(type="text", text=f"Done.\nANSWER: {ans}")]
            out = 30 + think_tok
            stop = "end_turn"
        if thinking:
            content.insert(0, NS(type="thinking", thinking="x" * (think_tok * 4), signature="sig"))
        usage = NS(input_tokens=ctx, output_tokens=out, cache_creation_input_tokens=0, cache_read_input_tokens=0)
        return NS(content=content, stop_reason=stop, usage=usage)
