"""Check recorded, synthetic text conversations without executing a workflow or service.

These assertions target the three fixed simulation scripts, not arbitrary natural language.
They do not establish speech recognition, physical hangup or live integration behavior.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

Data = dict[str, Any]
Call = tuple[int, str, Data]
END = "hr_builtin_tool__end_conversation"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_conversation(record: Data) -> None:
    """Fail on an incorrect amount, missing clarification, false offer or broken ending."""
    _require(record.get("status", "completed") == "completed", "simulation is not complete")
    _require(record.get("close_reason") != "idle_timeout", "simulation reached idle timeout")
    messages = record["messages"]
    calls = _calls(messages)
    names = [name for _, name, _ in calls]
    _check_ending(messages, calls)
    kind = record["kind"]
    if kind == "refusal":
        _require("verify_carrier" in names, "check authority before refusing")
        _require(
            not set(names) & {"find_loads", "negotiate", "send_code", "verify_code"},
            "refused carrier must not proceed",
        )
        return
    _require(
        names.index("verify_carrier") < names.index("verify_code") < names.index("find_loads"),
        "verification must precede matching",
    )
    text = " ".join(m.get("content", "") for m in messages if m["role"] == "assistant")
    _require(
        bool(re.search(r"November\s+7\b.*11:04\s*PM.*(?:Central|CST)", text, re.I)),
        "pitch must retain the supplied Central Time date and clock",
    )
    if kind == "compound":
        _check_compound(messages, calls)
        _check_handoff(messages, calls)
    elif kind == "repeat":
        _check_repeat(messages, calls)
    else:
        raise ValueError(f"unknown simulation kind: {kind}")


def _calls(messages: list[Data]) -> list[Call]:
    return [
        (i, call["function"]["name"], json.loads(call["function"]["arguments"]))
        for i, message in enumerate(messages)
        for call in message.get("tool_calls", [])
    ]


def _check_ending(messages: list[Data], calls: list[Call]) -> None:
    closes = [i for i, name, _ in calls if name == "close_call"]
    ends = [i for i, name, _ in calls if name == END]
    _require(len(closes) == len(ends) == 1, "closing and built-in ending must each occur once")
    _require(calls[-1][1] == END, "built-in ending must be last")
    spoken = _spoken(messages)
    goodbye = [i for i, text in spoken if re.search(r"\bgoodbye\b", text, re.I)]
    _require(bool(goodbye), "speak goodbye after closing")
    _require(closes[0] < goodbye[0] <= ends[0], "speak goodbye after closing")
    _check_final_words(spoken, closes[0], goodbye[0])
    _check_no_wait(messages, goodbye[0], ends[0])


def _spoken(messages: list[Data]) -> list[tuple[int, str]]:
    return [(i, m.get("content", "")) for i, m in enumerate(messages) if m["role"] == "assistant"]


def _check_final_words(spoken: list[tuple[int, str]], close_at: int, goodbye_at: int) -> None:
    _require(not any(text for i, text in spoken if i > goodbye_at), "no speech after goodbye")
    _require(not any("?" in text for i, text in spoken if i > close_at), "no closing questions")


def _check_no_wait(messages: list[Data], goodbye_at: int, end_at: int) -> None:
    _require(
        not any(m["role"] == "user" for m in messages[goodbye_at + 1 : end_at + 1]),
        "do not wait for another caller turn after goodbye",
    )


def _check_compound(messages: list[Data], calls: list[Call]) -> None:
    ambiguous, clarified = _amount_turns(messages)
    _check_clarification(messages[ambiguous + 1 : clarified])
    negotiations = [(i, args) for i, name, args in calls if name == "negotiate"]
    _require(len(negotiations) == 1, "one clarified total must reach negotiation once")
    at, args = negotiations[0]
    _require(at > clarified and args["rate"] == "1625", "submit exactly 1625 after clarification")
    _require(args["load_id"] == "LD90001", "negotiate the offered load")
    matched_at = next(i for i, name, _ in calls if name == "find_loads")
    close_at = next(i for i, name, _ in calls if name == "close_call")
    _require(matched_at < at < close_at, "match, negotiate and close must occur in order")


def _check_clarification(messages: list[Data]) -> None:
    words = [m.get("content", "") for m in messages if m["role"] == "assistant"]
    # Conservative fixed-script gate: unseen wording needs manual review, not a guessed pass.
    requests = {
        "please repeat one complete total dollar amount",
        "please repeat one complete total",
    }
    _require(
        any(text.strip().rstrip(".?!").lower() in requests for text in words),
        "clarification does not match a reviewed fixed-script request",
    )
    _require(
        not any(
            re.search(r"\b(?:agreed|accepted|reserved|booked)\b", text, re.I) for text in words
        ),
        "no agreement claim before clarification",
    )


def _amount_turns(messages: list[Data]) -> tuple[int, int]:
    users = [(i, m.get("content", "")) for i, m in enumerate(messages) if m["role"] == "user"]
    ambiguous = next(i for i, text in users if "1600 and 25" in text)
    clarified = next(
        i
        for i, text in users
        if i > ambiguous and re.search(r"1625|six hundred (?:and )?twenty.five", text, re.I)
    )
    return ambiguous, clarified


def _check_handoff(messages: list[Data], calls: list[Call]) -> None:
    close_at = next(i for i, name, _ in calls if name == "close_call")
    text = " ".join(word for i, word in _spoken(messages) if i > close_at)
    _require("LD90001" in text and bool(re.search(r"1,?625", text)), "speak approved load and rate")
    _require("senior rep" in text.lower() and "confirm" in text.lower(), "speak mocked rep handoff")


def _check_repeat(messages: list[Data], calls: list[Call]) -> None:
    negotiations = [(i, args) for i, name, args in calls if name == "negotiate"]
    rates = [args["rate"] for _, args in negotiations]
    _require(len(rates) >= 2 and set(rates) == {"2200"}, "repeat the same caller ask exactly")
    repeated_at = negotiations[1][0]
    text = " ".join(word for i, word in _spoken(messages) if i >= repeated_at)
    _require(
        bool(re.search(r"(?:remains|still|unchanged|same).*1,?775", text, re.I)),
        "name unchanged offer",
    )
    _require(
        not re.search(r"new offer|final offer|transferring", text, re.I),
        "no false offer or handoff",
    )


def main() -> None:
    report = json.loads(Path(sys.argv[1]).read_text())
    records = report["full_conversations"]
    _require(len(records) == 6, "require two runs of each of three full conversations")
    for kind in ("compound", "repeat", "refusal"):
        _require(sum(r["kind"] == kind for r in records) == 2, f"two {kind} runs required")
    failed = 0
    for record in records:
        label = f"{record['kind']} repetition {record['repetition']}"
        try:
            check_conversation(record)
        except (ValueError, StopIteration) as error:
            print(f"FAIL {label}: {error}")
            failed += 1
        else:
            print(f"PASS {label}")
    if failed:
        raise SystemExit(1)
    print("Six recorded text conversations pass deterministic argument, order and ending checks.")


if __name__ == "__main__":
    main()
