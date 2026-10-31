"""Offline checks for TMS reply framing. Never contacts the real TMS.

  python3 scripts/test_query_loads.py
"""

from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

from query_loads import is_complete

GOOD_RECORD = "LOAD_ID:LD01023|RATE:2709|MAX_BUY:2922\r\nEND\r\n"
# Passes a plain endswith("END\r\n") test, but no END line was ever sent.
CUT_OFF_RECORD = "LOAD_ID:LD01023|NOTES:WEEKEND\r\n"


class FramingTests(unittest.TestCase):
    def test_accepts_complete_replies(self):
        for reply in (
            GOOD_RECORD,
            "END\r\n",
            "LOAD_ID:LD1|STATUS:OPEN\r\nLOAD_ID:LD2|STATUS:OPEN\r\nEND\r\n",
            "LOAD_ID:LD1|NOTES:WEEKEND\r\nEND\r\n",
            "ERR|CODE:NOT_FOUND|MSG:Load not found\r\n",
        ):
            with self.subTest(reply=reply):
                self.assertTrue(is_complete(reply))

    def test_rejects_replies_without_an_exact_end_line(self):
        for reply in (
            "",
            CUT_OFF_RECORD,
            "NOTES:END\r\n",
            "LOAD_ID:LD1\r\nNOTES:LEGEND\r\n",
            "LOAD_ID:LD1|RATE:27",
            "LOAD_ID:LD1\r\nEND",
            "LOAD_ID:LD1\r\nEND\r",
            "LOAD_ID:LD1\r\nEND\n",
            "LOAD_ID:LD1\nEND\r\n",
            "LOAD_ID:LD1\r\nEND  \r\n",
            "LOAD_ID:LD1\r\nend\r\n",
        ):
            with self.subTest(reply=reply):
                self.assertFalse(is_complete(reply))

    def test_rejects_anything_around_the_end_line(self):
        for reply in (
            "END\r\nEND\r\n",
            "END\r\nLOAD_ID:LD1\r\n",
            "END\r\nextra",
            "LOAD_ID:LD1\r\n\r\nEND\r\n",
        ):
            with self.subTest(reply=reply):
                self.assertFalse(is_complete(reply))

    def test_rejects_malformed_records(self):
        self.assertFalse(is_complete("LOAD_ID:LD1||RATE:2709\r\nEND\r\n"))

    def test_error_reply_is_exactly_one_terminated_line(self):
        for reply in (
            "ERR|CODE:NOT_FOUND",
            "ERR|CODE:NOT_FOUND\r",
            "ERR|\r\n",
            "ERR|CODE:X|MSG:y\r\nEND\r\n",
        ):
            with self.subTest(reply=reply):
                self.assertFalse(is_complete(reply))


class RetryTests(unittest.TestCase):
    def run_against(self, replies):
        """Run the script against a fake TMS that closes after each reply."""
        server = socket.create_server(("127.0.0.1", 0))
        requests = []

        def serve():
            for reply in replies:
                connection, _ = server.accept()
                with connection:
                    requests.append(connection.recv(4096))
                    connection.sendall(reply.encode("ascii"))

        threading.Thread(target=serve, daemon=True).start()
        with server, tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scripts").mkdir()
            script = shutil.copy(Path(__file__).with_name("query_loads.py"), root / "scripts")
            (root / ".env").write_text(
                f"TMS_HOST=127.0.0.1\nTMS_PORT={server.getsockname()[1]}\nTMS_TOKEN=fake-token\n"
            )
            done = subprocess.run(
                [sys.executable, str(script), "--load-id", "LD01023"],
                capture_output=True, text=True, timeout=30,
            )
        return done, len(requests)

    def test_cut_off_record_is_retried(self):
        done, attempts = self.run_against([CUT_OFF_RECORD, GOOD_RECORD])
        self.assertEqual((done.returncode, attempts), (0, 2))
        self.assertIn("MAX_BUY:2922", done.stdout)
        self.assertNotIn("WEEKEND", done.stdout)

    def test_cut_off_records_are_never_shown_as_a_result(self):
        done, attempts = self.run_against([CUT_OFF_RECORD] * 3)
        self.assertEqual((done.returncode, attempts), (1, 3))
        self.assertNotIn("TMS RESPONSE", done.stdout)


if __name__ == "__main__":
    unittest.main()
