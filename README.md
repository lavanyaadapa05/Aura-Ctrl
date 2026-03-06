# Aura-Ctrl

Aura-Ctrl is a comprehensive computer control system that allows you to interact with your Windows PC using hand gestures and voice commands. Control your mouse, keyboard, applications, and system settings hands-free!

## Features

- **Gesture Control**: Control mouse cursor, clicks, scrolling, volume, brightness, and launch applications with hand gestures
- **Voice Control**: Execute commands through speech recognition for app management, window control, and system operations
- **PowerPoint Integration**: Create and control PowerPoint presentations with voice commands
- **Cross-Platform UI**: Modern web-based interface for easy access

## Prerequisites

- **Operating System**: Windows 10/11
- **Python**: Version 3.8 or higher
- **Camera**: Webcam for gesture control
- **Microphone**: For voice control
- **PowerPoint**: Microsoft PowerPoint (optional, for presentation features)

## Installation

### Step 1: Download and Extract
1. Download the Aura-Ctrl project files
2. Extract the ZIP file to a folder on your computer (e.g., `C:\Aura-Ctrl` or `Desktop\Aura-Ctrl`)

### Step 2: Install Python Dependencies
1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the extracted folder:
   ```
   cd C:\Path\To\Aura-Ctrl
   ```
   (Replace `C:\Path\To\Aura-Ctrl` with your actual folder path)

3. Install all required Python packages:
   ```
   pip install -r requirements.txt
   ```

   This will install the following packages:
   - opencv-python (computer vision)
   - mediapipe (hand tracking)
   - numpy (numerical computing)
   - pyautogui (GUI automation)
   - pywin32 (Windows API access)
   - pycaw (audio control)
   - comtypes (COM interface)
   - screen-brightness-control (brightness control)
   - PyQt6 (GUI framework)
   - speechrecognition (speech-to-text)
   - pyttsx3 (text-to-speech)
   - pywebview (web interface)
   - google-generativeai (AI features)
   - pygetwindow (window management)

### Step 3: Verify Installation
Run this command to check if all packages are installed:
```
python -c "import cv2, mediapipe, pyautogui, speech_recognition, pyttsx3; print('All packages installed successfully!')"
```

## How to Run

### Option 1: Full Application (Recommended)
1. Navigate to your Aura-Ctrl folder in Command Prompt/PowerShell
2. Run the main application:
   ```
   python app.py
   ```
3. A web browser window will open with the Aura-Ctrl interface
4. Click "Gesture Control" for hand gesture control or "Voice based Control" for voice commands
5. Click the help button (?) for detailed instructions on available gestures and commands

### Option 2: Individual Components
- **Gesture Control Only**:
  ```
  python gesture.py
  ```
- **Voice Control Only**:
  ```
  python voice.py
  ```

## Usage Guide

### Gesture Control
- **Cursor Movement**: Raise your index finger and move your hand
- **Left Click**: Bring index finger and thumb close together
- **Right Click**: Bring thumb and pinky finger close together
- **Scroll**: Join index and middle fingers, move hand up/down
- **Volume Control**: Make a fist, move hand up/down
- **Brightness Control**: Make a fist, move hand left/right
- **Launch Apps**: Various finger combinations (see help for details)

### Voice Commands
- **App Control**: "open chrome", "close notepad", "maximize window"
- **System Control**: "volume up", "brightness down", "take screenshot"
- **Window Management**: "arrange left right", "swap windows"
- **WiFi Control**: "wifi on", "wifi off"

### PowerPoint Features
- "create new presentation"
- "create slide about [topic]"
- "start presentation", "next slide", "previous slide"

## Troubleshooting

### Common Issues

**Camera/Microphone Not Working**
- Ensure your webcam and microphone are properly connected
- Check that no other applications are using them
- Grant camera/microphone permissions when prompted

**Packages Not Installing**
- Run Command Prompt as Administrator
- Update pip: `python -m pip install --upgrade pip`
- If pip fails, try: `python -m pip install --user -r requirements.txt`

**Gesture Recognition Not Accurate**
- Ensure good lighting
- Keep your hand clearly visible in the camera frame
- Use a plain background
- Avoid multiple hands in frame

**Voice Commands Not Recognized**
- Speak clearly and close to the microphone
- Reduce background noise
- Ensure your microphone is set as default in Windows settings

**Application Won't Start**
- Verify Python is installed and in PATH
- Check that all dependencies are installed
- Try running individual components to isolate issues

### Performance Tips
- Use a well-lit environment for better gesture detection
- Keep camera steady and at eye level
- Close unnecessary applications to improve performance
- Restart the application if gestures become unresponsive

## File Structure
```
Aura-Ctrl/
├── app.py                 # Main application entry point
├── gesture.py             # Hand gesture control logic
├── voice.py               # Voice command processing
├── ppt_controller.py      # PowerPoint integration
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── ui/                    # Web interface files
│   ├── index.html         # Main interface
│   ├── help.html          # Help documentation
│   ├── style.css          # Styling
│   └── assets/            # Images and resources
└── screenshots/           # Saved screenshots (created automatically)
```

## Contributing
Feel free to submit issues, feature requests, or pull requests to improve Aura-Ctrl!

## License
This project is open-source. Please check individual package licenses for third-party dependencies.
