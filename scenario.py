import time
import random
from device import ADBDevice


def run_scenario_loop(device: ADBDevice, trigger_image: str, poll_interval: float = 1.0) -> None:
    print(f"[{device.name}] start loop — trigger image: {trigger_image}")
    while device.is_connected():
        if device.find_stable_screen(trigger_image):
            print(f"[{device.name}] triggered → run scenario")
            run_scenario(device)
        else:
            # print(f"[{device.name}] 트리거 미감지 — {poll_interval}초 대기")
            time.sleep(poll_interval)
    print(f"[{device.name}] 디바이스 연결 끊김 — 루프 종료")


def _jitter(sigma: float = 6.0) -> tuple[float, float]:
    return random.gauss(0, sigma), random.gauss(0, sigma)


def run_scenario(device: ADBDevice) -> None:
    print(f"[{device.name}] scenario start")

    # 결과확인
    dx, dy = _jitter()
    device.tap(1000 + dx, 1200 + dy)
    time.sleep(1.0)

    # 미스터리박스 오픈
    for _ in range(6):
        dx, dy = _jitter()
        device.tap(1300 + dx, 1300 + dy)
        time.sleep(0.3)

    time.sleep(random.gauss(1.0, 0.2))
    # 게임시작
    for _ in range(5):
        dx, dy = _jitter()
        device.tap(1800 + dx, 1250 + dy)
        time.sleep(0.3)

    print(f"[{device.name}] scenario done")
