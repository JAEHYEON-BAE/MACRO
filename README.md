# CKR Macro

Requires Python 3.12 and `adb` available in your PATH.

## Setup

```sh
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Enable ADB on your emulator, check its ID with `adb devices`, and update `DEVICE_IDS` in `main.py`.

## Run

From the project directory:

```sh
source venv/bin/activate
python main.py
```

Press `Ctrl+C` to stop.
