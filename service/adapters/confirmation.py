"""Conservative booking consent from platform-owned dialogue, never tool arguments."""

import asyncio
import re
from datetime import datetime


def dialogue_turns(messages):
    turns = []
    for message in messages:
        role = message.get("role")
        text = message.get("content")
        if role not in ("user", "assistant") or not isinstance(text, str) or not text.strip():
            continue
        if text.startswith("<Thoughts>") or message.get("is_filler"):
            continue
        if turns and turns[-1]["role"] == role:
            turns[-1]["text"] += " " + text
            turns[-1]["id"] = message["id"]
            turns[-1]["ids"].append(message["id"])
            turns[-1]["interrupted"] |= bool(message.get("is_interrupted"))
        else:
            turns.append(
                {
                    "role": role,
                    "text": text,
                    "id": message["id"],
                    "ids": [message["id"]],
                    "interrupted": bool(message.get("is_interrupted")),
                }
            )
    return turns


def consent_evidence(messages, rate, anchor=None, load_id=None):
    turns = dialogue_turns(messages)
    acknowledgement = None
    # Native neutral speech is sometimes missing its filler flag. Keep the
    # original consent evidence and retain every ignored message ID for audit.
    if (
        len(turns) >= 3
        and turns[-1]["role"] == "assistant"
        and not turns[-1]["interrupted"]
        and turns[-2]["role"] == "user"
        and re.fullmatch(
            r"(?:one moment|just a moment|let me check|let me see)[.!]*",
            turns[-1]["text"].strip(),
            re.I,
        )
    ):
        acknowledgement = list(turns[-1]["ids"])
        turns = turns[:-1]
    users = [turn for turn in turns if turn["role"] == "user"]
    latest = users[-1]["id"] if users else None
    result = {"anchor": latest, "approved": False}
    if not anchor or latest == anchor or len(turns) < 2:
        return result
    user, question = turns[-1], turns[-2]
    anchor_positions = [
        i for i, turn in enumerate(turns) if anchor in turn["ids"] and turn["role"] == "user"
    ]
    if not anchor_positions or anchor_positions[-1] >= len(turns) - 2:
        return result
    if (
        user["role"] != "user"
        or user["interrupted"]
        or question["role"] != "assistant"
        or question["interrupted"]
    ):
        return result
    # Reject contradictory or conditional answers before removing punctuation.
    original = user["text"].lower().replace("\u2019", "'")
    if re.search(r"[\d$?]", original):
        return result
    if re.search(r"\b(?:no|not|don't|wait|hold|but|if|only|actually|maybe)\b", original):
        return result
    answer = " ".join(re.sub(r"[.,!]", " ", original).split())
    if len(answer.split()) > 8:
        return result
    affirmative = (
        r"(?:yes|yeah|yep|yup|sure|correct|that's right|go ahead|"
        r"book it|sounds good|that works|okay)"
    )
    polite = (
        r"(?:please|thanks|thank you|perfect|that's fine|sir|ma'am|"
        r"do|go ahead|book it|and book it)"
    )
    if not re.fullmatch(affirmative + r"(?:\s+" + polite + r")*", answer):
        return result
    amounts = "(?:" + re.escape(str(rate)) + "|" + re.escape(format(rate, ",")) + ")"
    expected = (
        r"May\s+I\s+book\s+load\s+"
        + re.escape(load_id or "")
        + r"\s+at\s+\$"
        + amounts
        + r"\s+total\?"
    )
    if load_id and re.search(r"\b" + expected + r"\s*\Z", question["text"], re.I):
        result["approved"] = True
        result["question_id"] = question["id"]
        result["answer_id"] = user["id"]
        if acknowledgement is not None:
            result["ignored_acknowledgement_ids"] = acknowledgement
    return result


class NativeConfirmation:
    def __init__(self, platform, workflow_id):
        self.platform, self.workflow_id = platform, workflow_id

    async def __call__(self, cid, load_id, rate, anchor):
        run = await asyncio.to_thread(self.platform.request, "/runs/" + cid)
        if run.get("workflow_id") != self.workflow_id:
            raise ValueError("Unexpected workflow")
        sessions = await asyncio.to_thread(self.platform.request, "/runs/" + cid + "/sessions")
        messages = []
        for session in sessions.get("data", []):
            cursor = None
            page = 1
            for _ in range(20):
                suffix = ("?cursor=" + cursor) if cursor else ("?page=" + str(page))
                path = "/sessions/" + session["id"] + "/messages" + suffix
                response = await asyncio.to_thread(self.platform.request, path)
                rows = response.get("data")
                if not isinstance(rows, list):
                    raise ValueError("Missing dialogue page")
                if any(m.get("session_id") != session["id"] for m in rows):
                    raise ValueError("Unexpected dialogue session")
                messages.extend(rows)
                cursor = response.get("next_cursor") or (response.get("pagination") or {}).get(
                    "next_cursor"
                )
                pagination = response.get("pagination") or {}
                if not cursor and not pagination.get("has_next_page"):
                    break
                page += 1
            else:
                raise ValueError("Incomplete dialogue")

        def timestamp(message):
            value = message["timestamp"]
            try:
                return float(value)
            except (TypeError, ValueError):
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()

        messages.sort(key=timestamp)
        users = [m for m in messages if m.get("role") == "user"]
        if not users:
            return {"anchor": None, "approved": False}
        session_id = users[-1]["session_id"]
        current = [m for m in messages if m["session_id"] == session_id]
        result = consent_evidence(current, rate, anchor, load_id)
        result["session_id"] = session_id
        return result
