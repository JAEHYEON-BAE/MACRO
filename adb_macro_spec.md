# ADB Multi-Instance Macro Automation — Specification Document

## Purpose

This document specifies the architecture and implementation of a **minimal ADB-based macro automation program** targeting multiple BlueStacks Air Android emulator instances on macOS. It is intended to be consumed by an AI coding agent (e.g., Claude Code) as a ground-truth specification for code generation.

---

## Scope and Constraints

- **In scope**: ADB device connection, screenshot capture, coordinate-based tap/swipe, sequential action execution, multi-instance parallel execution.
- **Out of scope (do not implement)**: Image template matching, OCR/text recognition, dynamic UI detection, any GUI. These will be added in a later phase.
- **Target environment**: macOS, Python 3.11+, BlueStacks Air with ADB enabled.
- **Known device IDs**: `emulator-5564` (Instance 1), `emulator-5574` (Instance 2).

---

## Project Structure

```
adb_macro/
├── main.py          # Entry point. Discovers devices and runs scenarios in parallel.
├── device.py        # ADBDevice class. Wraps all adb shell calls.
├── scenario.py      # Scenario function(s). Defines the sequence of actions per instance.
└── requirements.txt # Python dependencies.
```

> **Rule for the agent**: One responsibility per file. Do not merge classes or scenario logic into `main.py`.

---

## Module Specifications

### `device.py`

**Intent**: Provide a thin, stateless wrapper around `adb -s <device_id> shell` commands. Every method must be a direct mapping to a single ADB operation. No logic beyond argument formatting and subprocess invocation.

**Class**: `ADBDevice`

**Constructor**:
```python
def __init__(self, device_id: str, name: str = "")
```
- `device_id`: ADB device identifier string, e.g. `"emulator-5564"`.
- `name`: Human-readable label used only in log output.

**Methods** (implement all of the following, no others):

```python
def screenshot(self) -> np.ndarray
```
- Runs `adb -s <device_id> exec-out screencap -p`.
- Decodes the raw PNG bytes from stdout into a NumPy array in BGR format (OpenCV-compatible).
- Returns the array. Raises `RuntimeError` if stdout is empty.

```python
def tap(self, x: int, y: int) -> None
```
- Runs `adb -s <device_id> shell input tap <x> <y>`.
- Prints a log line: `[<name>] tap (<x>, <y>)`.

```python
def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None
```
- Runs `adb -s <device_id> shell input swipe <x1> <y1> <x2> <y2> <duration_ms>`.

```python
def key_event(self, keycode: int) -> None
```
- Runs `adb -s <device_id> shell input keyevent <keycode>`.
- Common keycodes: `3` = HOME, `4` = BACK.

```python
def is_connected(self) -> bool
```
- Runs `adb devices` (no `-s` flag).
- Returns `True` if `self.device_id` appears in stdout.

**Imports required**: `subprocess`, `io`, `numpy`, `PIL.Image`

---

### `scenario.py`

**Intent**: Define the automation sequence as a plain Python function that accepts an `ADBDevice` and executes a fixed, hardcoded list of actions in order. No branching, no detection logic.

**Function signature**:
```python
def run_scenario(device: ADBDevice) -> None
```

**Implementation rules**:
- The body is a linear sequence of `device.tap(...)`, `device.swipe(...)`, `device.key_event(...)`, and `time.sleep(...)` calls.
- Every action must be followed by an appropriate `time.sleep()` to allow the emulator UI to settle. Minimum sleep between taps: `0.5` seconds.
- Coordinates are in the emulator's internal pixel space (independent of macOS display resolution).
- Log the start and end of the scenario with `print(f"[{device.name}] scenario start")` and `print(f"[{device.name}] scenario done")`.

**Placeholder implementation** (agent must keep this structure, replacing coordinates as needed):
```python
def run_scenario(device: ADBDevice) -> None:
    import time
    print(f"[{device.name}] scenario start")

    device.tap(540, 960)
    time.sleep(1.0)

    device.swipe(540, 1400, 540, 600, duration_ms=400)
    time.sleep(0.8)

    device.tap(540, 500)
    time.sleep(0.5)

    print(f"[{device.name}] scenario done")
```

**Imports required**: `time`, `device.ADBDevice`

---

### `main.py`

**Intent**: Discover connected devices, validate connectivity, then execute `run_scenario` on each device concurrently using threads.

**Implementation rules**:
- Define `DEVICE_IDS` as a module-level list of known ADB device ID strings.
- Instantiate one `ADBDevice` per entry.
- Before launching threads, call `device.is_connected()` for each. Skip (with a warning print) any device that is not connected.
- Use `threading.Thread` with `daemon=True`. Start all threads, then `join` all threads.
- Do not use `multiprocessing`. Do not use `asyncio`.

**Structure**:
```python
DEVICE_IDS = [
    ("emulator-5564", "Instance-1"),
    ("emulator-5574", "Instance-2"),
]

def main() -> None:
    devices = [ADBDevice(did, name) for did, name in DEVICE_IDS]

    active = []
    for dev in devices:
        if dev.is_connected():
            active.append(dev)
        else:
            print(f"[WARN] {dev.name} ({dev.device_id}) not connected — skipping")

    threads = [threading.Thread(target=run_scenario, args=(dev,), daemon=True) for dev in active]
    for t in threads: t.start()
    for t in threads: t.join()

    print("All instances finished.")

if __name__ == "__main__":
    main()
```

**Imports required**: `threading`, `device.ADBDevice`, `scenario.run_scenario`

---

### `requirements.txt`

```
opencv-python
numpy
pillow
```

> `pytesseract` and other vision libraries must NOT be included at this phase.

---

## Coordinate System

- All `(x, y)` coordinates are in the **emulator's internal resolution**, not macOS screen pixels.
- To determine the internal resolution, run:
  ```bash
  adb -s emulator-5564 shell wm size
  # Expected output: Physical size: <width>x<height>
  ```
- To capture a reference screenshot for coordinate measurement:
  ```bash
  adb -s emulator-5564 exec-out screencap -p > reference.png
  ```
  Open `reference.png` in any image viewer that shows pixel coordinates (e.g., Preview.app with cursor position, or GIMP).

---

## Environment Setup

```bash
# 1. Verify ADB is installed and devices are visible
adb devices
# Expected: emulator-5564 and emulator-5574 listed as "device"

# 2. Install Python dependencies
pip install opencv-python numpy pillow

# 3. Run
python main.py
```

---

## Explicit Non-Goals (do not implement unless instructed)

| Feature | Reason excluded |
|---|---|
| Image template matching (`cv2.matchTemplate`) | Phase 2 |
| OCR / text detection (`pytesseract`) | Phase 2 |
| Config files or CLI argument parsing | Unnecessary complexity at this phase |
| Error retry logic | Out of scope for minimal version |
| GUI or dashboard | Out of scope |
| Logging to file | Out of scope |

---

## Agent Instructions Summary

1. Implement exactly three source files: `device.py`, `scenario.py`, `main.py`.
2. Follow method signatures and return types exactly as specified.
3. Do not add any method, class, or import not listed in this document.
4. Placeholder coordinates in `scenario.py` are intentional — do not invent real coordinates.
5. All print-based logging must include the device name in brackets: `[Instance-1]`.
