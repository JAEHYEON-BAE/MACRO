import subprocess
import io
import numpy as np
import cv2
from PIL import Image


class ADBDevice:
    def __init__(self, device_id: str, name: str = ""):
        self.device_id = device_id
        self.name = name

    def screenshot(self) -> np.ndarray:
        result = subprocess.run(
            ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],
            capture_output=True,
        )
        if not result.stdout:
            raise RuntimeError(f"[{self.name}] screencap returned empty output")
        image = Image.open(io.BytesIO(result.stdout)).convert("RGB")
        arr = np.array(image)
        return arr[:, :, ::-1]  # RGB -> BGR

    def tap(self, x: int, y: int) -> None:
        subprocess.run(
            ["adb", "-s", self.device_id, "shell", "input", "tap", str(x), str(y)],
            check=True,
        )
        print(f"[{self.name}] tap ({x}, {y})")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        subprocess.run(
            [
                "adb", "-s", self.device_id, "shell", "input", "swipe",
                str(x1), str(y1), str(x2), str(y2), str(duration_ms),
            ],
            check=True,
        )

    def key_event(self, keycode: int) -> None:
        subprocess.run(
            ["adb", "-s", self.device_id, "shell", "input", "keyevent", str(keycode)],
            check=True,
        )

    def find_image(self, template_path: str, threshold: float = 0.8) -> bool:
        screen = self.screenshot()
        template = cv2.imread(template_path)
        if template is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val >= threshold

    def find_stable_screen(
        self,
        template_path: str,
        top_ratio: float = 0.18,
        bottom_ratio: float = 0.22,
        threshold: float = 0.8,
    ) -> bool:
        """
        템플릿 이미지의 상단(제목)과 하단(버튼) 영역만 분리해 매칭한다.
        중간의 점수·닉네임 등 가변 영역은 무시하므로 매 판 달라져도 안정적으로 감지된다.
        둘 다 화면에서 발견될 때만 True를 반환한다.
        """
        screen = self.screenshot()
        template = cv2.imread(template_path)
        if template is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")

        scale = screen.shape[1] / template.shape[1]
        if abs(scale - 1.0) > 0.01:
            new_w = int(template.shape[1] * scale)
            new_h = int(template.shape[0] * scale)
            template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        h = template.shape[0]
        top_strip = template[: int(h * top_ratio), :]
        bottom_strip = template[int(h * (1 - bottom_ratio)) :, :]

        for strip in (top_strip, bottom_strip):
            result = cv2.matchTemplate(screen, strip, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val < threshold:
                return False
        return True

    def is_connected(self) -> bool:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        return self.device_id in result.stdout
