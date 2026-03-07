import webview
import gesture
import voice
import threading
import pyautogui

class API:

    def start_gesture(self):
        print("gesture")
        threading.Thread(target=gesture.run).start()

    def start_volume(self):
        print("volume")
        threading.Thread(target=voice.main).start()

    def start_both(self):
        print("gesture + voice")
        threading.Thread(target=gesture.run).start()
        threading.Thread(target=voice.main).start()

    def open_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Help",
            "ui/help.html",
            js_api=self,      # IMPORTANT
            width=screen_w,
            height=screen_h
        )

    def open_gesture_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Gesture Help",
            "ui/help_gesture.html",
            js_api=self,      # IMPORTANT
            width=screen_w,
            height=screen_h
        )

    def open_voice_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window(
            "Voice Help",
            "ui/help_voice.html",
            js_api=self,      # IMPORTANT
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
        js_api=api,        # API attached to main window
        width=screen_w,
        height=screen_h
    )

    webview.start()
