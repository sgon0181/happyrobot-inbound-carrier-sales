// Defense in depth for free text written during a call: mask anything that looks like
// a code, a pricing figure or a token, even though the service never stores one.
export function redactText(text: string, max = 2_000): string {
  return text
    .slice(0, max)
    .replace(/[A-Za-z0-9_-]{40,}/g, "[redacted]")
    .replace(
      /\b(otp|one[- ]time|code|passcode|pin|verification|token|password|secret)\b([^\n]{0,40}?)(\d(?:[\s-]?\d){3,7})/gi,
      "$1$2[redacted]"
    )
    .replace(
      /\b(ceiling|cap|max(?:imum)? rate|max buy|target rate|policy)\b([^\n\d$]{0,20})\$?\s?\d[\d,.]*/gi,
      "$1$2[redacted]"
    );
}

