# Windows Platform Guide

## Screenshot
```python
# pyautogui (cross-platform, recommended)
import pyautogui
pyautogui.screenshot("output.png")

# PIL/Pillow
from PIL import ImageGrab
img = ImageGrab.grab()
img.save("output.png")
```

## Input

### pyautogui (Python, recommended)
```python
import pyautogui

# Click
pyautogui.click(x, y)

# Double-click
pyautogui.doubleClick(x, y)

# Right-click
pyautogui.rightClick(x, y)

# Type text
pyautogui.typewrite("hello", interval=0.02)

# Hotkeys
pyautogui.hotkey("ctrl", "c")
pyautogui.hotkey("ctrl", "v")
pyautogui.press("enter")

# Drag
pyautogui.dragTo(x2, y2, duration=0.5)
```

### pynput (Python)
```python
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

mouse = MouseController()
keyboard = KeyboardController()

mouse.position = (x, y)
mouse.click(Button.left)
keyboard.press(Key.enter)
keyboard.release(Key.enter)
```

## Clipboard
```python
import pyperclip
pyperclip.copy("text")
text = pyperclip.paste()
```

## Window Management
```python
import pyautogui
# Find and activate window
import subprocess
subprocess.run(["powershell", "-Command",
    "Add-Type -AssemblyName Microsoft.VisualBasic; "
    "[Microsoft.VisualBasic.Interaction]::AppActivate('WindowTitle')"])
```

## Notes
- Coordinates are logical pixels; HiDPI (scaling > 100%) is handled automatically by the agent harness.
- Run actions via the HTTP API the same way as Linux/macOS: `POST /execute`.
- PowerShell is available for system-level tasks; prefer Python where possible.
