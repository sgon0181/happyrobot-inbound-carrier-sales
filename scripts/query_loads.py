"""Read loads from the TMS. Read-only, and no extra packages needed.

  python3 scripts/query_loads.py                    up to 3 dry-van summaries
  python3 scripts/query_loads.py --limit 20         up to 20 dry-van summaries
  python3 scripts/query_loads.py --load-id LD01023  one full record, with MAX_BUY
"""

from pathlib import Path
import argparse
import re
import socket
import sys
import time

DEFAULT_LIMIT = 3
ATTEMPTS = 3
TIMEOUT_SECONDS = 5


def load_id(value):
    if not re.fullmatch(r"[A-Za-z0-9]{1,32}", value):
        raise argparse.ArgumentTypeError("use a letters-and-digits load ID, such as LD01023")
    return value


def limit(value):
    if not re.fullmatch(r"[0-9]{1,4}", value) or not 1 <= int(value) <= 1000:
        raise argparse.ArgumentTypeError("use a whole number from 1 to 1000")
    return int(value)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--load-id", type=load_id, help="fetch one full record with LOAD_GET")
    target.add_argument("--limit", type=limit, help="dry-van summaries to request with LOAD_QUERY")
    return parser.parse_args(argv)


def build_request(args, token):
    # Both commands only read. Neither can book a load.
    if args.load_id:
        return f"CMD:LOAD_GET|AUTH:{token}|LOAD_ID:{args.load_id}\r\n"
    return (
        f"CMD:LOAD_QUERY|AUTH:{token}"
        f"|EQTYPE:DRY_VAN|MAX_RESULTS:{args.limit or DEFAULT_LIMIT}\r\n"
    )


def send(config, request):
    with socket.create_connection(
        (config["TMS_HOST"], int(config["TMS_PORT"])), timeout=TIMEOUT_SECONDS
    ) as connection:
        connection.settimeout(TIMEOUT_SECONDS)
        connection.sendall(request.encode("ascii"))
        response = bytearray()
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
            if len(response) > 1_048_576:
                raise ValueError("TMS response exceeded the size limit.")
            lines = bytes(response).split(b"\r\n")
            if b"END" in lines[:-1] or (
                lines[0].startswith(b"ERR|") and len(lines) > 1
            ):
                break
    return response.decode("ascii")


def is_complete(reply):
    # The TMS does not signal its faults, so check the framing here. Success
    # must finish with a whole line equal to END, not one that merely ends in it.
    *lines, tail = reply.split("\r\n")
    if not lines or tail:
        return False
    if reply.startswith("ERR|"):
        return len(lines) == 1 and all(":" in field for field in lines[0].split("|")[1:])
    if lines.pop() != "END":
        return False
    return all(":" in field for line in lines for field in line.split("|"))


def main():
    # Reject bad arguments before reading credentials or opening a connection.
    args = parse_args()

    # Load credentials from the project's .env file, regardless of where we run.
    env_path = Path(__file__).resolve().parents[1] / ".env"
    config = {}
    for line in env_path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip("\"").strip("'")

    for key in ("TMS_HOST", "TMS_PORT", "TMS_TOKEN"):
        if not config.get(key):
            raise ValueError(f"Fill in {key} in your .env file first.")

    token = config["TMS_TOKEN"]
    if any(char in token for char in "|\r\n"):
        raise ValueError("TMS_TOKEN contains an invalid separator.")

    request = build_request(args, token)
    print("SENDING:", request.replace(token, "[TOKEN HIDDEN]").strip(), flush=True)

    # Safe to retry, because neither command changes anything.
    for attempt in range(1, ATTEMPTS + 1):
        try:
            reply = send(config, request)
            problem = None if is_complete(reply) else "incomplete or malformed reply"
        except (OSError, UnicodeError) as error:
            problem = type(error).__name__
        if not problem:
            break
        print(f"Attempt {attempt} of {ATTEMPTS} failed: {problem}.", file=sys.stderr)
        if attempt < ATTEMPTS:
            time.sleep(0.3)
    else:
        return 1

    print("\nTMS RESPONSE:", flush=True)
    print(reply.replace(token, "[TOKEN HIDDEN]"), end="")
    return 1 if reply.startswith("ERR|") else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        # Avoid printing connection details or credentials in error messages.
        print(f"Query failed ({type(error).__name__}). Check .env and retry.", file=sys.stderr)
        sys.exit(1)
