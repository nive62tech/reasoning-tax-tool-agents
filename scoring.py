"""Answer parsing, scoring, and failure classification."""
import re


def extract_answer(text):
    if not text:
        return None
    m = re.findall(r"ANSWER\s*:\s*(.+)", text, flags=re.IGNORECASE)
    return m[-1].strip().strip("*`").strip() if m else None


def _norm_str(s):
    return re.sub(r"[\s_]+", "_", s.strip().strip("\"'.*`").lower())


def _to_num(s):
    s = re.sub(r"[,$%€£\s]", "", s)
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def answer_matches(task, ans):
    if ans is None:
        return False
    t, exp = task["answer_type"], task["expected"]
    if t == "str":
        return _norm_str(ans) == _norm_str(str(exp))
    if t == "bool":
        a = _norm_str(ans)
        a = {"true": "yes", "false": "no"}.get(a, a)
        return a == exp
    if t == "num":
        v = _to_num(ans)
        return v is not None and abs(v - float(exp)) <= 0.011
    if t == "set":
        got = {x.upper() for x in re.findall(r"[A-Za-z]\d+", ans)}
        return got == {x.upper() for x in exp}
    raise ValueError(t)


def score_run(task, final_text, tool_names):
    ans = extract_answer(final_text)
    ans_ok = answer_matches(task, ans)
    req_ok = set(task["required_tools"]).issubset(set(tool_names))
    return {"final_answer": ans, "answer_correct": ans_ok, "required_ok": req_ok,
            "correct": bool(ans_ok and req_ok)}


def classify_failure(row):
    """None if correct; otherwise a coarse failure category."""
    if row["correct"]:
        return None
    if row["final_answer"] is None:
        return "no final answer (ran out of turns/tokens)"
    if not row["required_ok"] and not row["answer_correct"]:
        return "skipped required tool calls"
    if not row["required_ok"] and row["answer_correct"]:
        return "right answer without required calls (guess)"
    if row["n_tool_errors"] > 0:
        return "tool errors (bad IDs/arguments) then wrong answer"
    return "wrong answer despite correct calls (reasoning/arithmetic/misread)"
