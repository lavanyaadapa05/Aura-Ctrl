import asyncio
import os
import time
from math import sqrt

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import screen_brightness_control as sbc
import win32api
import winreg
from comtypes import CLSCTX_ALL
from comtypes.client import CreateObject
from ctypes import POINTER, cast
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import IAudioEndpointVolume, IMMDeviceEnumerator
from winsdk.windows.devices import radios
from winsdk.windows.networking.connectivity import NetworkInformation
from winsdk.windows.networking.networkoperators import (
    NetworkOperatorTetheringManager,
    TetheringOperationalState,
)


mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()
stop_gesture_flag = False

enumerator = CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)
device = enumerator.GetDefaultAudioEndpoint(0, 1)
volume = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(volume, POINTER(IAudioEndpointVolume))


def set_volume(level):
    volume.SetMasterVolumeLevelScalar(float(level), None)


def get_volume():
    return volume.GetMasterVolumeLevelScalar()


def set_brightness(level):
    sbc.set_brightness(int(level))


def fingers_up(hand_landmarks):
    fingers = []
    fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
    fingers.append(1 if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y else 0)
    fingers.append(1 if hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y else 0)
    fingers.append(1 if hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y else 0)
    fingers.append(1 if hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y else 0)
    return fingers


def wifi_on():
    try:
        os.system("netsh wlan connect")
        print("WiFi turned on")
    except Exception:
        print("Unable to turn WiFi on")


def wifi_off():
    try:
        os.system("netsh wlan disconnect")
        print("WiFi turned off")
    except Exception:
        print("Unable to turn WiFi off")


async def set_bluetooth_state(turn_on):
    all_radios = await radios.Radio.get_radios_async()

    for radio in all_radios:
        if radio.kind == radios.RadioKind.BLUETOOTH:
            if turn_on:
                await radio.set_state_async(radios.RadioState.ON)
                print("Bluetooth turned on")
            else:
                await radio.set_state_async(radios.RadioState.OFF)
                print("Bluetooth turned off")


def bluetooth_on():
    asyncio.run(set_bluetooth_state(True))
    os.system("start ms-actioncenter:controlcenter/bluetooth")


def bluetooth_off():
    asyncio.run(set_bluetooth_state(False))
    os.system("start ms-actioncenter:controlcenter/bluetooth")


async def set_hotspot_state(turn_on):
    connection_profile = NetworkInformation.get_internet_connection_profile()
    if not connection_profile:
        print("No active internet connection found to share.")
        return

    tethering_manager = NetworkOperatorTetheringManager.create_from_connection_profile(
        connection_profile
    )

    if turn_on:
        if tethering_manager.tethering_operational_state == TetheringOperationalState.OFF:
            await tethering_manager.start_tethering_async()
            print("Hotspot turned on")
    elif tethering_manager.tethering_operational_state == TetheringOperationalState.ON:
        await tethering_manager.stop_tethering_async()
        print("Hotspot turned off")


def hotspot_on():
    asyncio.run(set_hotspot_state(True))
    os.system("start ms-settings:network-mobilehotspot")


def hotspot_off():
    asyncio.run(set_hotspot_state(False))
    os.system("start ms-settings:network-mobilehotspot")


def set_nearby_share(state):
    registry_path = r"Software\Microsoft\Windows\CurrentVersion\CDP"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NearShareChannelUserAuthzPolicy", 0, winreg.REG_DWORD, state)
        winreg.SetValueEx(key, "CdpSessionUserAuthzPolicy", 0, winreg.REG_DWORD, state)
        winreg.SetValueEx(key, "BluetoothLastDisabledNearShare", 0, winreg.REG_DWORD, state)
        winreg.CloseKey(key)
        print(f"Nearby Share set to {state}")
    except Exception as exc:
        print(f"Error updating registry: {exc}")


def airplane_mode():
    try:
        os.system("start ms-settings:network-airplanemode")
    except Exception:
        print("Unable to open airplane mode")


def stop_gesture():
    global stop_gesture_flag
    stop_gesture_flag = True
    print("[LOG] Gesture control stopped")


def run():
    global stop_gesture_flag
    stop_gesture_flag = False

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[LOG] Unable to open camera")
        return

    prev_x, prev_y = 0, 0
    smooth = 7

    prev_vol_y = None
    prev_bright_x = None
    prev_scroll_y = None

    last_action = 0
    last_scroll_time = 0

    gesture_count = 0
    prev_gesture = None

    min_dist = 0.10
    max_dist = 0.55

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.8,
    ) as hands:
        while not stop_gesture_flag:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            gesture_text = ""
            scroll_active = False
            color = (0, 255, 0)

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                h, w, _ = frame.shape
                x = int(hand.landmark[8].x * w)
                y = int(hand.landmark[8].y * h)
                mx = int(hand.landmark[12].x * w)
                my = int(hand.landmark[12].y * h)
                wrist_x = int(hand.landmark[0].x * w)
                wrist_y = int(hand.landmark[0].y * h)

                margin_x = 0.07 * w
                margin_y = 0.07 * h

                if x < margin_x:
                    gesture_text = "Move Hand Right"
                elif x > w - margin_x:
                    gesture_text = "Move Hand Left"
                elif y < margin_y:
                    gesture_text = "Move Hand Down"
                elif y > h - margin_y:
                    gesture_text = "Move Hand Up"
                else:
                    fingers = fingers_up(hand)
                    wrist = hand.landmark[0]
                    middle_tip = hand.landmark[12]
                    dist = sqrt((wrist.x - middle_tip.x) ** 2 + (wrist.y - middle_tip.y) ** 2)

                    if dist < min_dist:
                        gesture_text = "Move Hand Closer"
                    elif dist > max_dist:
                        gesture_text = "Move Hand Away"
                    else:
                        if fingers == prev_gesture:
                            gesture_count += 1
                        else:
                            gesture_count = 0
                        prev_gesture = fingers

                        if gesture_count >= 5:
                            recognized = False

                            if fingers == [0, 0, 0, 0, 0]:
                                recognized = True
                                gesture_text = "Control Mode"

                                if prev_vol_y is not None:
                                    dy = prev_vol_y - wrist_y
                                    set_volume(np.clip(get_volume() + dy / 300, 0, 1))

                                if prev_bright_x is not None:
                                    dx = x - prev_bright_x
                                    current_brightness = sbc.get_brightness()[0]
                                    set_brightness(np.clip(current_brightness + dx / 5, 0, 100))

                                prev_vol_y = wrist_y
                                prev_bright_x = x

                            else:
                                prev_vol_y = None
                                prev_bright_x = None

                                if fingers == [0, 1, 0, 0, 0]:
                                    recognized = True
                                    sx = np.interp(x, [0, w], [0, screen_w])
                                    sy = np.interp(y, [0, h], [0, screen_h])
                                    cx = prev_x + (sx - prev_x) / smooth
                                    cy = prev_y + (sy - prev_y) / smooth
                                    win32api.SetCursorPos((int(cx), int(cy)))
                                    prev_x, prev_y = cx, cy
                                    gesture_text = "Move"

                                elif fingers == [0, 1, 1, 0, 0]:
                                    recognized = True
                                    gesture_text = "Scroll"
                                    scroll_active = True

                                    if prev_scroll_y is None:
                                        prev_scroll_y = wrist_y
                                    else:
                                        dy = prev_scroll_y - wrist_y
                                        if abs(dy) > 5 and time.time() - last_scroll_time > 0.05:
                                            pyautogui.scroll(int(dy * 5))
                                            last_scroll_time = time.time()
                                        prev_scroll_y = wrist_y

                                elif fingers == [0, 1, 0, 0, 1]:
                                    recognized = True
                                    if time.time() - last_action > 1:
                                        pyautogui.click()
                                        gesture_text = "Left Click"
                                        last_action = time.time()

                                elif fingers == [1, 0, 0, 0, 1]:
                                    recognized = True
                                    if time.time() - last_action > 1:
                                        pyautogui.rightClick()
                                        gesture_text = "Right Click"
                                        last_action = time.time()

                                elif fingers == [0, 1, 1, 1, 0]:
                                    recognized = True
                                    dist_zoom = sqrt((x - mx) ** 2 + (y - my) ** 2)
                                    if time.time() - last_action > 1:
                                        if dist_zoom > 80:
                                            pyautogui.hotkey("ctrl", "+")
                                        elif dist_zoom < 30:
                                            pyautogui.hotkey("ctrl", "-")
                                        gesture_text = "Zoom"
                                        last_action = time.time()

                                elif fingers == [0, 0, 0, 0, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        pyautogui.hotkey("alt", "f4")
                                        gesture_text = "Close Window"
                                        last_action = time.time()

                                elif fingers == [1, 1, 1, 0, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        pyautogui.screenshot().save(
                                            f"screenshot_{int(time.time())}.png"
                                        )
                                        gesture_text = "Screenshot"
                                        last_action = time.time()

                                elif fingers == [1, 0, 0, 0, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        os.system("start chrome")
                                        gesture_text = "Chrome"
                                        last_action = time.time()

                                elif fingers == [0, 0, 0, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        os.system("start calc")
                                        gesture_text = "Calculator"
                                        last_action = time.time()

                                elif fingers == [1, 1, 0, 0, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        os.system("notepad")
                                        gesture_text = "Notepad"
                                        last_action = time.time()

                                elif fingers == [1, 1, 1, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        os.system("start ms-settings:")
                                        gesture_text = "Settings"
                                        last_action = time.time()

                                elif fingers == [0, 1, 1, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        pyautogui.hotkey("alt", "tab")
                                        gesture_text = "Alt Tab"
                                        last_action = time.time()

                                elif fingers == [1, 1, 0, 0, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        bluetooth_on()
                                        gesture_text = "Bluetooth On"
                                        last_action = time.time()

                                elif fingers == [0, 0, 1, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        bluetooth_off()
                                        gesture_text = "Bluetooth Off"
                                        last_action = time.time()

                                elif fingers == [1, 1, 1, 1, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        airplane_mode()
                                        gesture_text = "Airplane Mode"
                                        last_action = time.time()

                                elif fingers == [1, 0, 1, 0, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        wifi_on()
                                        gesture_text = "WiFi On"
                                        last_action = time.time()

                                elif fingers == [0, 1, 0, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        wifi_off()
                                        gesture_text = "WiFi Off"
                                        last_action = time.time()

                                elif fingers == [1, 1, 0, 1, 0]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        hotspot_on()
                                        gesture_text = "Hotspot On"
                                        last_action = time.time()

                                elif fingers == [0, 0, 1, 0, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        hotspot_off()
                                        gesture_text = "Hotspot Off"
                                        last_action = time.time()

                                elif fingers == [1, 0, 1, 1, 1]:
                                    recognized = True
                                    if time.time() - last_action > 2:
                                        stop_gesture()
                                        gesture_text = "Exit Gesture Mode"
                                        last_action = time.time()

                                if not recognized:
                                    gesture_text = "Unknown Gesture"
                        else:
                            gesture_text = "Hold Gesture Steady"

            if not scroll_active:
                prev_scroll_y = None

            if gesture_text in {
                "Move Hand Right",
                "Move Hand Left",
                "Move Hand Down",
                "Move Hand Up",
                "Move Hand Closer",
                "Move Hand Away",
                "Unknown Gesture",
            }:
                color = (0, 0, 255)

            cv2.putText(
                frame,
                gesture_text,
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2,
            )
            cv2.imshow("Virtual Mouse", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("x") or key == 27:
                stop_gesture_flag = True
                break

            if cv2.getWindowProperty("Virtual Mouse", cv2.WND_PROP_VISIBLE) < 1:
                stop_gesture_flag = True
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
