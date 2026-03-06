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

    def open_help(self):
        screen_w, screen_h = pyautogui.size()
        webview.create_window("Help", "ui/help.html", width=screen_w, height=screen_h)

if __name__ == "__main__":
    print("started")
    api = API()
    print("window started")
    screen_w, screen_h = pyautogui.size()
    webview.create_window(
        "Aura-Ctrl",
        "ui/index.html",
        js_api=api,
        width=screen_w,
        height=screen_h
    )
    webview.start()
