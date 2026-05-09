import threading
from device import ADBDevice
from scenario import run_scenario_loop

TRIGGER_IMAGE = "images/trigger.png"  # 트리거 이미지 경로

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

    threads = [threading.Thread(target=run_scenario_loop, args=(dev, TRIGGER_IMAGE), daemon=True) for dev in active]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("All instances finished.")


if __name__ == "__main__":
    main()
