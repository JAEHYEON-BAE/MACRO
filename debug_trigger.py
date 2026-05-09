"""
트리거 감지 디버그 스크립트.
게임결과 화면이 떠있는 상태에서 실행하세요.
"""
import cv2
from device import ADBDevice
from main import DEVICE_IDS, TRIGGER_IMAGE

TOP_RATIO = 0.18
BOTTOM_RATIO = 0.22

device = ADBDevice(*DEVICE_IDS[0])

print("스크린샷 캡처 중...")
screen = device.screenshot()
cv2.imwrite("debug_screen.png", screen)
print(f"화면 크기:    {screen.shape[1]}x{screen.shape[0]} (w x h)")

template = cv2.imread(TRIGGER_IMAGE)
print(f"trigger.png:  {template.shape[1]}x{template.shape[0]} (w x h)")

scale = screen.shape[1] / template.shape[1]
print(f"\n스케일 비율: {scale:.4f}")
if abs(scale - 1.0) > 0.01:
    new_w = int(template.shape[1] * scale)
    new_h = int(template.shape[0] * scale)
    template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    print(f"리사이즈 후 trigger.png: {template.shape[1]}x{template.shape[0]}")

h = template.shape[0]
top_strip    = template[: int(h * TOP_RATIO), :]
bottom_strip = template[int(h * (1 - BOTTOM_RATIO)) :, :]

cv2.imwrite("debug_top_strip.png",    top_strip)
cv2.imwrite("debug_bottom_strip.png", bottom_strip)
print(f"\n상단 strip 크기: {top_strip.shape[1]}x{top_strip.shape[0]}")
print(f"하단 strip 크기: {bottom_strip.shape[1]}x{bottom_strip.shape[0]}")

for name, strip in [("상단(제목)", top_strip), ("하단(버튼)", bottom_strip)]:
    res = cv2.matchTemplate(screen, strip, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    print(f"\n[{name}] 최대 매칭 점수: {max_val:.4f}  위치: {max_loc}")
    if max_val >= 0.8:
        print(f"  → threshold 0.8 통과")
    elif max_val >= 0.6:
        print(f"  → threshold 0.6~0.8: threshold를 낮추거나 해상도를 확인하세요")
    else:
        print(f"  → 점수가 매우 낮음: 해상도 불일치 또는 화면이 다름")

print("\n디버그 이미지 저장됨: debug_screen.png / debug_top_strip.png / debug_bottom_strip.png")
