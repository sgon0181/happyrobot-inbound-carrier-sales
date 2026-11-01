"""Redact code attempts while retaining contextual carrier identity."""

import json
import re

DIGIT_WORDS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}
WORD = r"(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)"
MC_LABEL = r"\b(?:mc|motor\s*carrier)(?:\s*(?:number|is|was|again|digits|:|#|,))*\s*$"


def tool_names(message):
    return [
        t.get("name") or (t.get("function") or {}).get("name")
        for t in message.get("tool_calls") or []
    ]


def joined_turns(messages):
    joined = []
    for message in messages:
        text = message.get("content")
        if isinstance(text, str) and text.startswith("<Thoughts>"):
            continue
        if (
            joined
            and message.get("role") in {"user", "assistant"}
            and joined[-1].get("role") == message.get("role")
            and joined[-1].get("session_id") == message.get("session_id")
            and isinstance(text, str)
            and isinstance(joined[-1].get("content"), str)
        ):
            joined[-1]["content"] += " " + text
            joined[-1]["tool_calls"] = (joined[-1].get("tool_calls") or []) + (
                message.get("tool_calls") or []
            )
        else:
            joined.append(dict(message))
    return joined


def redact_transcript(messages, mc=None):
    joined = joined_turns(messages)
    submitted, tools, lines, context = [], [], [], {}
    mc = str(mc) if mc is not None else None
    for message in joined:
        for tool in message.get("tool_calls") or []:
            function = tool.get("function") or {}
            if (tool.get("name") or function.get("name")) != "verify_code":
                continue
            arguments = tool.get("arguments", function.get("arguments", tool.get("args", {})))
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except ValueError:
                    continue
            code = arguments.get("code") if isinstance(arguments, dict) else None
            if isinstance(code, (str, int)) and re.fullmatch(r"[0-9]{6}", str(code)):
                submitted.append(str(code))
    for index, message in enumerate(joined):
        names = tool_names(message)
        tools.extend(name for name in names if name)
        session = message.get("session_id")
        raw = message.get("content")
        raw = raw if isinstance(raw, str) else ""
        text = raw
        next_message = joined[index + 1] if index + 1 < len(joined) else {}
        next_code = next_message.get("session_id") == session and "verify_code" in tool_names(
            next_message
        )
        code_context = context.get(session) == "code" or next_code
        protected = {}
        if mc:
            numeric = r"(?<!\d)" + r"[\s,.-]*".join(mc) + r"(?!\d)"
            spoken = r"\b" + WORD + rf"(?:[\s,-]+{WORD}){{{len(mc) - 1}}}\b"
            mixed = bool(re.search(r"\bmc\b", text, re.I) and re.search(r"\bcode\b", text, re.I))

            def protect(match):
                candidate = match.group()
                words = re.findall(WORD, candidate.lower())
                value = (
                    "".join(DIGIT_WORDS[w] for w in words)
                    if words
                    else re.sub(r"\D", "", candidate)
                )
                prefix = text[: match.start()]
                labelled = bool(re.search(MC_LABEL, prefix[-70:], re.I))
                code_before = bool(re.search(r"\bcode\b", prefix, re.I))
                allowed = (labelled and not code_before and (not code_context or mixed)) or (
                    context.get(session) == "mc" and not code_context and not code_before
                )
                if value == mc and allowed:
                    token = "CARRIERIDENTITY" + "X" * (len(protected) + 1)
                    protected[token] = candidate
                    return token
                return candidate

            text = re.sub(numeric + "|" + spoken, protect, text, flags=re.I)
        for code in submitted:
            text = re.sub(r"(?<!\d)" + r"[\s,.-]*".join(code) + r"(?!\d)", "[code redacted]", text)
        text = re.sub(r"\b[0-9]{6}\b", "[code redacted]", text)
        text = re.sub(
            r"\b" + WORD + rf"(?:[\s,-]+{WORD}){{5}}\b", "[spoken code redacted]", text, flags=re.I
        )
        text = re.sub(r"(?<!\d)(?:\d[ ,.-]){5}\d(?!\d)", "[code redacted]", text)
        if message.get("role") == "user" and code_context:
            text = re.sub(r"\b[0-9]{1,8}\b", "[code redacted]", text)
            text = re.sub(
                r"\b" + WORD + rf"(?:[\s,-]+{WORD})*\b", "[spoken code redacted]", text, flags=re.I
            )
        for token, identity in sorted(protected.items(), key=lambda x: -len(x[0])):
            text = text.replace(token, identity)
        if message.get("role") in {"user", "assistant"} and text:
            lines.append(message["role"] + ": " + text)
        if message.get("role") == "assistant":
            if "send_code" in names or (
                re.search(r"\bcode\b", raw or "", re.I)
                and re.search(r"\?|read|tell|check|enter", raw or "", re.I)
            ):
                context[session] = "code"
            elif re.search(r"\bmc\b", raw or "", re.I) and re.search(
                r"\?|give|tell", raw or "", re.I
            ):
                context[session] = "mc"
            elif re.search(r"\blane|equipment|load|offer|rate|verified\b", raw or "", re.I):
                context[session] = None
    return "\n".join(lines), tools
