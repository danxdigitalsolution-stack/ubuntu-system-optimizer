# 🐧 Ubuntu System Optimizer — Enterprise

A dark-themed PySide6 GUI for common Ubuntu/Debian system maintenance tasks — package cache cleanup, dependency fixes, updates, and application removal — wrapped around `apt`/`dpkg` with a live, scrollable process log. Root-requiring commands are run through `pkexec`, so you get Ubuntu's native graphical authentication prompt instead of typing your password into a terminal.

## Features

### 🧹 Dashboard & Cleanup
- **Clear Downloaded Package Cache** — `apt-get clean` (removes all cached `.deb` files from `/var/cache/apt/archives/`)
- **Clear Obsolete Package Cache** — `apt-get autoclean` (removes only cache files that can no longer be downloaded)
- **Remove Unused Dependencies** — `apt-get autoremove` (removes orphaned packages no longer required by anything installed)

### 🔧 Maintenance & Fixes
- **Refresh Package Lists** — `apt-get update`
- **Upgrade System Packages** — `apt-get upgrade`
- **Fix Broken Dependencies** — `apt-get --fix-broken install`
- **Reconfigure Interrupted Installs** — `dpkg --configure -a`
- **Fix Broken Thumbnails** — clears and recreates `~/.cache/thumbnails` (runs without root, since it only touches the user's own cache)

### 🗑 App Uninstaller
- Enter an exact package name and completely remove it, including its configuration files — `apt-get remove --purge`
- Confirmation dialog before any purge is executed

### 🖥 UI / Execution
- Commands run on a background `QThread` (`CommandRunner`) so the GUI never freezes
- Live, auto-scrolling process log (stdout + stderr merged) at the bottom of the window, always visible regardless of which page is active
- UI is disabled while a command is running, with a "busy" prompt if another action is attempted mid-run
- Exit code is reported at the end of every run, with a hint that codes `126`/`127` usually mean the `pkexec` authentication prompt was canceled
- Dark "charcoal enterprise" Qt stylesheet, with distinct visual treatment for the destructive uninstall action (`DangerButton`) and the cache-clearing warning action (`WarningButton`)

## Requirements

- **Ubuntu or another Debian-based distribution** (relies on `apt-get`, `dpkg`, and `pkexec`, which are Debian/Ubuntu-specific)
- Python 3.8+
- [PySide6](https://pypi.org/project/PySide6/)
- `policykit-1` (provides `pkexec`) — installed by default on standard Ubuntu desktop images

```bash
pip install PySide6
```

## Usage

```bash
python3 ubuntu_system_optimizer.py
```

Run as your normal user — **do not** launch with `sudo`. Any action that needs elevated privileges triggers a native `pkexec` authentication dialog on demand, rather than requiring the whole app to run as root.

1. Use the sidebar to switch between **Dashboard & Cleanup**, **Maintenance & Fixes**, and **App Uninstaller**
2. Click any action button to run the corresponding command
3. Watch progress and output in the **Process Log** panel at the bottom
4. For uninstalling an app, type the exact package name (e.g. `firefox`, `vlc`) and confirm the removal prompt

## How it works

| Component | Purpose |
|---|---|
| `CommandRunner` (`QThread`) | Runs a given command list via `subprocess.Popen`, prefixing it with `pkexec` when root is required, and streams merged stdout/stderr back to the GUI line by line |
| `run_system_command()` | Guards against overlapping runs, disables the UI, clears the log, and starts a `CommandRunner` for the requested command |
| `fix_thumbnails()` | Runs entirely in Python (no subprocess/root needed) — deletes and recreates `~/.cache/thumbnails` |
| `uninstall_app()` | Validates the package name field, shows a confirmation dialog, then runs `apt-get remove --purge` on confirmation |
| `apply_stylesheet()` | Defines the app's dark charcoal Qt stylesheet, including dedicated styling for warning/danger buttons |

## Notes

- All `apt-get`/`dpkg` actions are run with `-y`, so they proceed without an additional interactive confirmation once triggered from the GUI — the app's own confirmation dialog (for uninstall) is the safety check in that case.
- Purging a package removes its configuration files as well as the binary — this is not reversible from within the app.
- Because this tool shells out to `apt-get`/`dpkg`/`pkexec` directly, it will not run on non-Debian-based distributions (Fedora, Arch, etc.) without modification.
