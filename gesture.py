import cv2
import mediapipe as mp
import numpy as np
import time
from math import sqrt
import pyautogui
import win32api
import os

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import IAudioEndpointVolume
from comtypes.client import CreateObject
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import IMMDeviceEnumerator
import screen_brightness_control as sbc

# 🔴 ADD THIS (GLOBAL STOP FLAG)
stop_flag = False

# ---------------- Setup ----------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

# Volume setup
enumerator = CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)
device = enumerator.GetDefaultAudioEndpoint(0, 1)
volume = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(volume, POINTER(IAudioEndpointVolume))

def set_volume(v): volume.SetMasterVolumeLevelScalar(v, None)
def get_volume(): return volume.GetMasterVolumeLevelScalar()
def set_brightness(b): sbc.set_brightness(int(b))

# ---------------- Finger Detection ----------------
def fingers_up(hand):
    fingers = []
    fingers.append(1 if hand.landmark[4].x < hand.landmark[3].x else 0)
    fingers.append(1 if hand.landmark[8].y < hand.landmark[6].y else 0)
    fingers.append(1 if hand.landmark[12].y < hand.landmark[10].y else 0)
    fingers.append(1 if hand.landmark[16].y < hand.landmark[14].y else 0)
    fingers.append(1 if hand.landmark[20].y < hand.landmark[18].y else 0)
    return fingers

# ---------------- Main ----------------
def run():
    global stop_flag
    stop_flag = False   # 🔥 reset when starting

    cap = cv2.VideoCapture(0)

    prev_x, prev_y = 0, 0
    smooth = 7

    prev_vol_y = None
    prev_bright_x = None
    prev_scroll_y = None

    last_action = 0
    last_scroll_time = 0

    gesture_count = 0
    prev_gesture = None

    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.8) as hands:
        while not stop_flag:   # 🔥 FIXED LOOP
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            gesture_text = ""
            scroll_active = False

            if result.multi_hand_landmarks:
                for hand in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                    h, w, _ = frame.shape

                    x = int(hand.landmark[8].x * w)
                    y = int(hand.landmark[8].y * h)

                    mx = int(hand.landmark[12].x * w)
                    my = int(hand.landmark[12].y * h)

                    wrist_y = int(hand.landmark[0].y * h)

                    fingers = fingers_up(hand)

                    # -------- Stability --------
                    if fingers == prev_gesture:
                        gesture_count += 1
                    else:
                        gesture_count = 0
                    prev_gesture = fingers

                    if gesture_count < 5:
                        continue

                    # ---------------- CONTROL MODE ----------------
                    if fingers == [0,0,0,0,0]:
                        gesture_text = "Control Mode"

                        if prev_vol_y is not None:
                            dy = prev_vol_y - wrist_y
                            set_volume(np.clip(get_volume() + dy/300, 0, 1))

                        if prev_bright_x is not None:
                            dx = x - prev_bright_x
                            set_brightness(np.clip(sbc.get_brightness()[0] + dx/5, 0, 100))

                        prev_vol_y = wrist_y
                        prev_bright_x = x
                        continue

                    prev_vol_y = None
                    prev_bright_x = None

                    # ---------------- MOVE ----------------
                    if fingers == [0,1,0,0,0]:
                        sx = np.interp(x, [0,w], [0,screen_w])
                        sy = np.interp(y, [0,h], [0,screen_h])

                        cx = prev_x + (sx - prev_x)/smooth
                        cy = prev_y + (sy - prev_y)/smooth

                        win32api.SetCursorPos((int(cx), int(cy)))
                        prev_x, prev_y = cx, cy
                        gesture_text = "Move"

                    # ---------------- SCROLL ----------------
                    elif fingers == [0,1,1,0,0]:
                        gesture_text = "Scroll"
                        scroll_active = True

                        if prev_scroll_y is None:
                            prev_scroll_y = wrist_y
                        else:
                            dy = prev_scroll_y - wrist_y

                            if abs(dy) > 5 and time.time() - last_scroll_time > 0.05:
                                scroll_amount = int(dy * 5)
                                pyautogui.scroll(scroll_amount)
                                last_scroll_time = time.time()

                            prev_scroll_y = wrist_y

                    # ---------------- LEFT CLICK ----------------
                    elif fingers == [0,1,0,0,1]:
                        if time.time() - last_action > 1:
                            pyautogui.click()
                            gesture_text = "Left Click"
                            last_action = time.time()

                    # ---------------- RIGHT CLICK ----------------
                    elif fingers == [1,0,0,0,1]:
                        if time.time() - last_action > 1:
                            pyautogui.rightClick()
                            gesture_text = "Right Click"
                            last_action = time.time()

                    # ---------------- ZOOM ----------------
                    elif fingers == [0,1,1,1,0]:
                        dist = sqrt((x-mx)**2 + (y-my)**2)
                        if time.time() - last_action > 1:
                            if dist > 80:
                                pyautogui.hotkey("ctrl","+")
                            elif dist < 30:
                                pyautogui.hotkey("ctrl","-")
                            gesture_text = "Zoom"
                            last_action = time.time()

                    # ---------------- CLOSE WINDOW ----------------
                    elif fingers == [0,0,0,0,1]:
                        if time.time() - last_action > 2:
                            pyautogui.hotkey("alt","f4")
                            gesture_text = "Close Window"
                            last_action = time.time()

                    # ---------------- SCREENSHOT ----------------
                    elif fingers == [1,1,1,0,0]:
                        if time.time() - last_action > 2:
                            pyautogui.screenshot().save(f"screenshot_{int(time.time())}.png")
                            gesture_text = "Screenshot"
                            last_action = time.time()

                    # ---------------- CHROME ----------------
                    elif fingers == [1,0,0,0,0]:
                        if time.time() - last_action > 2:
                            os.system("start chrome")
                            gesture_text = "Chrome"
                            last_action = time.time()

                    # ---------------- NOTEPAD ----------------
                    elif fingers == [1,1,0,0,1]:
                        if time.time() - last_action > 2:
                            os.system("notepad")
                            gesture_text = "Notepad"
                            last_action = time.time()

                    # ---------------- SETTINGS ----------------
                    elif fingers == [1,1,1,1,1]:
                        if time.time() - last_action > 2:
                            os.system("start ms-settings:")
                            gesture_text = "Settings"
                            last_action = time.time()

                    # ---------------- ALT TAB ----------------
                    elif fingers == [0,1,1,1,1]:
                        if time.time() - last_action > 2:
                            pyautogui.hotkey("alt","tab")
                            gesture_text = "Alt Tab"
                            last_action = time.time()

            if not scroll_active:
                prev_scroll_y = None

            cv2.putText(frame, gesture_text, (10,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            cv2.imshow("Virtual Mouse", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('x') or key == 27:
                break

            # 🔥 STOP FROM UI
            if stop_flag:
                print("[INFO] Gesture stopped from UI")
                break

            if cv2.getWindowProperty("Virtual Mouse", cv2.WND_PROP_VISIBLE) < 1:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()
