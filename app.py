import webview
import gesture
import voice
import threading
import pyautogui

class API:

    def __init__(self):
        self.gesture_running = False
        self.voice_running = False

    def start_gesture(self):
        if not self.gesture_running:
            self.gesture_running = True
            threading.Thread(target=gesture.run).start()

    def stop_gesture(self):
        self.gesture_running = False
        gesture.stop_flag = True   # you must add this in gesture.py

    def start_voice(self):
        if not self.voice_running:
            self.voice_running = True
            threading.Thread(target=voice.main).start()

    def stop_voice(self):
        self.voice_running = False
        voice.stop_flag = True   # add in voice.py

    def start_both(self):
        self.start_gesture()
        self.start_voice()

    def stop_both(self):
        self.stop_gesture()
        self.stop_voice()

    def open_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Help",
            "ui/help.html",
            js_api=self,
            width=screen_w,
            height=screen_h
        )

    def open_gesture_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Gesture Help",
            "ui/help_gesture.html",
            js_api=self,
            width=screen_w,
            height=screen_h
        )

    def open_voice_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Voice Help",
            "ui/help_voice.html",
            js_api=self,
            width=screen_w,
            height=screen_h
        )

    def close_window(self):
        webview.windows[-1].destroy()


if __name__ == "__main__":
    print("started")

    api = API()

    screen_w, screen_h = pyautogui.size()

    webview.create_window(
        "Aura-Ctrl",
        "ui/index.html",
        js_api=api,
        width=screen_w,
        height=screen_h
    )

    webview.start()
