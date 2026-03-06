import speech_recognition as sr
import pyautogui
import os
import time
import pyttsx3
import subprocess
import google.generativeai as genai
import pygetwindow as gw
import ctypes
from ppt_controller import PPTController
import screen_brightness_control as sbc
import importlib

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 140)
engine.setProperty('volume', 1)

pyautogui.FAILSAFE = False

ppt = PPTController()
current_file = None



# ===================== WIFI CONTROL (REAL TOGGLE) =====================

def wifi_off():
    try:
        os.system("netsh wlan disconnect")
        speak_status("WiFi turned off")
    except:
        speak_status("Unable to turn WiFi off")


def wifi_on():
    try:
        # This reconnects automatically to saved network
        os.system("netsh wlan connect")
        speak_status("WiFi turned on")
    except:
        speak_status("Unable to turn WiFi on")



# ===================== SCREENSHOT CONTROL =====================

def take_screenshot():
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)

        speak_status(f"Screenshot saved as {filename}")
    except Exception as e:
        speak_status("Failed to take screenshot")

# ===================== APP ALIAS MAPPING =====================

aliases = {
    # Browsers
    "chrome": "chrome",
    "edge": "msedge",
    "firefox": "firefox",

    # Office Apps
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",

    # System Apps
    "file explorer": "explorer",
    "explorer": "explorer",
    "this pc": "explorer",
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
    "command prompt": "cmd",
    "cmd": "cmd",
    "powershell": "powershell",
    "terminal": "wt",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings": "ms-settings:",

    # Utilities
    "calculator": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "snipping tool": "snippingtool",
    "camera": "microsoft.windows.camera:",

    # Development
    "vscode": "code",
    "vs code": "code",
    "visual studio": "devenv",

    # Communication
    "whatsapp": "WhatsApp",
    "telegram": "telegram",
    "zoom": "zoom",
    "teams": "ms-teams:",

    # Media
    "media player": "wmplayer",
    "vlc": "vlc",
    "spotify": "spotify"
}
# ===================== WINDOW MANAGEMENT =====================

def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_user_windows():
    windows = []
    for w in gw.getAllWindows():
        if (
            w.title
            and w.visible
            and not w.title.lower().startswith("program manager")
            and not w.title.lower().startswith("settings")
            and not w.title.lower().startswith("task switching")
        ):
            windows.append(w)
    return windows


def get_two_windows():
    active = gw.getActiveWindow()
    if not active or not active.title:
        return None, None

    all_windows = get_user_windows()
    second = None

    for w in all_windows:
        if w != active:
            second = w
            break

    return active, second


def safe_restore(window):
    try:
        if window.isMinimized:
            window.restore()
            time.sleep(0.3)

        if window.isMaximized:
            window.restore()
            time.sleep(0.3)
    except:
        pass


def arrange_left_right():
    try:
        screen_width, screen_height = get_screen_size()
        win1, win2 = get_two_windows()

        if not win1 or not win2:
            speak_status("Need at least two open applications")
            return

        safe_restore(win1)
        safe_restore(win2)

        win1.moveTo(0, 0)
        win1.resizeTo(screen_width // 2, screen_height)

        win2.moveTo(screen_width // 2, 0)
        win2.resizeTo(screen_width // 2, screen_height)

        speak_status("Windows arranged left and right")

    except Exception as e:
        speak_status(f"Tiling error: {e}")


def arrange_top_bottom():
    try:
        screen_width, screen_height = get_screen_size()
        win1, win2 = get_two_windows()

        if not win1 or not win2:
            speak_status("Need at least two open applications")
            return

        safe_restore(win1)
        safe_restore(win2)

        win1.moveTo(0, 0)
        win1.resizeTo(screen_width, screen_height // 2)

        win2.moveTo(0, screen_height // 2)
        win2.resizeTo(screen_width, screen_height // 2)

        speak_status("Windows arranged top and bottom")

    except Exception as e:
        speak_status(f"Tiling error: {e}")


def swap_active_windows():
    try:
        win1, win2 = get_two_windows()

        if not win1 or not win2:
            speak_status("Need at least two open applications")
            return

        safe_restore(win1)
        safe_restore(win2)

        x1, y1 = win1.topleft
        w1, h1 = win1.size

        x2, y2 = win2.topleft
        w2, h2 = win2.size

        win1.moveTo(x2, y2)
        win1.resizeTo(w2, h2)

        win2.moveTo(x1, y1)
        win2.resizeTo(w1, h1)

        speak_status("Windows swapped successfully")

    except Exception as e:
        speak_status(f"Swap error: {e}")

# ===================== IMPROVED UNIVERSAL APP CONTROL =====================

def find_window_by_name(app_name):
    app_name = app_name.lower().strip()

    for w in gw.getAllWindows():
        if w.title and app_name in w.title.lower():
            return w

    return None
    


def minimize_app(app_name):
    time.sleep(0.5)  # Allow window to load
    win = find_window_by_name(app_name)

    if win:
        try:
            win.minimize()
            speak_status(f"{app_name} minimized")
        except Exception as e:
            speak_status(f"Could not minimize {app_name}")
    else:
        speak_status(f"{app_name} not found")


def maximize_app(app_name):
    time.sleep(0.5)
    win = find_window_by_name(app_name)

    if win:
        try:
            if win.isMinimized:
                win.restore()
                time.sleep(0.3)
            win.maximize()
            speak_status(f"{app_name} maximized")
        except Exception:
            speak_status(f"Could not maximize {app_name}")
    else:
        speak_status(f"{app_name} not found")


def close_app(app_name):
    time.sleep(0.5)
    win = find_window_by_name(app_name)

    if win:
        try:
            win.close()
            speak_status(f"{app_name} closed")
        except Exception:
            speak_status(f"Could not close {app_name}")
    else:
        speak_status(f"{app_name} not found")


def open_app(app_name):
    original_name = app_name.strip()
    app_name = app_name.lower().strip()

    # Apply alias mapping
    app_name = aliases.get(app_name, app_name)

    try:
        subprocess.Popen(
            f'start "" {app_name}',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        speak_status(f"Opening {original_name}")
    except:
        speak_status(f"Application {original_name} not found")

# ===================== BRIGHTNESS CONTROL =====================

def increase_brightness():
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(min(current + 10, 100))
        speak_status("Brightness increased")
    except:
        speak_status("Brightness control not supported")


def decrease_brightness():
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(max(current - 10, 0))
        speak_status("Brightness decreased")
    except:
        speak_status("Brightness control not supported")


def set_brightness_level(level):
    try:
        level = max(0, min(100, level))
        sbc.set_brightness(level)
        speak_status(f"Brightness set to {level} percent")
    except:
        speak_status("Brightness control not supported")

# ===================== BASIC FUNCTIONS =====================

def speak_status(text):
    print("[INFO]:", text)
    importlib.reload(pyttsx3)  # Hard reset of the library state
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak_status("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        command = command.lower()
        speak_status(f"You said: {command}")
        return command
    except:
        speak_status("Speech recognition error")
        return ""

# ===================== COMMAND EXECUTION =====================

def execute_command(command):

    if "arrange left right" in command:
        arrange_left_right()

    elif "arrange top bottom" in command:
        arrange_top_bottom()

    elif "swap windows" in command:
        swap_active_windows()

    elif command.startswith("open "):
        app_name = command.replace("open ", "").strip()
        open_app(app_name)

    elif command.startswith("minimise "):
        app_name = command.replace("minimise ", "").strip()
        minimize_app(app_name)

    elif command.startswith("maximize "):
        app_name = command.replace("maximize ", "").strip()
        maximize_app(app_name)

    elif command.startswith("close "):
        app_name = command.replace("close ", "").strip()
        close_app(app_name)

    elif "create new presentation" in command:
        ppt.create_new_presentation()
        speak_status("New presentation created")

    elif "create slide about" in command:
        topic = command.replace("create slide about", "").strip()
        if topic:
            ppt.add_slide(topic)
        else:
            speak_status("Please specify a topic")

    elif "start presentation" in command:
        ppt.start_slideshow()
        speak_status("Presentation started")

    elif "next slide" in command:
        ppt.next_slide()
        speak_status("Next slide")

    elif "previous slide" in command:
        ppt.previous_slide()
        speak_status("Previous slide")

    elif "stop presentation" in command:
        ppt.stop_slideshow()
        speak_status("Presentation stopped")

    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak_status("Volume increased")

    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak_status("Volume decreased")

    elif "mute volume" in command:
        pyautogui.press("volumemute")
        speak_status("Volume muted")

    elif "brightness up" in command:
        increase_brightness()

    elif "brightness down" in command:
        decrease_brightness()

    elif "set brightness to" in command:
        try:
            level = int(command.replace("set brightness to", "").strip().replace("percent",""))
            set_brightness_level(level)
        except:
            speak_status("Please specify brightness level")

    elif "mouse left" in command:
        pyautogui.moveRel(-100, 0, duration=0.2)
        speak_status("Mouse moved left")

    elif "mouse right" in command:
        pyautogui.moveRel(100, 0, duration=0.2)
        speak_status("Mouse moved right")

    elif "mouse up" in command:
        pyautogui.moveRel(0, -100, duration=0.2)
        speak_status("Mouse moved up")

    elif "mouse down" in command:
        pyautogui.moveRel(0, 100, duration=0.2)
        speak_status("Mouse moved down")
        
    elif "double click" in command:
        pyautogui.doubleClick()
        speak_status("Double click performed")

    elif "click" in command:
        pyautogui.click()
        speak_status("Click performed")

    elif "scroll up" in command:
        pyautogui.scroll(500)
        speak_status("Scrolled up")

    elif "scroll down" in command:
        pyautogui.scroll(-500)
        speak_status("Scrolled down")

    elif "wifi on" in command:
        wifi_on()

    elif "wi-fi off" in command:
        wifi_off()

    elif "take screenshot" in command:
        take_screenshot()

    elif "exit" in command or "stop" in command:
        speak_status("Exiting program...")
        return False

    return True

# ===================== MAIN =====================

def main():
    speak_status("Voice Control System Started")
    print("started")
    # engine.say("Hello. Aura Control activated.")
    # engine.runAndWait()

    # time.sleep(1)

    running = True
    while running:
        print("listenn START")
        command = listen_command()
        if command:
            running = execute_command(command)

if __name__ == "__main__":
    main()