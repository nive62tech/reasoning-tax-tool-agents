"""Provider adapters. Each exposes run(task, db, cond, state) which runs the tool-calling
loop for one task and fills `state` in place (so partial data survives exceptions).

state keys: input, output, thinking, cache_creation, cache_read (token counts), tool_log,
thinking_chars, api_s, wait_s (throttle/backoff sleeping, excluded from reported wall time),
turns, final_text, stop_reason
"""
import json
import re
import threading
import time

import config
from mockdb import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = (
    "You are an operations assistant for an online store. You have tools that query the store's "
    "database. Use the tools to find information; never guess IDs or values, and do arithmetic carefully. "
    "If an entity does not exist, answer NOT_FOUND. When you are finished, end your reply with a single "
    "final line in exactly this form:\nANSWER: <answer>\n"
    "Answer formats: numbers as plain digits with up to 2 decimals (no currency symbols or units); "
    "yes/no questions as 'yes' or 'no'; lists of IDs comma-separated; text values exactly as stored."
)


class QuotaExhausted(Exception):
    """Daily quota hit: stop the whole run; re-run later (finished runs are kept)."""


def new_state():
    return {"input": 0, "output": 0, "thinking": 0, "cache_creation": 0, "cache_read": 0, "tool_log": [],
            "thinking_chars": 0, "api_s": 0.0, "wait_s": 0.0, "turns": 0, "final_text": "", "stop_reason": None}


# ------------------------------------------------------------------ Anthropic
class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client):
        self.client = client

    def run(self, task, db, cond, st):
        messages = [{"role": "user", "content": task["prompt"]}]
        for _ in range(config.MAX_TURNS):
            kw = dict(model=cond["model"], max_tokens=config.MAX_TOKENS, system=SYSTEM_PROMPT,
                      tools=TOOL_SCHEMAS, messages=messages)
            if cond["thinking"]:
                kw["thinking"] = cond["thinking"]
            elif config.BASELINE_TEMPERATURE is not None:
                kw["temperature"] = config.BASELINE_TEMPERATURE
            c0 = time.perf_counter()
            resp = self.client.messages.create(**kw)
            st["api_s"] += time.perf_counter() - c0
            st["turns"] += 1
            us = resp.usage
            st["input"] += us.input_tokens or 0
            st["output"] += us.output_tokens or 0
            st["cache_creation"] += getattr(us, "cache_creation_input_tokens", 0) or 0
            st["cache_read"] += getattr(us, "cache_read_input_tokens", 0) or 0
            st["stop_reason"] = resp.stop_reason
            for b in resp.content:
                if b.type == "thinking":
                    st["thinking_chars"] += len(getattr(b, "thinking", "") or "")
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason == "tool_use":
                results = []
                for b in resp.content:
                    if b.type == "tool_use":
                        res, is_err = execute_tool(db, b.name, b.input)
                        st["tool_log"].append({"name": b.name, "args": b.input, "error": is_err})
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": json.dumps(res), "is_error": is_err})
                messages.append({"role": "user", "content": results})
            else:
                st["final_text"] = "".join(b.text for b in resp.content if b.type == "text")
                break


# ----------------------------------------------------------------------- Gemini
class _Throttle:
    """Global client-side pacing so a free-tier requests-per-minute cap is not exceeded."""
    def __init__(self, rpm):
        self.interval = 60.0 / rpm if rpm and rpm > 0 else 0.0
        self.lock, self.next_ok = threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delay = max(0.0, self.next_ok - now)
            self.next_ok = max(now, self.next_ok) + self.interval
        if delay:
            time.sleep(delay)
        return delay


def _parse_thinking(spec):
    kind, _, val = spec.partition(":")
    if kind == "level":
        return {"thinking_level": val.upper()}
    if kind == "budget":
        return {"thinking_budget": int(val)}
    raise ValueError(f"Bad thinking spec {spec!r}; use level:<minimal|low|medium|high> or budget:<int>")


def _gemini_tools(types):
    decls = [types.FunctionDeclaration(name=s["name"], description=s["description"],
                                       parameters_json_schema=s["input_schema"]) for s in TOOL_SCHEMAS]
    return [types.Tool(function_declarations=decls)]


class GeminiProvider:
    name = "gemini"

    def __init__(self, client, types, errors, rpm=None):
        self.client, self.types, self.errors = client, types, errors
        self.throttle = _Throttle(config.GEMINI_RPM if rpm is None else rpm)
        self.tools = _gemini_tools(types)

    def _call(self, model, contents, cfg, st):
        """One API call with pacing + retry/backoff. Sleeping is tracked in st['wait_s']."""
        for attempt in range(7):
            st["wait_s"] += self.throttle.wait()
            c0 = time.perf_counter()
            try:
                resp = self.client.models.generate_content(model=model, contents=contents, config=cfg)
                st["api_s"] += time.perf_counter() - c0
                return resp
            except self.errors.APIError as e:
                st["api_s"] += time.perf_counter() - c0
                msg = str(e)
                if e.code == 429 and re.search(r"per ?day|PerDay|daily", msg, re.I):
                    raise QuotaExhausted(msg[:300])
                if e.code in (429, 500, 502, 503, 504) and attempt < 6:
                    m = re.search(r"retry in ([\d.]+)s", msg, re.I)
                    delay = float(m.group(1)) + 1 if m else min(90, 5 * 2 ** attempt)
                    time.sleep(delay)
                    st["wait_s"] += delay
                    continue
                raise
        raise RuntimeError("retries exhausted")

    def run(self, task, db, cond, st):
        t = self.types
        cfg = t.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, tools=self.tools,
            thinking_config=t.ThinkingConfig(**_parse_thinking(cond["thinking"])),
            max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
            automatic_function_calling=t.AutomaticFunctionCallingConfig(disable=True),
        )
        contents = [t.Content(role="user", parts=[t.Part(text=task["prompt"])])]
        for _ in range(config.MAX_TURNS):
            resp = self._call(cond["model"], contents, cfg, st)
            st["turns"] += 1
            um = resp.usage_metadata
            if um:
                thoughts = um.thoughts_token_count or 0
                st["input"] += (um.prompt_token_count or 0) + (um.tool_use_prompt_token_count or 0)
                st["output"] += (um.candidates_token_count or 0) + thoughts   # thinking is billed as output
                st["thinking"] += thoughts
            cand = resp.candidates[0] if resp.candidates else None
            st["stop_reason"] = str(cand.finish_reason) if cand and cand.finish_reason else "no_candidate"
            if not cand or not cand.content or not cand.content.parts:
                break
            parts = cand.content.parts
            # Return the ENTIRE model turn (incl. thought signatures) on the next request.
            contents.append(cand.content)
            calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
            if calls:
                resp_parts = []
                for fc in calls:
                    args = dict(fc.args or {})
                    res, is_err = execute_tool(db, fc.name, args)
                    st["tool_log"].append({"name": fc.name, "args": args, "error": is_err})
                    resp_parts.append(t.Part.from_function_response(
                        name=fc.name, response={"error": res["error"]} if is_err else {"result": res}))
                contents.append(t.Content(role="user", parts=resp_parts))
            else:
                st["final_text"] = "".join(p.text for p in parts if p.text and not getattr(p, "thought", False))
                break
