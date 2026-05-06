import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from llm.groq_client import GroqClient


class GroqClientTests(unittest.TestCase):
    def test_generate_response_raises_when_api_key_missing(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True), patch("llm.groq_client.Groq"):
            client = GroqClient()
            with self.assertRaises(RuntimeError):
                client.generate_response("sys", "user")

    def test_generate_response_uses_json_mode_by_default(self):
        fake_create = MagicMock(
            return_value=SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
            )
        )
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True), patch(
            "llm.groq_client.Groq", return_value=fake_client
        ):
            client = GroqClient()
            out = client.generate_response("sys", "user")

        self.assertEqual(out, '{"ok": true}')
        kwargs = fake_create.call_args.kwargs
        self.assertIn("response_format", kwargs)
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})

    def test_generate_response_raises_on_empty_content(self):
        fake_create = MagicMock(
            return_value=SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=""))]
            )
        )
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True), patch(
            "llm.groq_client.Groq", return_value=fake_client
        ):
            client = GroqClient()
            with self.assertRaises(RuntimeError):
                client.generate_response("sys", "user")

    def test_generate_response_raises_on_provider_error(self):
        fake_create = MagicMock(side_effect=Exception("provider_down"))
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True), patch(
            "llm.groq_client.Groq", return_value=fake_client
        ):
            client = GroqClient()
            with self.assertRaises(RuntimeError):
                client.generate_response("sys", "user")


if __name__ == "__main__":
    unittest.main()
