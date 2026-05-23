import struct
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
        """Raw RGBA screencap — PNG 인코딩/디코딩 없이 픽셀 데이터를 직접 수신"""
        result = subprocess.run(
            ["adb", "-s", self.device_id, "exec-out", "screencap"],
            capture_output=True,
        )
        data = result.stdout
        if not data:
            raise RuntimeError(f"[{self.name}] screencap returned empty output")
        w, h, _ = struct.unpack_from("<III", data, 0)
        header_size = len(data) - w * h * 4  # Android 버전마다 헤더 크기가 다름
        pixels = np.frombuffer(data, dtype=np.uint8, offset=header_size).reshape(h, w, 4)
        return cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGR)

    def screenshot_png(self) -> np.ndarray:
        """PNG 방식 폴백 — raw가 실패할 경우 사용."""
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
        screen = cv2.cvtColor(self.screenshot(), cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val >= threshold

    def match_regions(
        self,
        screen_gray: np.ndarray,
        template_gray: np.ndarray,
        regions: list[tuple[float, float, float, float]],
        threshold: float = 0.8,
    ) -> bool:
        """
        그레이스케일 screen/template으로 region 매칭
        루프에서 스크린샷과 cvtColor를 한 번만 하고 여러 씬에 재사용할 때 사용.
        regions: (y0, y1, x0, x1) 비율 목록. 모두 일치해야 True.
        """
        scale = screen_gray.shape[1] / template_gray.shape[1]
        if abs(scale - 1.0) > 0.01:
            new_w = int(template_gray.shape[1] * scale)
            new_h = int(template_gray.shape[0] * scale)
            template_gray = cv2.resize(template_gray, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        h, w = template_gray.shape[:2]
        for y0, y1, x0, x1 in regions:
            strip = template_gray[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
            result = cv2.matchTemplate(screen_gray, strip, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val < threshold:
                return False
        return True

    def find_screen_regions(
        self,
        template_path: str,
        regions: list[tuple[float, float, float, float]],
        threshold: float = 0.8,
    ) -> bool:
        template_gray = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template_gray is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")
        screen_gray = cv2.cvtColor(self.screenshot(), cv2.COLOR_BGR2GRAY)
        return self.match_regions(screen_gray, template_gray, regions, threshold)

    def find_stable_screen(
        self,
        template_path: str,
        top_ratio: float = 0.18,
        bottom_ratio: float = 0.22,
        threshold: float = 0.8,
    ) -> bool:
        screen_gray = cv2.cvtColor(self.screenshot(), cv2.COLOR_BGR2GRAY)
        template_gray = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template_gray is None:
            raise FileNotFoundError(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")

        scale = screen_gray.shape[1] / template_gray.shape[1]
        if abs(scale - 1.0) > 0.01:
            new_w = int(template_gray.shape[1] * scale)
            new_h = int(template_gray.shape[0] * scale)
            template_gray = cv2.resize(template_gray, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        h = template_gray.shape[0]
        for strip in (template_gray[:int(h * top_ratio), :], template_gray[int(h * (1 - bottom_ratio)):, :]):
            result = cv2.matchTemplate(screen_gray, strip, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val < threshold:
                return False
        return True

    def is_connected(self) -> bool:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        return self.device_id in result.stdout
