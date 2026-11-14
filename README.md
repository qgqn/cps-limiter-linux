# CPS Limiter & Sensitivity (Linux)

A lightweight, precise CPS (Clicks Per Second) limiter and mouse sensitivity adjuster for Linux, designed primarily for Gamers.

## Features
- Limits Left and Right Click CPS independently.
- Adjusts mouse sensitivity (e.g., 0.61) without pixel skipping.
- Works at the hardware level (`evdev`).
- Runs in the background with a simple GUI.

## Prerequisites
- Linux (X11 or Wayland)
- Python 3
- `python-evdev` installed (`sudo pacman -S python-evdev` on Arch/Manjaro)

## Installation

**1. Build the Executable:**
Install PyInstaller if you haven't already:
```bash
pip install pyinstaller --break-system-packages
