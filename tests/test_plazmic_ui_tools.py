from __future__ import annotations

import http.client
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


apply_improvements = load_module("apply_improvements", ROOT / "ui-tools" / "apply-improvements.py")
lint_ui = load_module("lint_ui", ROOT / "ui-tools" / "lint-ui.py")
format_xml = load_module("format_xml_tests", ROOT / "ui-tools" / "format_xml.py")
ui_studio = load_module("ui_studio_tests", ROOT / "ui-tools" / "ui_studio.py")


ADVANCED_LOOT_FIXTURE = """\
<?xml version="1.0" encoding="us-ascii"?>
<XML ID="EQInterfaceDefinitionLanguage">
\t<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />

\t<!-- Templates for dynamic loot list -->
\t<Listbox item="ADLW_LootList">
\t\t<Tooltip>Store item(s) on corpse(s) to either tradeskill depo or item hoard</Tooltip>
\t</Listbox>
\t<Screen item="ADLW_LootListScreen">
\t\t<ResizeLast>true</ResizeLast>
\t\t<Style_Border>true</Style_Border>
\t\t<Style_VScroll>false</Style_VScroll>
\t\t<Style_Transparent>true</Style_Transparent>
\t\t<Style_Border>true</Style_Border>
\t\t<Style_Titlebar>false</Style_Titlebar>
\t</Screen>
\t<Screen item="ADLW_CheckboxesScreen">
\t\t<DrawTemplate>WDT_Inner</DrawTemplate>
\t\t<AutoStretch>true</AutoStretch>
\t\t<DrawTemplate>WDT_Inner</DrawTemplate>
\t\t<Style_Border>true</Style_Border>
\t\t<Style_HScroll>false</Style_HScroll>
\t\t<Style_VScroll>false</Style_VScroll>
\t\t<Style_Transparent>true</Style_Transparent>
\t\t<Style_Border>true</Style_Border>
\t\t<Style_Titlebar>false</Style_Titlebar>
\t</Screen>
\t<Screen item="AdvancedLootWnd">
\t\t<Size>
\t\t\t<CX>450</CX>
\t\t\t<CY>450</CY>
\t\t</Size>
\t</Screen>
</XML>
"""


class ApplyImprovementsTests(unittest.TestCase):
    def test_advanced_loot_cleanup_is_deterministic(self) -> None:
        improved = apply_improvements.improve_advanced_loot(ADVANCED_LOOT_FIXTURE)

        self.assertIn("<CX>800</CX>", improved)
        self.assertIn("<CY>600</CY>", improved)
        self.assertIn("tradeskill depot or item hoard", improved)
        self.assertEqual(improved.count("<Style_Border>true</Style_Border>"), 2)
        self.assertEqual(improved.count("<DrawTemplate>WDT_Inner</DrawTemplate>"), 1)
        self.assertIn("Plazmic: locally derived", improved)

    def test_cleanup_refuses_unreviewed_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "depot tooltip correction"):
            apply_improvements.improve_advanced_loot("<XML />")


class LintTests(unittest.TestCase):
    def test_linter_accepts_minimal_improved_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ui_dir = Path(temp_dir)
            advanced = apply_improvements.improve_advanced_loot(ADVANCED_LOOT_FIXTURE)
            (ui_dir / "EQUI_AdvancedLootWnd.xml").write_text(advanced, encoding="us-ascii")
            (ui_dir / "EQUI.xml").write_text(
                """\
<?xml version="1.0"?>
<XML ID="EQInterfaceDefinitionLanguage">
  <Composite>
    <Include>EQUI_AdvancedLootWnd.xml</Include>
  </Composite>
</XML>
""",
                encoding="us-ascii",
            )

            findings, count = lint_ui.lint_directory(ui_dir, check_format=False)

            self.assertEqual(findings, [])
            self.assertEqual(count, 2)

    def test_linter_rejects_missing_include(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ui_dir = Path(temp_dir)
            (ui_dir / "EQUI.xml").write_text(
                """\
<?xml version="1.0"?>
<XML ID="EQInterfaceDefinitionLanguage">
  <Composite><Include>missing.xml</Include></Composite>
</XML>
""",
                encoding="us-ascii",
            )

            findings, _ = lint_ui.lint_directory(ui_dir, check_format=False)

            self.assertTrue(any("missing included file" in item.message for item in findings))

    def test_linter_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ui_dir = Path(temp_dir)
            advanced = apply_improvements.improve_advanced_loot(ADVANCED_LOOT_FIXTURE)
            (ui_dir / "EQUI_AdvancedLootWnd.xml").write_text(advanced, encoding="us-ascii")
            (ui_dir / "EQUI.xml").write_text(
                """\
<?xml version="1.0"?>
<XML ID="EQInterfaceDefinitionLanguage">
  <Composite><Include>EQUI_AdvancedLootWnd.xml</Include></Composite>
</XML>
""",
                encoding="us-ascii",
            )
            (ui_dir / "linked.tga").symlink_to(ui_dir / "missing.tga")

            findings, _ = lint_ui.lint_directory(ui_dir, check_format=False)

            self.assertTrue(any("symlinks are not allowed" in item.message for item in findings))


class FormatTests(unittest.TestCase):
    def test_formatter_is_idempotent_and_preserves_mixed_text(self) -> None:
        source = (
            '<?xml version="1.0"?>\r\n'
            "<XML>\r\n"
            "\t<Button>y\r\n"
            "\t\t<Text>Keep  internal spacing</Text>   \r\n"
            "\t</Button>\r\n"
            "</XML>\r\n"
        )

        formatted = format_xml.format_text(source)

        self.assertEqual(formatted, format_xml.format_text(formatted))
        self.assertIn("  <Button>y\n", formatted)
        self.assertIn("<Text>Keep  internal spacing</Text>", formatted)
        self.assertNotIn("\r", formatted)


class UiStudioTests(unittest.TestCase):
    def test_layout_update_preserves_newlines_and_unrelated_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout = root / "UI_plazmic_1440p.ini"
            layout.write_bytes(
                b"[Main]\r\nUISkin=plazmic-ui\r\n"
                b"[PlayerWindow]\r\nXRef=center\r\nXPos=-15.000000%\r\n"
                b"Alpha=255\r\nCustomSetting=keep-me\r\n"
            )

            backup = ui_studio.update_ini_section(
                layout,
                "PlayerWindow",
                {"XPos": "-12.500000%", "Alpha": "200", "Width": "336"},
                root / "backups",
            )

            contents = layout.read_bytes()
            self.assertIn(b"XPos=-12.500000%\r\n", contents)
            self.assertIn(b"Alpha=200\r\n", contents)
            self.assertIn(b"Width=336\r\n", contents)
            self.assertIn(b"CustomSetting=keep-me\r\n", contents)
            self.assertNotIn(b"\n", contents.replace(b"\r\n", b""))
            self.assertIsNotNone(backup)
            self.assertTrue(backup.is_file())

    def test_layout_update_rejects_duplicate_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout = root / "UI_example.ini"
            layout.write_bytes(b"[PlayerWindow]\r\nAlpha=255\r\n[PlayerWindow]\r\nAlpha=200\r\n")

            with self.assertRaisesRegex(ValueError, "must appear exactly once"):
                ui_studio.update_ini_section(
                    layout,
                    "PlayerWindow",
                    {"Alpha": "180"},
                    root / "backups",
                )

            self.assertEqual(
                layout.read_bytes(),
                b"[PlayerWindow]\r\nAlpha=255\r\n[PlayerWindow]\r\nAlpha=200\r\n",
            )

    def test_anchor_conversion_round_trips(self) -> None:
        for reference in ("left", "center", "right"):
            position = ui_studio.anchored_position(reference, 13.25, 336, 2560)
            percent = ui_studio.position_percent(reference, position, 336, 2560)
            self.assertAlmostEqual(percent, 13.25)

    def test_resolution_validation_and_state(self) -> None:
        self.assertEqual(ui_studio.parse_resolution(None), (2560, 1440))
        self.assertEqual(ui_studio.parse_resolution("1920x1080"), (1920, 1080))
        with self.assertRaisesRegex(ValueError, "WIDTHxHEIGHT"):
            ui_studio.parse_resolution("1920:1080")
        with self.assertRaisesRegex(ValueError, "between 640 and 8192"):
            ui_studio.parse_resolution("320x200")

    def test_settings_and_xml_validation_fail_closed(self) -> None:
        settings = ui_studio.validated_settings({"XPos": "12.5", "Alpha": "128", "Locked": "1"})
        self.assertEqual(settings["XPos"], "12.500000%")
        with self.assertRaisesRegex(ValueError, "Alpha"):
            ui_studio.validated_settings({"Alpha": "999"})
        with self.assertRaisesRegex(ValueError, "well formed"):
            ui_studio.validate_xml("<XML>")
        with self.assertRaisesRegex(ValueError, "root ID"):
            ui_studio.validate_xml("<XML />")

    def test_capture_and_publish_copy_private_files_with_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            game = root / "game"
            installed_skin = game / "uifiles" / "plazmic-ui"
            installed_skin.mkdir(parents=True)
            repo.mkdir()
            (game / "eqgame.exe").write_bytes(b"client")
            (installed_skin / "EQUI.xml").write_text(
                '<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii"
            )
            (installed_skin / "texture.tga").write_bytes(b"asset")
            (installed_skin / "texture.tga:crc").write_bytes(b"sidecar")
            source_layout = game / "UI_plazmic_1440p.ini"
            source_layout.write_bytes(b"[PlayerWindow]\r\nAlpha=255\r\n")

            skin, layout = ui_studio.capture_workspace(repo, game, source_layout)

            self.assertTrue((skin / "texture.tga").is_file())
            self.assertFalse((skin / "texture.tga:crc").exists())
            self.assertEqual(layout.read_bytes(), source_layout.read_bytes())
            self.assertIn(
                '"resolution": "2560x1440"',
                (repo / ui_studio.WORKSPACE_DIRECTORY / "studio.json").read_text(encoding="utf-8"),
            )

            ui_studio.update_ini_section(
                layout,
                "PlayerWindow",
                {"Alpha": "180"},
                repo / "ui-backups",
            )
            (skin / "texture.tga").write_bytes(b"edited")
            paths = ui_studio.StudioPaths(
                repo=repo,
                skin=skin,
                layouts=repo / "ui-layouts",
                backups=repo / "ui-backups",
                config=repo / ".plazmic-ui-studio.json",
                game=game,
                layout=layout,
            )

            result = ui_studio.publish_workspace(paths, source_layout.name)

            self.assertEqual((installed_skin / "texture.tga").read_bytes(), b"edited")
            self.assertIn(b"Alpha=180", source_layout.read_bytes())
            skin_backup = installed_skin.parent / result["skinBackup"]
            layout_backup = source_layout.parent / result["layoutBackup"]
            self.assertTrue(skin_backup.is_dir())
            self.assertTrue(layout_backup.is_file())
            self.assertNotIn(str(root), " ".join(result.values()))
            shutil.rmtree(skin_backup)

    def test_capture_rejects_skin_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            game = root / "game"
            skin = game / "uifiles" / "default_modern"
            skin.mkdir(parents=True)
            repo.mkdir()
            (game / "eqgame.exe").write_bytes(b"client")
            (skin / "EQUI.xml").write_text(
                '<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii"
            )
            (skin / "linked.tga").symlink_to(root / "outside.tga")
            layout = game / "UI_example.ini"
            layout.write_bytes(b"[PlayerWindow]\r\nAlpha=255\r\n")

            with self.assertRaisesRegex(ValueError, "contains a symlink"):
                ui_studio.capture_workspace(repo, game, layout)

    def test_xml_and_layout_selection_reject_symlinks_and_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            game = root / "game"
            skin = root / "skin"
            game.mkdir()
            skin.mkdir()
            layout = game / "UI_example.ini"
            layout.write_bytes(b"[Main]\n")
            (game / "UI_link.ini").symlink_to(layout)
            xml = skin / "EQUI.xml"
            xml.write_text('<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii")
            (skin / "linked.xml").symlink_to(xml)

            self.assertEqual(ui_studio.choose_layout(game, layout.name), layout)
            with self.assertRaisesRegex(ValueError, r"top-level UI_\*\.ini"):
                ui_studio.choose_layout(game, "nested/UI_example.ini")
            with self.assertRaisesRegex(ValueError, "symlinks are not editable"):
                ui_studio.safe_xml_path(skin, "linked.xml")

    def test_interactive_layout_selection_rejects_nonpositive_and_eof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            game = Path(temp_dir)
            for name in ("UI_a.ini", "UI_b.ini"):
                (game / name).write_bytes(b"[Main]\n")

            with (
                mock.patch.object(ui_studio.sys.stdin, "isatty", return_value=True),
                mock.patch("builtins.input", side_effect=["0", "1"]),
            ):
                self.assertEqual(ui_studio.choose_layout(game, None).name, "UI_a.ini")

            with (
                mock.patch.object(ui_studio.sys.stdin, "isatty", return_value=True),
                mock.patch("builtins.input", side_effect=EOFError),
                self.assertRaisesRegex(ValueError, "selection ended"),
            ):
                ui_studio.choose_layout(game, None)

    def test_publish_rolls_back_skin_when_layout_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            game = root / "game"
            installed_skin = game / "uifiles" / "plazmic-ui"
            workspace_skin = repo / "plazmic-ui"
            installed_skin.mkdir(parents=True)
            workspace_skin.mkdir(parents=True)
            (game / "eqgame.exe").write_bytes(b"client")
            for skin in (installed_skin, workspace_skin):
                (skin / "EQUI.xml").write_text(
                    '<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii"
                )
            (installed_skin / "texture.tga").write_bytes(b"original")
            (workspace_skin / "texture.tga").write_bytes(b"replacement")
            target_layout = game / "UI_example.ini"
            target_layout.write_bytes(b"[PlayerWindow]\r\nAlpha=255\r\n")
            local_layout = repo / "ui-layouts" / target_layout.name
            local_layout.parent.mkdir()
            local_layout.write_bytes(b"[PlayerWindow]\r\nAlpha=180\r\n")
            paths = ui_studio.StudioPaths(
                repo=repo,
                skin=workspace_skin,
                layouts=local_layout.parent,
                backups=repo / "ui-backups",
                config=repo / ".plazmic-ui-studio.json",
                game=game,
                layout=local_layout,
            )
            real_replace = os.replace

            def replace_with_layout_failure(source: object, target: object) -> None:
                if Path(target) == target_layout and Path(source).suffix == ".tmp":
                    raise OSError("synthetic layout failure")
                real_replace(source, target)

            with (
                mock.patch.object(
                    ui_studio.os,
                    "replace",
                    side_effect=replace_with_layout_failure,
                ),
                self.assertRaisesRegex(OSError, "synthetic layout failure"),
            ):
                ui_studio.publish_workspace(paths, target_layout.name)

            self.assertEqual((installed_skin / "texture.tga").read_bytes(), b"original")
            self.assertEqual(target_layout.read_bytes(), b"[PlayerWindow]\r\nAlpha=255\r\n")
            self.assertEqual(list(game.glob("UI_example.ini.backup-*")), [])

    def test_loopback_server_requires_host_token_and_allowed_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            game = root / "game"
            skin = repo / "plazmic-ui"
            layout = repo / "ui-layouts" / "UI_example.ini"
            skin.mkdir(parents=True)
            layout.parent.mkdir()
            game.mkdir()
            (game / "eqgame.exe").write_bytes(b"client")
            layout.write_bytes(b"[Main]\n")
            (game / layout.name).write_bytes(b"[Main]\n")
            (skin / "EQUI.xml").write_text(
                '<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii"
            )
            paths = ui_studio.StudioPaths(
                repo=repo,
                skin=skin,
                layouts=layout.parent,
                backups=repo / "ui-backups",
                config=repo / ".plazmic-ui-studio.json",
                game=game,
                layout=layout,
                screen_width=1920,
                screen_height=1080,
            )
            server = ui_studio.StudioServer(("127.0.0.1", 0), paths, ROOT / "ui-tools" / "studio")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                connection.request("GET", "/api/state")
                response = connection.getresponse()
                self.assertEqual(response.status, 403)
                response.read()

                connection.request(
                    "GET",
                    "/api/state",
                    headers={"X-Plazmic-Token": server.token},
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn("default-src 'self'", response.getheader("Content-Security-Policy"))
                self.assertIn(b'"width": 1920', response.read())

                connection.request(
                    "GET",
                    "/api/state",
                    headers={
                        "X-Plazmic-Token": server.token,
                        "Origin": "https://example.invalid",
                    },
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 403)
                response.read()

                connection.request(
                    "POST",
                    "/api/layout",
                    body=b"",
                    headers={
                        "X-Plazmic-Token": server.token,
                        "Origin": server.origin,
                        "Content-Length": str(ui_studio.MAX_REQUEST_BYTES + 1),
                    },
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 400)
                self.assertIn(b"request is too large", response.read())
            finally:
                connection.close()
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


class CliTests(unittest.TestCase):
    def test_unknown_command_fails_with_help(self) -> None:
        result = subprocess.run(
            [ROOT / "plazmic-ui", "unknown"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown command", result.stderr)

    def test_install_dry_run_rejects_workspace_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            game = root / "game"
            source = root / "source"
            default = game / "uifiles" / "default_modern"
            default.mkdir(parents=True)
            source.mkdir()
            (game / "eqgame.exe").write_bytes(b"client")
            for directory in (default, source):
                (directory / "EQUI.xml").write_text(
                    '<XML ID="EQInterfaceDefinitionLanguage" />\n', encoding="ascii"
                )
            (source / "linked.tga").symlink_to(root / "outside.tga")
            (source / ".plazmic-upstream").write_text("source=synthetic\n", encoding="ascii")

            result = subprocess.run(
                [
                    ROOT / "ui-tools" / "install-ui.sh",
                    "--game-dir",
                    game,
                    "--source",
                    source,
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("contains a symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
