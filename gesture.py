# ------------------- Virtual Mouse with Volume & Brightness Control -------------------
# Install required packages: opencv, mediapipe, pyautogui, pywin32, pycaw, screen_brightness_control

import cv2
import mediapipe as mp
import numpy as np
# landmark_pb2 is a protocolbuffer file used by mediapipe to store and represent landmark data like handpoints, face mesh points or body poses.
import time
from math import sqrt                                                                                 
import win32api
import pyautogui
# win32api: allows interaction with Windows API for mouse/keyboard
# pyautogui: cross-platform automation of mouse/keyboard

# For volume control
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# For brightness control
import screen_brightness_control as sbc

import os  # for opening files
print(mp.solutions)
# -------------------- MediaPipe Hands Setup --------------------
m_drawing = mp.solutions.drawing_utils
m_hands = mp.solutions.hands

# -------------------- Variables --------------------
click = 0
dragging = False
prev_screen_x, prev_screen_y = 0, 0
smoothening = 7
stop_gesture_flag = False
screen_w, screen_h = pyautogui.size()

prev_hand_center_x = None
prev_hand_center_y = None

# Scroll variables
two_fingers_joined_frames = 0
JOINED_FRAMES_REQUIRED = 3
last_scroll_time = 0
SCROLL_COOLDOWN = 0.12
MIN_DY_FOR_SCROLL = 12
SCROLL_SCALE = 3
MAX_SCROLL_PER_ACTION = 250
FINGERS_JOINED_DIST_PX = 40

# Cooldown for app actions
last_action_time = 0
ACTION_COOLDOWN = 2

# -------------------- Pycaw Setup for Volume --------------------
from comtypes.client import CreateObject
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import IMMDeviceEnumerator

enumerator = CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)
device = enumerator.GetDefaultAudioEndpoint(0, 1)  # 0=eRender, 1=Console
volume = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(volume, POINTER(IAudioEndpointVolume))

def set_volume(level):
    volume.SetMasterVolumeLevelScalar(level, None)

def get_volume():
    return volume.GetMasterVolumeLevelScalar()

def set_brightness(level):
    sbc.set_brightness(level)

# -------------------- Helper Function --------------------
def fingers_up(hand_landmarks):
    """Returns list indicating which fingers are up (1) or down (0)"""
    fingers = []
    # Thumb
    fingers.append(1 if hand_landmarks.landmark[m_hands.HandLandmark.THUMB_TIP].x < hand_landmarks.landmark[m_hands.HandLandmark.THUMB_IP].x else 0)
    # Index
    fingers.append(1 if hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_TIP].y < hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_PIP].y else 0)
    # Middle
    fingers.append(1 if hand_landmarks.landmark[m_hands.HandLandmark.MIDDLE_FINGER_TIP].y < hand_landmarks.landmark[m_hands.HandLandmark.MIDDLE_FINGER_PIP].y else 0)
    # Ring
    fingers.append(1 if hand_landmarks.landmark[m_hands.HandLandmark.RING_FINGER_TIP].y < hand_landmarks.landmark[m_hands.HandLandmark.RING_FINGER_PIP].y else 0)
    # Pinky
    fingers.append(1 if hand_landmarks.landmark[m_hands.HandLandmark.PINKY_TIP].y < hand_landmarks.landmark[m_hands.HandLandmark.PINKY_PIP].y else 0)
    return fingers

# -------------------- Main Program --------------------
def run():
    global prev_screen_x, prev_screen_y, prev_hand_center_x, prev_hand_center_y, click, dragging, two_fingers_joined_frames, last_scroll_time, stop_gesture_flag
    # Reset variables for new session
    prev_screen_x, prev_screen_y = 0, 0
    prev_hand_center_x = None
    prev_hand_center_y = None
    click = 0
    dragging = False
    last_action_time = 0
    ACTION_COOLDOWN = 2
    two_fingers_joined_frames = 0
    last_scroll_time = 0
    video = cv2.VideoCapture(0)
# -------------------- Main Loop --------------------
    with m_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.8) as hands:
        while not stop_gesture_flag and video.isOpened():
            ret, frame = video.read()
            if not ret:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = cv2.flip(image, 1)
            imgheight, imgwidth, _ = image.shape

            results = hands.process(image)
            gesture_text = ""  # display gesture info

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    m_drawing.draw_landmarks(
                        image, hand_landmarks, m_hands.HAND_CONNECTIONS,
                        m_drawing.DrawingSpec(color=(250, 0, 0), thickness=2, circle_radius=4),
                    )

                    # -------------------- Get Hand Points --------------------
                    index_x = int(hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_TIP].x * imgwidth)
                    index_y = int(hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_TIP].y * imgheight)

                    thumb_x = int(hand_landmarks.landmark[m_hands.HandLandmark.THUMB_TIP].x * imgwidth)
                    thumb_y = int(hand_landmarks.landmark[m_hands.HandLandmark.THUMB_TIP].y * imgheight)

                    pinky_x = int(hand_landmarks.landmark[m_hands.HandLandmark.PINKY_TIP].x * imgwidth)
                    pinky_y = int(hand_landmarks.landmark[m_hands.HandLandmark.PINKY_TIP].y * imgheight)

                    # Always compute wrist (hand center) so scrolling logic in cursor mode has a reference
                    hand_center_x = int(hand_landmarks.landmark[m_hands.HandLandmark.WRIST].x * imgwidth)
                    hand_center_y = int(hand_landmarks.landmark[m_hands.HandLandmark.WRIST].y * imgheight)

                    # -------------------- Detect Mode --------------------
                    fingers = fingers_up(hand_landmarks)
                    if fingers == [0,0,0,0,0]:  # FIST -> Volume/Brightness mode
                        # -------------------- VOLUME CONTROL --------------------
                        if prev_hand_center_y is not None:
                            dy = prev_hand_center_y - hand_center_y  # move up = increase
                            vol_level = np.interp(dy, [-1200, 1200], [0.0, 1.0]) # larger hand movement range = smaller volume change
                            set_volume(max(0, min(vol_level, 1)))
                            gesture_text += f"Volume: {int(get_volume()*100)}% "
                            print(f"[LOG] Volume set to {int(get_volume()*100)}%")

                        # -------------------- BRIGHTNESS CONTROL --------------------
                        if prev_hand_center_x is not None:
                            dx = hand_center_x - prev_hand_center_x  # move right = increase
                            bright_level = np.interp(dx, [-1200, 1200], [0, 100])  # larger hand movement range = smaller brightness change
                            set_brightness(max(0, min(int(bright_level), 100)))
                            gesture_text += f"Brightness: {int(bright_level)}% "
                            print(f"[LOG] Brightness set to {int(bright_level)}%")

                        prev_hand_center_y = hand_center_y
                        prev_hand_center_x = hand_center_x

                    else:

                        # -------------------- Move Cursor --------------------
                        
                        screen_x = np.interp(index_x, [0, imgwidth], [0, screen_w])
                        screen_y = np.interp(index_y, [0, imgheight], [0, screen_h])

                        cur_screen_x = prev_screen_x + (screen_x - prev_screen_x) / smoothening
                        cur_screen_y = prev_screen_y + (screen_y - prev_screen_y) / smoothening
                        win32api.SetCursorPos((int(cur_screen_x), int(cur_screen_y)))
                        prev_screen_x, prev_screen_y = cur_screen_x, cur_screen_y
                         # -------------------- LEFT CLICK --------------------
                        distance = sqrt((index_x - thumb_x) ** 2 + (index_y - thumb_y) ** 2)
                        if distance < 40:
                            click += 1
                            gesture_text += "Left Click "
                            if click % 5 == 0:
                                pyautogui.click()
                                print("[LOG] Left Click")
                        else:
                            click = 0

                         # -------------------- DRAG & DROP --------------------
                        if distance < 25 and not dragging:
                            pyautogui.mouseDown()
                            dragging = True
                            gesture_text += "Dragging "
                            print("[LOG] Dragging started")
                        elif distance > 25 and dragging:
                            pyautogui.mouseUp()
                            dragging = False
                            print("[LOG] Dragging ended")

                        # -------------------- RIGHT CLICK --------------------
                        right_distance = sqrt((thumb_x - pinky_x) ** 2 + (thumb_y - pinky_y) ** 2)
                        if right_distance < 25:
                            pyautogui.rightClick()
                            gesture_text += "Right Click "
                            print("[LOG] Right Click")

                        # ---------------- SCROLL ----------------
                      # -------------------- SCROLL --------------------
                        # -------------------- SCROLL WITH 2 FINGERS JOINED (RELIABLE VERSION) --------------------
                        # Compute fingertip coordinates using appropriate axes
                        ix = hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_TIP].x * imgwidth
                        iy = hand_landmarks.landmark[m_hands.HandLandmark.INDEX_FINGER_TIP].y * imgheight

                        mx = hand_landmarks.landmark[m_hands.HandLandmark.MIDDLE_FINGER_TIP].x * imgwidth
                        my = hand_landmarks.landmark[m_hands.HandLandmark.MIDDLE_FINGER_TIP].y * imgheight

                        two_fingers_distance = sqrt((ix - mx)**2 + (iy - my)**2)

                        # If index+middle are close, count this frame as "joined"
                        if two_fingers_distance < FINGERS_JOINED_DIST_PX:
                            two_fingers_joined_frames += 1
                        else:
                            two_fingers_joined_frames = 0

                        # Only consider scrolling when fingers have been joined for required consecutive frames
                        if two_fingers_joined_frames >= JOINED_FRAMES_REQUIRED:
                            # use wrist vertical motion for scrolling
                            if prev_hand_center_y is not None:
                                dy_scroll = prev_hand_center_y - hand_center_y  # positive when hand moved up
                                # require some minimum movement to avoid tiny jitter
                                if abs(dy_scroll) >= MIN_DY_FOR_SCROLL:
                                    now = time.time()
                                    if now - last_scroll_time >= SCROLL_COOLDOWN:
                                        # convert pixel delta to scroll units (tunable)
                                        scroll_amount = int(np.sign(dy_scroll) * min(MAX_SCROLL_PER_ACTION, abs(dy_scroll) * SCROLL_SCALE))
                                        # perform the scroll
                                        pyautogui.scroll(scroll_amount)
                                        last_scroll_time = now
                                        if scroll_amount > 0:
                                            gesture_text += "Scroll Up "
                                            print(f"[LOG] Scroll Up (joined fingers) amt={scroll_amount}")
                                        else:
                                            gesture_text += "Scroll Down "
                                            print(f"[LOG] Scroll Down (joined fingers) amt={scroll_amount}")

                        # always update prev_hand_center_y for next frame
                        prev_hand_center_y = hand_center_y


                        # ---------------- NEW FEATURES ----------------

                        if time.time() - last_action_time > ACTION_COOLDOWN:

                            if fingers == [1,0,0,0,0]:
                                os.system("start chrome")
                                gesture_text += "Open Chrome"
                                last_action_time=time.time()
                                print("chrome opened")

                            elif fingers == [1,1,0,0,1]:
                                os.system("notepad")
                                gesture_text += "Open Notepad"
                                last_action_time=time.time()
                                print("notepad opened")

                            elif fingers == [1,1,1,1,1]:
                                os.system("start ms-settings:")
                                gesture_text += "Open Settings"
                                last_action_time=time.time()
                                print("settings")

                            elif fingers == [1,0,0,0,1]:
                                pyautogui.hotkey("win","a")   # open quick settings
                                time.sleep(1)
                                pyautogui.press("b")          # toggle bluetooth
                                gesture_text += "Bluetooth Toggle"
                                last_action_time=time.time()
                                print("Bluetooth toggled")

                            elif fingers == [1,1,1,0,0]:
                                screenshot = pyautogui.screenshot()
                                screenshot.save("screenshot.png")
                                gesture_text += "Screenshot Taken "
                                print("[LOG] Screenshot taken")
                                time.sleep(1)
                                filename = f"screenshot_{int(time.time())}.png"
                                screenshot.save(filename)

                            elif fingers == [0,1,1,1,1]:
                                pyautogui.hotkey("alt","tab")
                                gesture_text += "Next Tab"
                                last_action_time=time.time()
                                print("Next tab")

                            elif fingers == [0,1,1,0,0]:

                                if two_fingers_distance > 80:
                                    pyautogui.hotkey("ctrl","+")
                                    gesture_text += "Zoom In"
                                    last_action_time=time.time()
                                    print("zoom in")

                                elif two_fingers_distance < 40:
                                    pyautogui.hotkey("ctrl","-")
                                    gesture_text += "Zoom Out"
                                    last_action_time=time.time()
                                    print("zoom")

            if gesture_text != "":
                cv2.putText(image,gesture_text,(10,50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,(0,255,0),2)

            image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)

            cv2.imshow("Virtual Mouse",image)

            if cv2.waitKey(1) & 0xFF == ord('x'):
                break

    video.release()
    cv2.destroyAllWindows()