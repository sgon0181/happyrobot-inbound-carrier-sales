# Shared project context

@AGENTS.md

Start with `README.md`, then `ARCHITECTURE.md` and `docs/decisions.md`. `docs/onboarding.md` covers access, current state and reading order. TMS usage is in `docs/tms/README.md`; sanitized experiment evidence, reply fixtures and blocked/protected inventory are linked from `docs/tms-contract.md`.

Keep credentials in the configured secret store or ignored local `.env`; never copy values into documentation, prompts or commits. A coding agent's internal TMS reference is not a runtime voice-agent prompt.
