"""
Lightweight tests for game-creation-agent tools.
No API keys, network calls, or browsers required.
"""
import base64
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make tools importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# pdf_tool
# ---------------------------------------------------------------------------
class TestPdfTool(unittest.TestCase):
    def test_import(self):
        from tools.pdf_tool import pdf_to_text
        self.assertTrue(callable(pdf_to_text))

    def test_missing_file_raises(self):
        from tools.pdf_tool import pdf_to_text
        with self.assertRaises(Exception):
            pdf_to_text("/nonexistent/file.pdf")

    def test_page_range_parse(self):
        """_parse_pages helper returns correct zero-based index sets."""
        from tools import pdf_tool
        if not hasattr(pdf_tool, "_parse_pages"):
            self.skipTest("_parse_pages not exposed")
        pages = pdf_tool._parse_pages("1-3")
        self.assertEqual(pages, {0, 1, 2})
        self.assertEqual(pdf_tool._parse_pages("2"), {1})


# ---------------------------------------------------------------------------
# research_all_games.discover_games
# ---------------------------------------------------------------------------
class TestDiscoverGames(unittest.TestCase):
    def _make_project(self, root, slug, name, add_pdf=False):
        game_dir = os.path.join(root, slug)
        res_dir = os.path.join(game_dir, "resources")
        os.makedirs(res_dir, exist_ok=True)
        with open(os.path.join(res_dir, "name.txt"), "w") as f:
            f.write(name)
        if add_pdf:
            open(os.path.join(res_dir, "rules.pdf"), "w").close()
        return game_dir

    def test_discovers_games_with_name_txt(self):
        from tools.research_all_games import discover_games
        with tempfile.TemporaryDirectory() as root:
            self._make_project(root, "alpha-game", "Alpha")
            self._make_project(root, "beta-game", "Beta", add_pdf=True)
            # This one has no name.txt — should be ignored
            os.makedirs(os.path.join(root, "no-name-game", "resources"), exist_ok=True)

            games = discover_games(root)
            slugs = {g["slug"] for g in games}
            self.assertIn("alpha-game", slugs)
            self.assertIn("beta-game", slugs)
            self.assertNotIn("no-name-game", slugs)

    def test_pdf_attached_when_present(self):
        from tools.research_all_games import discover_games
        with tempfile.TemporaryDirectory() as root:
            self._make_project(root, "with-pdf", "WithPDF", add_pdf=True)
            self._make_project(root, "no-pdf", "NoPDF", add_pdf=False)
            games = {g["slug"]: g for g in discover_games(root)}
            self.assertIsNotNone(games["with-pdf"]["pdf"])
            self.assertIsNone(games["no-pdf"]["pdf"])

    def test_name_matches_txt_content(self):
        from tools.research_all_games import discover_games
        with tempfile.TemporaryDirectory() as root:
            self._make_project(root, "my-game", "My Actual Game Name")
            games = discover_games(root)
            # discover_games returns slug/dir/pdf — name is read at call site in __main__
            # Just verify the name.txt is accessible
            game = games[0]
            name = open(game["name_file"]).read().strip()
            self.assertEqual(name, "My Actual Game Name")


# ---------------------------------------------------------------------------
# scaffold_game
# ---------------------------------------------------------------------------
class TestScaffoldGame(unittest.TestCase):
    def test_creates_expected_files(self):
        from tools.scaffold_game import scaffold_game
        with tempfile.TemporaryDirectory() as game_dir:
            # Patch npm install to avoid running it
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                scaffold_game("test-game", game_dir)

            expected = [
                "package.json",
                "public/index.html",
                ".gitignore",
                "src/index.js",
                "src/index.css",
                "src/App.js",
                "src/App.css",
                "src/Game.js",
                "src/AI/ai.js",
            ]
            for rel in expected:
                self.assertTrue(
                    os.path.exists(os.path.join(game_dir, rel)),
                    f"Missing: {rel}",
                )

    def test_package_json_name(self):
        from tools.scaffold_game import scaffold_game
        with tempfile.TemporaryDirectory() as game_dir:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                scaffold_game("my-cool-game", game_dir)

            pkg = json.loads(open(os.path.join(game_dir, "package.json")).read())
            self.assertEqual(pkg["name"], "my-cool-game")

    def test_skips_existing_files(self):
        from tools.scaffold_game import scaffold_game
        with tempfile.TemporaryDirectory() as game_dir:
            # Pre-create App.js with custom content
            src_dir = os.path.join(game_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            with open(os.path.join(src_dir, "App.js"), "w") as f:
                f.write("// my custom content")

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                scaffold_game("test-game", game_dir)

            # Custom content should be preserved
            content = open(os.path.join(src_dir, "App.js")).read()
            self.assertEqual(content, "// my custom content")

    def test_npm_install_called(self):
        from tools.scaffold_game import scaffold_game
        with tempfile.TemporaryDirectory() as game_dir:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                scaffold_game("test-game", game_dir)
            # npm install should have been invoked
            calls = [str(c) for c in mock_run.call_args_list]
            self.assertTrue(any("npm" in c or "install" in c for c in calls))


# ---------------------------------------------------------------------------
# generate_game_plan (prompt construction only — no API call)
# ---------------------------------------------------------------------------
class TestGenerateGamePlan(unittest.TestCase):
    def test_load_text_truncates(self):
        from tools.generate_game_plan import load_text
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * 1000)
            name = f.name
        try:
            result = load_text(name, max_chars=100)
            self.assertEqual(len(result), 100)
        finally:
            os.unlink(name)

    def test_prompt_contains_game_name(self):
        """PROMPT template substitutes game_name correctly."""
        from tools.generate_game_plan import PROMPT
        filled = PROMPT.format(game_name="TestGame", generic_plan="PLAN", rules_text="RULES")
        self.assertIn("TestGame", filled)
        self.assertIn("PLAN", filled)
        self.assertIn("RULES", filled)

    def test_generate_calls_api(self):
        from tools.generate_game_plan import generate_game_plan
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Generated plan content")]
        )
        with patch("anthropic.Anthropic", return_value=mock_client):
            with tempfile.TemporaryDirectory() as d:
                out = os.path.join(d, "plan.md")
                result = generate_game_plan("TestGame", "Some rules text", out)
                self.assertIn("TestGame", result)
                self.assertTrue(os.path.exists(out))


# ---------------------------------------------------------------------------
# youtube_pipeline helpers (no network/whisper/API)
# ---------------------------------------------------------------------------
class TestYoutubePipelineHelpers(unittest.TestCase):
    def test_transcript_window(self):
        from tools.youtube_pipeline import transcript_window
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello"},
            {"start": 10.0, "end": 15.0, "text": "world"},
            {"start": 35.0, "end": 40.0, "text": "outside"},
        ]
        result = transcript_window(segments, start=0.0, duration=30)
        self.assertIn("Hello", result)
        self.assertIn("world", result)
        self.assertNotIn("outside", result)

    def test_transcript_window_empty(self):
        from tools.youtube_pipeline import transcript_window
        result = transcript_window([], start=0.0)
        self.assertEqual(result, "")

    def test_full_transcript(self):
        from tools.youtube_pipeline import full_transcript
        segments = [
            {"start": 0, "end": 5, "text": " A"},
            {"start": 5, "end": 10, "text": " B"},
        ]
        self.assertIn("A", full_transcript(segments))
        self.assertIn("B", full_transcript(segments))

    def test_encode_image_roundtrip(self):
        from tools.youtube_pipeline import encode_image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0test")  # minimal JPEG-like bytes
            name = f.name
        try:
            b64 = encode_image(name)
            decoded = base64.standard_b64decode(b64)
            self.assertTrue(decoded.startswith(b"\xff\xd8"))
        finally:
            os.unlink(name)


if __name__ == "__main__":
    unittest.main()
