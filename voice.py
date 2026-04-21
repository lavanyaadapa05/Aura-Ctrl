# ============================================================
#                     AURA CTRL - VOICE MODULE
#  Handles all voice-based system control commands for Aura.
#  Uses speech recognition, text-to-speech, and system APIs.
# ============================================================

# ===================== IMPORTS =====================

import speech_recognition as sr
import pyautogui
import os
import time
import pyttsx3
import subprocess
import webbrowser
import socket
import shutil
import asyncio
import winreg
import ctypes
import datetime
import psutil
from dotenv import load_dotenv


import google.generativeai as genai
import pygetwindow as gw
import screen_brightness_control as sbc

from winsdk.windows.devices import radios
from winsdk.windows.networking.connectivity import NetworkInformation
from winsdk.windows.networking.networkoperators import NetworkOperatorTetheringManager, TetheringOperationalState

from ppt_controller import PPTController

# ===================== GLOBAL SETTINGS =====================

# Disable PyAutoGUI fail-safe (prevents corner-of-screen crash)
pyautogui.FAILSAFE = False

# Initialize PowerPoint controller
ppt = PPTController()

# Tracks the currently active file for code generation/execution
current_file = None

# Configure Gemini AI for code generation
# Load local environment variables from .env
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")


# ============================================================
#                   SECTION 1: TTS & SPEECH
#  Core voice input/output utilities used throughout the file.
# ============================================================

def speak_status(text):
    """Prints and speaks a status message aloud using TTS."""
    print("[INFO]:", text)
    engine.say(text)
    engine.runAndWait()


def listen_command():
    """
    Listens from the microphone and returns the recognized command as a string.
    Returns an empty string if recognition fails.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        speak_status("Listening...")
        audio = recognizer.listen(source)
        print("listen step done")

    try:
        command = recognizer.recognize_google(audio)
        command = command.lower()
        speak_status(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        speak_status("Could not understand audio")
        return ""
    except sr.RequestError:
        speak_status("Speech service error")
        return ""


# ============================================================
#                SECTION 2: SYSTEM INFORMATION
#  Reads and reports system stats like battery, CPU, memory, etc.
# ============================================================

def battery_status():
    """Reports the current battery percentage and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "plugged in" if battery.power_plugged else "discharging"
            speak_status(f"Battery is at {percent} percent and it is {plugged}")
        else:
            speak_status("Battery information is not available on this device")
    except Exception:
        speak_status("Unable to check battery status")


def system_time():
    """Reads and speaks the current system time in 12-hour format."""
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak_status(f"The current system time is {now}")


def storage_usage():
    """Reports C: drive usage and remaining free space."""
    try:
        total, used, free = shutil.disk_usage("C:/")
        percent_used = (used / total) * 100
        speak_status(f"Storage usage is at {percent_used:.1f} percent. You have {free // (2**30)} gigabytes free.")
    except Exception:
        speak_status("Unable to calculate storage usage")


def internet_status():
    """Checks internet connectivity by attempting a connection to Google DNS."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        speak_status("The internet is connected and stable")
    except OSError:
        speak_status("The internet appears to be disconnected")


def cpu_usage():
    """Reports current CPU usage percentage (sampled over 1 second for accuracy)."""
    usage = psutil.cpu_percent(interval=1)
    speak_status(f"Current CPU usage is {usage} percent")


def memory_usage():
    """Reports current RAM usage percentage and available memory."""
    try:
        mem = psutil.virtual_memory()
        speak_status(f"Memory usage is {mem.percent} percent. {mem.available // (1024**3)} gigabytes available.")
    except Exception:
        speak_status("Unable to read memory usage")


def system_uptime():
    """Calculates and reports how long the system has been running."""
    try:
        boot = datetime.datetime.fromtimestamp(psutil.boot_time())
        now = datetime.datetime.now()
        uptime = now - boot
        hours = uptime.seconds // 3600
        speak_status(f"System has been running for {uptime.days} days and {hours} hours")
    except Exception:
        speak_status("Unable to calculate uptime")


def ip_address():
    """Retrieves and speaks the local system IP address."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        speak_status(f"Your system IP address is {ip}")
    except Exception:
        speak_status("Unable to determine IP address")


# ============================================================
#           SECTION 3: CONNECTIVITY (WiFi / Bluetooth / Hotspot)
#  Controls network-related features like WiFi, Bluetooth,
#  Mobile Hotspot, Nearby Share, and Airplane Mode.
# ============================================================

# -------------------- WiFi --------------------

def wifi_on():
    """Reconnects to the previously saved WiFi network."""
    try:
        os.system("netsh wlan connect")
        speak_status("SudhaRani WiFi turned on")
    except Exception:
        speak_status("Unable to turn WiFi on")


def wifi_off():
    """Disconnects from the current WiFi network."""
    try:
        os.system("netsh wlan disconnect")
        speak_status("WiFi turned off")
    except Exception:
        speak_status("Unable to turn WiFi off")


# -------------------- Bluetooth --------------------

async def set_bluetooth_state(turn_on):
    """
    Async function that toggles Bluetooth ON or OFF using Windows Radio API.
    Iterates all system radios and targets the Bluetooth radio.
    """
    all_radios = await radios.Radio.get_radios_async()

    for radio in all_radios:
        if radio.kind == radios.RadioKind.BLUETOOTH:
            if turn_on:
                await radio.set_state_async(radios.RadioState.ON)
                speak_status("Bluetooth turned on")
            else:
                await radio.set_state_async(radios.RadioState.OFF)
                speak_status("Bluetooth turned off")


def bluetooth_on():
    """Turns Bluetooth ON and opens the action center."""
    asyncio.run(set_bluetooth_state(True))
    os.system("start ms-actioncenter:controlcenter/bluetooth")


def bluetooth_off():
    """Turns Bluetooth OFF and opens the action center."""
    asyncio.run(set_bluetooth_state(False))
    os.system("start ms-actioncenter:controlcenter/bluetooth")


# -------------------- Mobile Hotspot --------------------

async def set_hotspot_state(turn_on):
    """
    Async function that toggles Mobile Hotspot ON or OFF.
    Uses Windows tethering API tied to the active connection profile.
    """
    connection_profile = NetworkInformation.get_internet_connection_profile()

    if not connection_profile:
        speak_status("No active internet connection found to share.")
        return

    tethering_manager = NetworkOperatorTetheringManager.create_from_connection_profile(connection_profile)

    if turn_on:
        if tethering_manager.tethering_operational_state == TetheringOperationalState.OFF:
            result = await tethering_manager.start_tethering_async()
            speak_status("Hotspot Turned ON")
        else:
            speak_status("Hotspot is already ON")
    else:
        if tethering_manager.tethering_operational_state == TetheringOperationalState.ON:
            result = await tethering_manager.stop_tethering_async()
            speak_status("Hotspot Turned OFF")
        else:
            speak_status("Hotspot is already OFF")


def hotspot_on():
    """Turns Mobile Hotspot ON and opens hotspot settings."""
    asyncio.run(set_hotspot_state(True))
    os.system("start ms-settings:network-mobilehotspot")


def hotspot_off():
    """Turns Mobile Hotspot OFF and opens hotspot settings."""
    asyncio.run(set_hotspot_state(False))
    os.system("start ms-settings:network-mobilehotspot")


# -------------------- Nearby Share --------------------

def set_nearby_share(state):
    """
    Sets the Windows Nearby Share state via registry (no admin required).
    state: 0 = Off | 1 = My Devices Only | 2 = Everyone Nearby
    """
    registry_path = r"Software\Microsoft\Windows\CurrentVersion\CDP"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)

        # These are the three registry keys Windows uses to control Nearby Share
        winreg.SetValueEx(key, "NearShareChannelUserAuthzPolicy", 0, winreg.REG_DWORD, state)
        winreg.SetValueEx(key, "CdpSessionUserAuthzPolicy", 0, winreg.REG_DWORD, state)
        winreg.SetValueEx(key, "BluetoothLastDisabledNearShare", 0, winreg.REG_DWORD, state)

        winreg.CloseKey(key)

        status_map = {0: "Off", 1: "My Devices Only", 2: "Everyone"}
        speak_status(f"Nearby Share set to: {status_map.get(state)}")
    except Exception as e:
        speak_status(f"Error updating registry: {e}")


# -------------------- Airplane Mode --------------------

def airplane_mode():
    """Opens the Windows Airplane Mode settings page."""
    try:
        os.system("start ms-settings:network-airplanemode")
        speak_status("Opening airplane mode settings")
    except Exception:
        speak_status("Unable to open airplane mode")


# ============================================================
#                  SECTION 4: DISPLAY CONTROL
#  Controls screen brightness via the sbc (screen-brightness-control) library.
# ============================================================

def increase_brightness():
    """Increases screen brightness by 10%."""
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(min(current + 10, 100))
        speak_status("Brightness increased")
    except Exception:
        speak_status("Brightness control not supported")


def decrease_brightness():
    """Decreases screen brightness by 10%."""
    try:
        current = sbc.get_brightness(display=0)[0]
        sbc.set_brightness(max(current - 10, 0))
        speak_status("Brightness decreased")
    except Exception:
        speak_status("Brightness control not supported")


def set_brightness_level(level):
    """Sets brightness to a specific level (0–100)."""
    try:
        level = max(0, min(100, level))
        sbc.set_brightness(level)
        speak_status(f"Brightness set to {level} percent")
    except Exception:
        speak_status("Brightness control not supported")


# ============================================================
#               SECTION 5: WINDOW MANAGEMENT
#  Handles tiling, snapping, swapping, and moving app windows.
# ============================================================

def get_screen_size():
    """Returns the (width, height) of the primary screen using Windows API."""
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_user_windows():
    """
    Returns a list of all visible, non-system windows currently open.
    Filters out Program Manager, Settings, and Task Switcher overlays.
    """
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
    """
    Returns the currently active window and the next available window.
    Used for tiling/swapping operations that require two windows.
    """
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
    """
    Restores a window from minimized or maximized state before repositioning.
    Prevents errors when resizing/moving snapped or minimized windows.
    """
    try:
        if window.isMinimized:
            window.restore()
            time.sleep(0.3)

        if window.isMaximized:
            window.restore()
            time.sleep(0.3)
    except Exception:
        pass


def arrange_left_right():
    """Tiles the two active windows side by side (left / right split)."""
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
    """Tiles the two active windows stacked vertically (top / bottom split)."""
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
    """Swaps the positions and sizes of the two currently active windows."""
    try:
        win1, win2 = get_two_windows()

        if not win1 or not win2:
            speak_status("Need at least two open applications")
            return

        safe_restore(win1)
        safe_restore(win2)

        # Store original positions and sizes
        x1, y1 = win1.topleft
        w1, h1 = win1.size

        x2, y2 = win2.topleft
        w2, h2 = win2.size

        # Swap them
        win1.moveTo(x2, y2)
        win1.resizeTo(w2, h2)

        win2.moveTo(x1, y1)
        win2.resizeTo(w1, h1)

        speak_status("Windows swapped successfully")

    except Exception as e:
        speak_status(f"Swap error: {e}")


# ============================================================
#                SECTION 6: APPLICATION CONTROL
#  Opens, closes, minimizes, and maximizes applications by name.
#  Uses an alias map for common app name variations.
# ============================================================

# Alias map: spoken name → executable/command Windows understands
aliases = {
    # Browsers
    "chrome":           "chrome",
    "edge":             "msedge",
    "firefox":          "firefox",

    # Office Apps
    "word":             "winword",
    "excel":            "excel",
    "powerpoint":       "powerpnt",
    "outlook":          "outlook",

    # System Apps
    "file explorer":    "explorer",
    "explorer":         "explorer",
    "this pc":          "explorer",
    "microsoft store":  "ms-windows-store:",
    "store":            "ms-windows-store:",
    "command prompt":   "cmd",
    "cmd":              "cmd",
    "powershell":       "powershell",
    "terminal":         "wt",
    "task manager":     "taskmgr",
    "control panel":    "control",
    "settings":         "ms-settings:",

    # Utilities
    "calculator":       "calc",
    "notepad":          "notepad",
    "paint":            "mspaint",
    "snipping tool":    "snippingtool",
    "camera":           "microsoft.windows.camera:",

    # Development
    "vscode":           "code",
    "vs code":          "code",
    "visual studio":    "devenv",

    # Communication
    "whatsapp":         "WhatsApp",
    "telegram":         "telegram",
    "zoom":             "zoom",
    "teams":            "ms-teams:",

    # Media
    "media player":     "wmplayer",
    "vlc":              "vlc",
    "spotify":          "spotify"
}


def find_window_by_name(app_name):
    """
    Searches all open windows for one whose title contains the given name.
    Returns the window object if found, or None if not found.
    """
    app_name = app_name.lower().strip()

    for w in gw.getAllWindows():
        if w.title and app_name in w.title.lower():
            return w

    return None


def open_app(app_name):
    """
    Launches an application by name.
    Applies alias mapping to handle common spoken variations.
    """
    original_name = app_name.strip()
    app_name = app_name.lower().strip()

    # Resolve alias if available
    app_name = aliases.get(app_name, app_name)

    try:
        subprocess.Popen(
            f'start "" {app_name}',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        speak_status(f"Opening {original_name}")
    except Exception:
        speak_status(f"Application {original_name} not found")


def minimize_app(app_name):
    """Minimizes the window whose title matches the given app name."""
    time.sleep(0.5)  # Allow window to fully load before targeting
    win = find_window_by_name(app_name)

    if win:
        try:
            win.minimize()
            speak_status(f"{app_name} minimized")
        except Exception:
            speak_status(f"Could not minimize {app_name}")
    else:
        speak_status(f"{app_name} not found")


def maximize_app(app_name):
    """Maximizes the window whose title matches the given app name."""
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
    """Closes the window whose title matches the given app name."""
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


def open_vscode():
    """
    Opens VS Code using multiple fallback strategies:
    1. Check if 'code' is in system PATH
    2. Check known install directories
    3. Fallback: os.system('start code')
    """
    try:
        # Method 1: Check if 'code' exists in PATH
        if shutil.which("code"):
            subprocess.Popen(["code", "-n"])
            speak_status("VS Code opened")
            return True

        # Method 2: Check common install locations
        possible_paths = [
            os.path.join(os.environ["LOCALAPPDATA"], r"Programs\Microsoft VS Code\Code.exe"),
            os.path.join(os.environ["PROGRAMFILES"], r"Microsoft VS Code\Code.exe"),
            os.path.join(os.environ["PROGRAMFILES(X86)"], r"Microsoft VS Code\Code.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                subprocess.Popen([path, "-n"])
                speak_status("VS Code opened")
                return True

        # Method 3: OS-level fallback
        os.system("start code")
        speak_status("VS Code opened")

    except Exception:
        speak_status("VS Code not found on system")


# ============================================================
#                   SECTION 7: MEDIA CONTROL
#  Handles music playback via YouTube and volume/screenshot controls.
# ============================================================

def play_music(song=None):
    """
    Plays music on YouTube.
    If a song name is given, searches YouTube for it.
    Otherwise, opens YouTube Music directly.
    """
    try:
        if song:
            url = f"https://www.youtube.com/results?search_query={song}+song"
            webbrowser.open(url)
            speak_status(f"Playing {song} on YouTube")
        else:
            webbrowser.open("https://music.youtube.com")
            speak_status("Opening YouTube Music")
    except Exception:
        speak_status("Unable to play music")


def take_screenshot():
    """
    Captures a screenshot and saves it in the current directory
    with a timestamp-based filename (e.g., screenshot_20250310_153000.png).
    """
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)

        speak_status(f"Screenshot saved as {filename}")
    except Exception:
        speak_status("Failed to take screenshot")


# ============================================================
#              SECTION 8: CODE GENERATION & EXECUTION
#  Uses Gemini AI to generate Python code from voice descriptions,
#  writes it to a file, and executes it via subprocess.
# ============================================================

def generate_code(description):
    """
    Sends a prompt to Gemini AI and returns clean, executable Python code.
    Strips any markdown code fences from the response if present.
    """
    try:
        prompt = f"""
        Generate clean, executable Python code.
        Only return the code.
        No explanations.
        Task: Write a Python program to {description}
        """

        response = model.generate_content(prompt)
        code = response.text.strip()

        # Strip markdown code blocks if Gemini wraps the output
        if code.startswith("```"):
            code = code.split("```")[1]
            if code.startswith("python"):
                code = code[6:].strip()

        return code

    except Exception as e:
        speak_status(f"Gemini error: {e}")
        return None


# ============================================================
#                  SECTION 9: COMMAND DISPATCHER
#  Central routing function that maps voice commands to actions.
#  All recognized commands are handled here in logical order.
# ============================================================

def execute_command(command):
    """
    Parses the recognized voice command and routes it to the
    appropriate handler function. Returns True to keep running,
    or False to stop the loop.
    """
    global current_file

    # -------------------- Window Management --------------------
    if "arrange left right" in command:
        arrange_left_right()

    elif "arrange top bottom" in command:
        arrange_top_bottom()

    elif "swap windows" in command:
        swap_active_windows()

    # -------------------- App Control --------------------
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

    elif "open vs code" in command:
        open_vscode()

    # -------------------- PowerPoint Control --------------------
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

    # -------------------- Volume Control --------------------
    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak_status("Volume increased")

    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak_status("Volume decreased")

    elif "mute volume" in command:
        pyautogui.press("volumemute")
        speak_status("Volume muted")

    # -------------------- Brightness Control --------------------
    elif "brightness up" in command:
        increase_brightness()

    elif "brightness down" in command:
        decrease_brightness()

    elif "set brightness to" in command:
        try:
            level = int(command.replace("set brightness to", "").strip().replace("percent", ""))
            set_brightness_level(level)
        except Exception:
            speak_status("Please specify brightness level")

    # -------------------- Mouse Control --------------------
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

    # -------------------- Scroll Control --------------------
    elif "scroll up" in command:
        pyautogui.scroll(500)
        speak_status("Scrolled up")

    elif "scroll down" in command:
        pyautogui.scroll(-500)
        speak_status("Scrolled down")

    # -------------------- Connectivity --------------------
    elif "wifi on"  in command:
        wifi_on()

    elif "wi-fi off" in command:
        wifi_off()

    elif "bluetooth on" in command:
        bluetooth_on()

    elif "bluetooth off" in command:
        bluetooth_off()

    elif "hotspot on" in command or "mobile hotspot on" in command:
        hotspot_on()

    elif "hotspot off" in command or "mobile hotspot off" in command:
        hotspot_off()

    elif "nearby share off" in command:
        set_nearby_share(0)
        os.system("start ms-settings:crossdevice")

    elif "nearby share my devices" in command:
        set_nearby_share(1)
        os.system("start ms-settings:crossdevice")

    elif "nearby share everyone" in command or "nearby share on" in command:
        set_nearby_share(2)
        os.system("start ms-settings:crossdevice")

    elif "airplane mode" in command:
        airplane_mode()

    # -------------------- System Info --------------------
    elif "battery status" in command or "battery level" in command:
        battery_status()

    elif "system time" in command or "what time is it" in command:
        system_time()

    elif "storage usage" in command or "disk usage" in command:
        storage_usage()

    elif "internet status" in command or "check internet" in command:
        internet_status()

    elif "cpu usage" in command or "processor usage" in command:
        cpu_usage()

    elif "memory usage" in command or "ram usage" in command:
        memory_usage()

    elif "ip address" in command:
        ip_address()

    elif "system uptime" in command:
        system_uptime()

    # -------------------- Media --------------------
    elif "take screenshot" in command:
        take_screenshot()

    elif command.startswith("play music"):
        song = command.replace("play music", "").strip()
        play_music(song)

    # -------------------- Code Generation & Execution --------------------
    elif "create new file as" in command:
        print("starting new file opening")
        try:
            filename = command.replace("create new file as", "").strip()
            filename = filename.replace(" ", "_") + ".py"

            # Create empty file
            with open(filename, "w"):
                pass

            # Open in VS Code
            subprocess.Popen(["code", filename])

            current_file = filename
            speak_status(f"File {filename} created")

        except Exception as e:
            speak_status(f"Error creating file: {e}")

    elif "write a program to" in command:
        description = command.replace("write a program to", "").strip()

        if not current_file:
            speak_status("Please create a file first")
            return True

        speak_status("Generating code")

        code = generate_code(description)

        if code:
            with open(current_file, "w", encoding="utf-8") as f:
                f.write(code)

            speak_status("Code written successfully")

            # Open the file in VS Code to show the result
            subprocess.Popen(["code", current_file])

    elif "execute code" in command:
        print("started execu")
        if not current_file:
            speak_status("No file to run")
            return True

        print("opening")
        try:
            process = subprocess.Popen(
                ["python", current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output, error = process.communicate()

            if error:
                print("ERROR:\n", error)
                speak_status("Error while executing code")
            else:
                print("OUTPUT:\n", output)
                speak_status("Code executed successfully")

        except Exception as e:
            speak_status(f"Execution error {e}")

    elif "close file" in command:
        current_file = None
        speak_status("File reference cleared")

    # -------------------- Exit --------------------
    elif "exit" in command or "stop" in command:
        speak_status("Exiting program...")
        return False

    return True


# ============================================================
#                     SECTION 10: MAIN ENTRY
#  Initializes the TTS engine, greets the user,
#  and starts the continuous voice command loop.
# ============================================================

def main():
    global engine

    # Initialize text-to-speech engine with a female voice at moderate speed
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)   # Index 1 = typically female voice
    engine.setProperty('rate', 140)              # Speaking speed (words per minute)
    engine.setProperty('volume', 1)              # Full volume

    speak_status("Voice Control System Started")
    print("started")
    engine.say("Hello. Aura Control activated.")
    engine.runAndWait()
    time.sleep(1)

    # Main voice command loop — keeps running until "exit" or "stop" is spoken
    running = True
    while running:
        print("listenn START")
        command = listen_command()
        if command:
            running = execute_command(command)


if __name__ == "__main__":
    main()
