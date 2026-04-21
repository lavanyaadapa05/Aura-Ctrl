#from curses import window

import webview
import gesture
import voice
import threading
import pyautogui

class API:

    def __init__(self):
        self.gesture_running = False
        self.voice_running = False
        #self._window = None

    def _gesture_thread(self):
        """Wrapper: runs gesture, then resets state and notifies UI."""
        try:
            gesture.run()
        finally:
            self.gesture_running = False  # 🔥 always reset
            gesture.stop_flag = True
            # Notify UI to reset button (handles window-close case)
            try:
                if webview.windows:
                    webview.windows[0].evaluate_js("resetGestureButton()")
            except Exception as e:
                print("Gesture UI reset error:", e)

    def _voice_thread(self):
        """Wrapper: runs voice, then resets state and notifies UI."""
        try:
            voice.main()
        finally:
            self.voice_running = False  # 🔥 always reset
            voice.stop_flag = True
            try:
                if self._window:
                    self._window.evaluate_js("resetVoiceButton()")
            except Exception:
                pass

    def start_gesture(self):
        if not self.gesture_running:
            self.gesture_running = True
            gesture.stop_flag = False  # 🔥 reset flag before starting
            threading.Thread(target=self._gesture_thread, daemon=True).start()
            #threading.Thread(target=gesture.run).start()

    def stop_gesture(self):
        self.gesture_running = False
        gesture.stop_flag = True   # you must add this in gesture.py
         # 🔥 Immediately update UI when stopped manually
        try:
            if webview.windows:
                webview.windows[0].evaluate_js("resetGestureButton()")
        except:
            pass

    def start_voice(self):
        if not self.voice_running:
            self.voice_running = True
            voice.stop_flag = False  # 🔥 reset flag before starting
            threading.Thread(target=self._voice_thread, daemon=True).start()
            #threading.Thread(target=voice.main, daemon=True).start()

    def stop_voice(self):
        self.voice_running = False
        voice.stop_flag = True   # add in voice.py
        try:
            if webview.windows:
                webview.windows[0].evaluate_js("resetVoiceButton()")
        except:
            pass

    def start_both(self):
        self.start_gesture()
        self.start_voice()

    def stop_both(self):
        self.stop_gesture()
        self.stop_voice()
         # 🔥 Reset BOTH button also
        try:
            if webview.windows:
                webview.windows[0].evaluate_js("resetBothButton()")
        except:
            pass

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

    window = webview.create_window(
        "Aura-Ctrl",
        "ui/index.html",
        js_api=api,
        width=screen_w,
        height=screen_h
    )
    api._window = window  # 🔥 store reference so threads can call evaluate_js

    webview.start()
