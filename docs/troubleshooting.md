# Troubleshooting and rollback

## Game directory is not found

The selected directory must directly contain `eqgame.exe`. Set it for the
current shell or pass it explicitly:

```bash
export EQ_LEGENDS_DIR='/path/to/EverQuest Legends'
./plazmic-ui capture
```

Delete ignored `.plazmic-ui-workspace/studio.json` if a previously saved local
path is no longer valid.

## Multiple layouts are found

Interactive commands show a numbered list. Non-interactive commands fail
instead of guessing. Pass only a top-level filename:

```bash
./plazmic-ui capture --layout UI_example.ini
./plazmic-ui publish --target-ini UI_example.ini
```

Nested and absolute layout paths are intentionally rejected.

## The reviewed XML hash changed

A game patch changed `EQUI_AdvancedLootWnd.xml`. `sync` stops before applying a
stale transformation. Do not replace the hash blindly. Compare the new shipped
file, update the transformation and synthetic tests, then record the reviewed
new hash.

`capture` remains available when you want to edit the currently installed skin
without applying the reviewed derivative.

## The Studio does not open

Copy the printed `http://127.0.0.1:<port>/` URL into a current browser. Confirm
the terminal process is still running and that no browser extension is
rewriting loopback requests. Do not change the bind address or expose the port.

If local configuration points to a missing layout, capture it again.

## A save is rejected

- INI positions must be between -200% and 200%.
- Width and height must be 1-8192 pixels.
- Alpha and tint channels must be 0-255.
- XML must be US-ASCII, well formed, under 10 MiB, and use the EQ interface
  root.
- Symlinked layouts, skins, and XML files are intentionally unsupported.

## Offline install says the game is running

`install` refuses when any `eqgame.exe` process is present. Exit the game and
retry. For intentional live UI iteration use `publish`, which still validates,
stages, backs up, and limits the target paths.

## Restore a backup

Stop the Studio before restoring workspace files.

- Local skin captures and refreshes use sibling
  `.plazmic-ui-workspace/skin.backup-*` paths.
- Local INI/XML edits are under
  `.plazmic-ui-workspace/backups/<filename>/`.
- Installed skins use sibling `uifiles/plazmic-ui.backup-*` paths.
- Published layouts use sibling `UI_name.ini.backup-*` files.

Move the current target aside, move the chosen backup back to its original
name, then reload the skin. Do not restore over `default` or `default_modern`.

As the simplest visual rollback inside EverQuest, load the shipped skin:

```text
/loadskin default_modern 1
```
