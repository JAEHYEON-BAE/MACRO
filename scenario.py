import time
import random
from dataclasses import dataclass, field
from typing import Callable
import cv2
import numpy as np
from device import ADBDevice


SCENE_RESULT              = "images/result.png"
SCENE_MYSTERY_BOX_BEFORE  = "images/misterybox_before_open.png"
SCENE_MYSTERY_BOX_AFTER   = "images/misterybox_after_open.png"
SCENE_LOBBY               = "images/lobby.png"
SCENE_POPUP               = "images/popup.png"
SCENE_MAILBOX             = "images/mailbox.png"
SCENE_FRIEND_INFO         = "images/friend_info.png"


@dataclass
class SceneDef:
    image: str
    # 매칭할 영역 목록: (y0, y1, x0, x1) 비율. 모두 일치해야 감지.
    regions: list[tuple[float, float, float, float]]
    handler: Callable[["ADBDevice"], None]
    threshold: float = 0.8
    template_gray: np.ndarray | None = field(default=None, repr=False)


def load_templates() -> None:
    """SCENES의 템플릿을 그레이스케일로 메모리에 미리 로딩한다."""
    for scene in SCENES:
        t = cv2.imread(scene.image, cv2.IMREAD_GRAYSCALE)
        if t is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {scene.image}")
        scene.template_gray = t


def _jitter(sigma: float = 6.0) -> tuple[float, float]:
    return random.gauss(0, sigma), random.gauss(0, sigma)


def _handle_result(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: result")
    dx, dy = _jitter()
    device.tap(1000 + dx, 1200 + dy)


def _handle_mystery_box_before(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: mystery box (before open)")
    dx, dy = _jitter()
    device.tap(1300 + dx, 1300 + dy)


def _handle_mystery_box_after(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: mystery box (after open)")
    dx, dy = _jitter()
    device.tap(1300 + dx, 1300 + dy)


def _handle_lobby(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: lobby")
    for _ in range(5):
        dx, dy = _jitter()
        device.tap(1800 + dx, 1250 + dy)
        time.sleep(random.gauss(0.3, 0.1))


def _handle_popup(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: popup")
    dx, dy = _jitter()
    device.tap(1275 + dx, 1125 + dy)

def _handle_mailbox(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: mailbox")
    dx, dy = _jitter()
    device.tap(2260 + dx, 177 + dy)

def _handle_friend_info(device: ADBDevice) -> None:
    print(f"[{device.name}] scene: friend info")
    dx, dy = _jitter()
    device.tap(2180 + dx, 148 + dy)


# 화면 → 영역 + 핸들러 매핑. 순서 = 우선순위.
# regions: (y0, y1, x0, x1) 비율 — 이미지 전체 크기 기준.
SCENES: list[SceneDef] = [
    SceneDef(
        image=SCENE_POPUP,
        regions=[
            (0.75, 0.9, 0.3, 0.7),   # 하단 버튼
        ],
        handler=_handle_popup,
    ),
    SceneDef(
        image=SCENE_RESULT,
        regions=[
            (0.0, 0.15, 0.0, 1.0),   # 상단 "게임결과"
            (0.8, 1.0, 0.0, 1.0),   # 하단 "확인", "자랑하기"
        ],
        handler=_handle_result,
    ),
    SceneDef(
        image=SCENE_MYSTERY_BOX_BEFORE,
        regions=[
            (0.0, 0.15, 0.3, 0.7),   # 상단 "미스터리박스 오픈"
            (0.85, 0.98, 0.3, 0.7),   # 하단 "모두 열기"
        ],
        handler=_handle_mystery_box_before,
    ),
    SceneDef(
        image=SCENE_MYSTERY_BOX_AFTER,
        regions=[
            (0.0, 0.15, 0.3, 0.7),   # 상단 "미스터리박스 오픈"
            (0.85, 0.98, 0.3, 0.7),   # 하단 "확인"
        ],
        handler=_handle_mystery_box_after,
    ),
    SceneDef(
        image=SCENE_LOBBY,
        regions=[
            (0.71, 0.95, 0.6, 0.9),  # 우측 하단 "게임시작" 버튼
        ],
        handler=_handle_lobby,
        threshold=0.8,
    ),
    SceneDef(
        image=SCENE_MAILBOX,
        regions=[
            (0.08, 0.15, 0.4, 0.9),  # 상단 "메일박스", "x" 버튼
        ],
        handler=_handle_mailbox,
        threshold=0.8,
    ),
    SceneDef(
        image=SCENE_FRIEND_INFO,
        regions=[
            (0.08, 0.15, 0.4, 0.88),  # 상단 "친구정보", "x" 버튼
        ],
        handler=_handle_friend_info,
        threshold=0.8,
    ),
]


def run_scenario_loop(device: ADBDevice, poll_interval: float = 1.0) -> None:
    print(f"[{device.name}] start loop")
    load_templates()
    while device.is_connected():
        screen_gray = cv2.cvtColor(device.screenshot(), cv2.COLOR_BGR2GRAY)
        for scene in SCENES:
            if device.match_regions(screen_gray, scene.template_gray, scene.regions, scene.threshold):
                scene.handler(device)
                break
        else:
            time.sleep(poll_interval)
    print(f"[{device.name}] 디바이스 연결 끊김 — 루프 종료")
