"""The replay check must reject the defects that model grades can miss. No workflow runs."""

import json
from collections.abc import Callable

import pytest

from tools.check_voice_tuning import END, Data, check_conversation


def call(name: str, **args: object) -> Data:
    return {
        "role": "assistant",
        "tool_calls": [{"function": {"name": name, "arguments": json.dumps(args)}}],
    }


def fixture(kind: str = "compound") -> Data:
    messages = [call("verify_carrier", mc="145678")]
    if kind != "refusal":
        messages += [
            call("verify_code"),
            call("find_loads"),
            {"role": "assistant", "content": "Pickup November 7 at 11:04 PM Central Time."},
        ]
    if kind == "compound":
        messages += [
            {"role": "user", "content": "1600 and 25"},
            {"role": "assistant", "content": "Please repeat one complete total."},
            {"role": "user", "content": "One thousand six hundred twenty-five dollars."},
            call("negotiate", load_id="LD90001", rate="1625"),
        ]
    if kind == "repeat":
        messages += [
            call("negotiate", rate="2200"),
            call("negotiate", rate="2200"),
            {"role": "assistant", "content": "Our offer remains $1,775."},
        ]
    final = "LD90001 at 1625; a senior rep will confirm. Thank you. Goodbye."
    messages += [
        call("close_call"),
        {"role": "assistant", "content": final if kind == "compound" else "Thank you. Goodbye."},
        call(END),
    ]
    return {"kind": kind, "messages": messages}


def wrong_rate(record: Data) -> None:
    record["messages"][7] = call("negotiate", load_id="LD90001", rate="1600")


def early_rate(record: Data) -> None:
    message = record["messages"].pop(7)
    record["messages"].insert(6, message)


def no_clarification(record: Data) -> None:
    record["messages"].pop(5)


def wrong_load(record: Data) -> None:
    record["messages"][7] = call("negotiate", load_id="LD90002", rate="1625")


def no_close(record: Data) -> None:
    record["messages"].pop(-3)


def duplicate_close(record: Data) -> None:
    record["messages"].insert(-3, call("close_call"))


def no_goodbye(record: Data) -> None:
    record["messages"][-2]["content"] = ""


def reopening(record: Data) -> None:
    record["messages"].insert(-1, {"role": "assistant", "content": "Is there anything else?"})


def no_ending(record: Data) -> None:
    record["messages"].pop()


def wrong_time(record: Data) -> None:
    record["messages"][3]["content"] = "Pickup November 8 at 05:04 AM Central Time."


def false_counter(record: Data) -> None:
    reply = next(m for m in record["messages"] if "remains" in m.get("content", ""))
    reply["content"] = "Our new offer is $1,775."


def refusal_bypass(record: Data) -> None:
    record["messages"].insert(1, call("send_code"))


def unfinished(record: Data) -> None:
    record["status"] = "in-progress"


def idle_timeout(record: Data) -> None:
    record["close_reason"] = "idle_timeout"


def no_handoff(record: Data) -> None:
    record["messages"][-2]["content"] = "Thank you. Goodbye."


def false_clarification(record: Data) -> None:
    record["messages"][5]["content"] = "I have agreed to 1600 dollars and reserved the load."


def claim_then_clarify(record: Data) -> None:
    record["messages"][5]["content"] = "Agreed at 1600. Please repeat one complete total."


def early_handoff(record: Data) -> None:
    record["messages"][3]["content"] += " LD90001 at 1625; a senior rep will confirm."
    record["messages"][-2]["content"] = "Thank you. Goodbye."


def caller_after_goodbye(record: Data) -> None:
    record["messages"].insert(-1, {"role": "user", "content": "Thanks, goodbye."})


def two_goodbyes(record: Data) -> None:
    caller_after_goodbye(record)
    record["messages"].insert(-1, {"role": "assistant", "content": "Goodbye."})


def asserted_total_is_not_a_question(record: Data) -> None:
    record["messages"][5]["content"] = "That total is fine. I will get this sent to the rep."


def closed_before_negotiation(record: Data) -> None:
    close = record["messages"].pop(-3)
    record["messages"].insert(1, close)


@pytest.mark.parametrize("kind", ["compound", "repeat", "refusal"])
def test_scripted_positive_traces_pass(kind: str) -> None:
    check_conversation(fixture(kind))


def test_a_changed_first_counter_can_be_called_new_before_an_unchanged_repeat() -> None:
    record = fixture("repeat")
    record["messages"].insert(5, {"role": "assistant", "content": "Our new offer is $1,775."})
    check_conversation(record)


@pytest.mark.parametrize(
    ("kind", "damage"),
    [
        ("compound", change)
        for change in (
            wrong_rate,
            early_rate,
            no_clarification,
            wrong_load,
            no_close,
            duplicate_close,
            no_goodbye,
            reopening,
            no_ending,
            wrong_time,
            unfinished,
            idle_timeout,
            no_handoff,
            false_clarification,
            claim_then_clarify,
            early_handoff,
            caller_after_goodbye,
            two_goodbyes,
            asserted_total_is_not_a_question,
            closed_before_negotiation,
        )
    ]
    + [("repeat", false_counter), ("refusal", refusal_bypass)],
)
def test_incorrect_traces_fail_even_if_a_model_would_grade_them_passed(
    kind: str, damage: Callable[[Data], None]
) -> None:
    record = fixture(kind)
    damage(record)
    with pytest.raises(ValueError):
        check_conversation(record)
