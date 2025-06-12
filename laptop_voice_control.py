import speech_recognition as sr
import pyautogui
import time
import re
import pygame
import threading
import os
import keyboard
import subprocess
import webbrowser
from datetime import datetime
import platform
import psutil
import pyttsx3
import ctypes

# Initialize Speech Recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Initialize pygame for audio feedback
pygame.mixer.init()

# Control variables
last_action_time = 0
cooldown_time = 0.5  # seconds between actions to avoid repeated triggers
listening = True
command_mode = False  # Whether the system is listening for commands
command_mode_timeout = 15  # Seconds to wait for a command before going back to trigger mode

# Trigger phrases that activate command mode
TRIGGER_PHRASES = ["computer", "hey computer", "ok computer", "laptop"]

# Application paths - adjust these for your system
APPLICATIONS = {
    "browser": "chrome",
    "chrome": "chrome",
    "firefox": "firefox",
    "explorer": "explorer",
    "file explorer": "explorer",
    "notepad": "notepad",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "spotify": "spotify",
    "calculator": "calc",
    "paint": "mspaint",
    "camera": "microsoft.windows.camera:",
    "settings": "ms-settings:",
    "mail": "outlook",
    "outlook": "outlook",
    "zoom": "zoom",
    "terminal": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "youtube": "https://www.youtube.com/",
    "google": "https://www.google.com/",
    "facebook": "https://www.facebook.com/",
    "twitter": "https://twitter.com/",
    "instagram": "https://www.instagram.com/",
    "linkedin": "https://www.linkedin.com/",
    "github": "https://github.com/",
    "netflix": "https://www.netflix.com/",
    "amazon": "https://www.amazon.com/"
}

def speak(text):
    """Use text-to-speech to speak the given text"""
    print(f"🔊 Assistant: {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()

def play_sound(sound_name):
    """Play a sound for feedback"""
    try:
        sound_file = os.path.join("sounds", f"{sound_name}.wav")
        if not os.path.exists(sound_file):
            return  # Skip if file doesn't exist
        
        pygame.mixer.Sound(sound_file).play()
    except Exception as e:
        print(f"Could not play sound: {e}")

def create_sounds_directory():
    """Create directory for sound files if it doesn't exist"""
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
        print("Created 'sounds' directory. You can add feedback sounds here.")

def listen_for_audio():
    """Listen for audio and return recognized text"""
    try:
        with microphone as source:
            if command_mode:
                print("Listening for command...")
            else:
                print("Waiting for trigger phrase...")
                
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        
        try:
            text = recognizer.recognize_google(audio).lower()
            if command_mode:
                print(f"Command recognized: {text}")
            else:
                print(f"Heard: {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Request error; {e}")
            return ""
    except Exception as e:
        print(f"Error in listen_for_audio: {e}")
        return ""

def extract_seconds(command_text):
    """Extract seconds from command text (e.g., 'forward 5' -> 5)"""
    # Look for numbers in the command
    numbers = re.findall(r'\d+', command_text)
    if numbers:
        return int(numbers[0])
    return 5  # Default to 5 seconds if no number is specified

def extract_app_name(command_text):
    """Extract application name from command text"""
    for app_name in APPLICATIONS.keys():
        if app_name in command_text:
            return app_name
    return None

def open_application(app_name):
    """Open the specified application"""
    try:
        app = APPLICATIONS.get(app_name.lower())
        if not app:
            speak(f"I don't know how to open {app_name}")
            return False
        
        # Check if it's a URL
        if app.startswith("http"):
            webbrowser.open(app)
            speak(f"Opening {app_name} in the browser")
            return True
        
        # Try to open the application
        if platform.system() == "Windows":
            try:
                subprocess.Popen([app])
            except:
                try:
                    os.startfile(app)
                except:
                    subprocess.Popen(f"start {app}", shell=True)
        else:  # macOS or Linux
            subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", app])
        
        speak(f"Opening {app_name}")
        return True
    except Exception as e:
        print(f"Error opening application: {e}")
        speak(f"Couldn't open {app_name}")
        return False

def set_system_volume(level):
    """Set system volume level (0-100)"""
    level = max(0, min(100, level))  # Ensure level is between 0 and 100
    
    if platform.system() == "Windows":
        try:
            # Fallback method using pyautogui
            current_vol = get_system_volume()
            difference = level - current_vol
            key = 'up' if difference > 0 else 'down'
            for _ in range(abs(difference) // 2):  # Each press changes by ~2%
                pyautogui.press(f'volume{key}')
            return True
        except Exception as e:
            print(f"Error adjusting volume: {e}")
            return False
    else:
        # For macOS and Linux, this is a simplified approach
        # You may need to adjust for your specific OS
        return False

def get_system_volume():
    """Get current system volume (0-100)"""
    # This is a simplified version, actual implementation would depend on the OS
    return 50  # Default if can't get actual volume

def adjust_brightness(increase=True):
    """Increase or decrease screen brightness"""
    if platform.system() == "Windows":
        try:
            # Using keyboard shortcuts
            if increase:
                keyboard.press_and_release('fn+f12')  # Common for brightness up
                # Alternative: keyboard.press_and_release('brightness_up')  
            else:
                keyboard.press_and_release('fn+f11')  # Common for brightness down
                # Alternative: keyboard.press_and_release('brightness_down')
            return True
        except:
            return False
    else:
        # For macOS and Linux, this functionality would need OS-specific code
        return False

def take_screenshot():
    """Take a screenshot and save it to Pictures folder"""
    try:
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        if not os.path.exists(pictures_dir):
            os.makedirs(pictures_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(pictures_dir, f"Screenshot_{timestamp}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        speak(f"Screenshot saved to Pictures folder")
        return True
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def lock_computer():
    """Lock the computer screen"""
    if platform.system() == "Windows":
        ctypes.windll.user32.LockWorkStation()
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(['pmset', 'displaysleepnow'])
    else:  # Linux
        subprocess.call(['xdg-screensaver', 'lock'])
    return True

def shutdown_computer():
    """Shutdown the computer with confirmation"""
    speak("Are you sure you want to shut down your computer? Say 'yes' to confirm or 'no' to cancel.")
    
    confirmation = listen_for_audio()
    if "yes" in confirmation.lower():
        speak("Shutting down your computer now. Goodbye!")
        
        if platform.system() == "Windows":
            os.system("shutdown /s /t 10")
        elif platform.system() == "Darwin":  # macOS
            os.system("sudo shutdown -h now")
        else:  # Linux
            os.system("sudo shutdown now")
        return True
    else:
        speak("Shutdown cancelled.")
        return False

def restart_computer():
    """Restart the computer with confirmation"""
    speak("Are you sure you want to restart your computer? Say 'yes' to confirm or 'no' to cancel.")
    
    confirmation = listen_for_audio()
    if "yes" in confirmation.lower():
        speak("Restarting your computer now.")
        
        if platform.system() == "Windows":
            os.system("shutdown /r /t 10")
        elif platform.system() == "Darwin":  # macOS
            os.system("sudo shutdown -r now")
        else:  # Linux
            os.system("sudo reboot")
        return True
    else:
        speak("Restart cancelled.")
        return False

def get_battery_status():
    """Get battery percentage and charging status"""
    if not hasattr(psutil, "sensors_battery"):
        speak("Battery status information not available on this system.")
        return False
    
    battery = psutil.sensors_battery()
    if battery is None:
        speak("No battery detected. Are you using a desktop?")
        return False
    
    percent = battery.percent
    charging = battery.power_plugged
    
    status = "charging" if charging else "discharging"
    speak(f"Battery is at {percent} percent and {status}.")
    return True

def get_current_time():
    """Tell the current time"""
    current_time = datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")
    return True

def get_current_date():
    """Tell the current date"""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {current_date}")
    return True

def get_weather():
    """Get current weather (simplified version)"""
    speak("To get accurate weather information, you'll need to connect this to a weather API. For now, I recommend checking your weather app.")
    return True

def process_media_command(command_text):
    """Process media playback commands"""
    if "play" in command_text or "pause" in command_text:
        pyautogui.press('playpause')  # Play/pause media key
        return "Media Play/Pause"
    
    elif "volume up" in command_text or "louder" in command_text:
        pyautogui.press('volumeup')  # Volume up
        return "Volume Up"
    
    elif "volume down" in command_text or "quieter" in command_text:
        pyautogui.press('volumedown')  # Volume down
        return "Volume Down"
    
    elif "mute" in command_text or "unmute" in command_text:
        pyautogui.press('volumemute')  # Mute/Unmute
        return "Mute Toggle"
    
    elif "next" in command_text or "skip" in command_text:
        pyautogui.press('nexttrack')  # Next track
        return "Next Track"
    
    elif "previous" in command_text or "back" in command_text:
        pyautogui.press('prevtrack')  # Previous track
        return "Previous Track"
    
    elif "forward" in command_text:
        seconds = extract_seconds(command_text)
        for _ in range(seconds):
            pyautogui.press('right')
            time.sleep(0.05)
        return f"Forward {seconds} seconds"
    
    elif "backward" in command_text or "rewind" in command_text:
        seconds = extract_seconds(command_text)
        for _ in range(seconds):
            pyautogui.press('left')
            time.sleep(0.05)
        return f"Backward {seconds} seconds"
    
    elif "fullscreen" in command_text:
        pyautogui.press('f')  # F key for fullscreen
        return "Fullscreen"
    
    return None

def process_command(command_text):
    """Process the recognized command and perform corresponding action"""
    global last_action_time, command_mode, listening
    
    # Only perform actions if cooldown has passed
    current_time = time.time()
    if current_time - last_action_time < cooldown_time:
        return "Cooldown"
    
    # Reset last action time for any recognized command
    last_action_time = current_time
    
    # Check for exit commands first
    if "exit" in command_text or "quit" in command_text or "stop listening" in command_text:
        listening = False
        speak("Stopping voice control system. Goodbye!")
        play_sound("exit")
        return "Exiting"
    
    # SYSTEM CONTROLS
    
    # Lock computer
    if "lock" in command_text and ("computer" in command_text or "screen" in command_text or "laptop" in command_text):
        lock_computer()
        speak("Locking your computer")
        return "Locked Computer"
    
    # Shutdown
    if "shut down" in command_text or "shutdown" in command_text or "turn off" in command_text:
        if "computer" in command_text or "laptop" in command_text or "system" in command_text:
            shutdown_computer()
            return "Shutdown Initiated"
    
    # Restart
    if "restart" in command_text or "reboot" in command_text:
        if "computer" in command_text or "laptop" in command_text or "system" in command_text:
            restart_computer()
            return "Restart Initiated"
    
    # Volume specific percentage
    volume_match = re.search(r"volume (\d+)(?:\s*percent)?", command_text)
    if volume_match:
        volume_level = int(volume_match.group(1))
        set_system_volume(volume_level)
        speak(f"Setting volume to {volume_level} percent")
        return f"Volume set to {volume_level}%"
    
    # Volume up/down
    if "volume up" in command_text or "increase volume" in command_text or "louder" in command_text:
        current_vol = get_system_volume()
        new_vol = min(100, current_vol + 10)
        set_system_volume(new_vol)
        speak(f"Volume increased")
        return "Volume Increased"
    
    if "volume down" in command_text or "decrease volume" in command_text or "quieter" in command_text:
        current_vol = get_system_volume()
        new_vol = max(0, current_vol - 10)
        set_system_volume(new_vol)
        speak(f"Volume decreased")
        return "Volume Decreased"
    
    # Mute toggle
    if "mute" in command_text or "unmute" in command_text:
        pyautogui.press('volumemute')
        speak("Toggled mute")
        return "Mute Toggled"
    
    # Brightness
    if "brightness up" in command_text or "increase brightness" in command_text or "brighter" in command_text:
        adjust_brightness(increase=True)
        speak("Increased brightness")
        return "Brightness Up"
    
    if "brightness down" in command_text or "decrease brightness" in command_text or "dimmer" in command_text:
        adjust_brightness(increase=False)
        speak("Decreased brightness")
        return "Brightness Down"
    
    # Screenshot
    if "screenshot" in command_text or "take a picture" in command_text or "capture screen" in command_text:
        take_screenshot()
        return "Screenshot Taken"
    
    # Battery status
    if "battery" in command_text or "power status" in command_text:
        get_battery_status()
        return "Battery Status"
    
    # INFORMATION QUERIES
    
    # Time
    if "what time" in command_text or "current time" in command_text or "tell me the time" in command_text:
        get_current_time()
        return "Current Time"
    
    # Date
    if "what day" in command_text or "what date" in command_text or "today's date" in command_text:
        get_current_date()
        return "Current Date"
    
    # Weather
    if "weather" in command_text:
        get_weather()
        return "Weather Information"
    
    # APPLICATION CONTROL
    
    # Open application
    if "open" in command_text:
        app_name = extract_app_name(command_text)
        if app_name:
            open_application(app_name)
            return f"Opening {app_name}"
        else:
            # Try to extract app name following "open"
            open_match = re.search(r"open\s+([a-z\s]+)", command_text)
            if open_match:
                app_name = open_match.group(1).strip()
                if app_name in APPLICATIONS:
                    open_application(app_name)
                    return f"Opening {app_name}"
                else:
                    speak(f"I don't know how to open {app_name}")
                    return f"Unknown App: {app_name}"
    
    # Close current window
    if "close window" in command_text or "close tab" in command_text or "close application" in command_text:
        pyautogui.hotkey('alt', 'f4')
        speak("Closing window")
        return "Window Closed"
    
    # Media control commands
    media_action = process_media_command(command_text)
    if media_action:
        speak(f"Media control: {media_action}")
        return media_action
    
    # NAVIGATION & WINDOW MANAGEMENT
    
    # Switch window
    if "switch window" in command_text or "next window" in command_text:
        pyautogui.hotkey('alt', 'tab')
        speak("Switching window")
        return "Window Switched"
    
    # Minimize window
    if "minimize" in command_text:
        pyautogui.hotkey('win', 'down')
        speak("Minimizing window")
        return "Window Minimized"
    
    # Maximize window
    if "maximize" in command_text:
        pyautogui.hotkey('win', 'up')
        speak("Maximizing window")
        return "Window Maximized"
    
    # Show desktop
    if "show desktop" in command_text or "go to desktop" in command_text:
        pyautogui.hotkey('win', 'd')
        speak("Showing desktop")
        return "Desktop Shown"
    
    # Scroll
    if "scroll down" in command_text:
        for _ in range(10):
            pyautogui.scroll(-100)
            time.sleep(0.1)
        speak("Scrolling down")
        return "Scrolled Down"
    
    if "scroll up" in command_text:
        for _ in range(10):
            pyautogui.scroll(100)
            time.sleep(0.1)
        speak("Scrolling up")
        return "Scrolled Up"
    
    # BASIC COMPUTER FUNCTIONS
    
    # Copy
    if "copy" in command_text and not any(word in command_text for word in ["text", "paste", "cut"]):
        pyautogui.hotkey('ctrl', 'c')
        speak("Copied")
        return "Copy"
    
    # Paste
    if "paste" in command_text:
        pyautogui.hotkey('ctrl', 'v')
        speak("Pasted")
        return "Paste"
    
    # Cut
    if "cut" in command_text and "text" not in command_text:
        pyautogui.hotkey('ctrl', 'x')
        speak("Cut")
        return "Cut"
    
    # Undo
    if "undo" in command_text:
        pyautogui.hotkey('ctrl', 'z')
        speak("Undo")
        return "Undo"
    
    # Redo
    if "redo" in command_text:
        pyautogui.hotkey('ctrl', 'y')
        speak("Redo")
        return "Redo"
    
    # Save
    if "save" in command_text:
        pyautogui.hotkey('ctrl', 's')
        speak("Saving")
        return "Save"
    
    # Select all
    if "select all" in command_text:
        pyautogui.hotkey('ctrl', 'a')
        speak("Selected all")
        return "Select All"
    
    # SPECIAL COMMANDS
    
    # Return to trigger mode if no command was recognized
    speak("I didn't understand that command. Please try again.")
    command_mode = False
    return "No Action - Returning to Trigger Mode"

def command_mode_timer():
    """Thread function to time out command mode after inactivity"""
    global command_mode
    time.sleep(command_mode_timeout)
    if command_mode:
        print(f"Command mode timed out after {command_mode_timeout} seconds")
        speak("Command mode timed out. Say the trigger phrase again when you need me.")
        command_mode = False

def check_for_trigger(text):
    """Check if the recognized text contains a trigger phrase"""
    return any(trigger in text for trigger in TRIGGER_PHRASES)

def check_keyboard_quit():
    """Thread function to monitor keyboard quit shortcut"""
    global listening
    while listening:
        try:
            # Press 'q' key or Ctrl+C to quit
            if keyboard.is_pressed('q') or keyboard.is_pressed('ctrl+c'):
                print("\nQuit shortcut pressed!")
                listening = False
                break
            time.sleep(0.1)
        except:
            pass

def continuous_listening():
    """Main function for continuously listening for trigger word and commands"""
    global command_mode, listening
    
    create_sounds_directory()
    print("Laptop Voice Control Started")
    speak("Voice control system activated. Say 'computer' or 'hey computer' to give a command.")
    
    print("\nCommand Guide (Partial List):")
    print("First say the trigger phrase ('Computer' or 'Hey Computer') to activate command mode")
    print("Then use one of the following commands:")
    print("- System: Lock computer, Shutdown computer, Restart computer")
    print("- Volume: Volume up, Volume down, Volume 50 percent, Mute")
    print("- Screen: Brightness up, Brightness down, Screenshot")
    print("- Information: What time is it, What's today's date, Battery status")
    print("- Applications: Open Chrome, Open Notepad, etc.")
    print("- Media: Play/Pause, Next track, Previous track")
    print("- Window: Close window, Switch window, Minimize, Maximize")
    print("- Navigation: Scroll up, Scroll down, Show desktop")
    print("- Basic functions: Copy, Paste, Cut, Undo, Save")
    print("- Exit: Exit, Quit, Stop listening")
    
    print("\nKeyboard shortcuts:")
    print("- Press 'q' key to quit the program")
    print("\nWaiting for trigger phrase...")
    
    # Start keyboard monitoring thread
    keyboard_thread = threading.Thread(target=check_keyboard_quit)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    
    while listening:
        text = listen_for_audio()
        
        if not text:
            continue
        
        # Check for trigger word if not in command mode
        if not command_mode:
            if check_for_trigger(text):
                command_mode = True
                print("Trigger detected! Command mode activated.")
                play_sound("activated")
                speak("I'm listening")
                
                # Start timer to deactivate command mode after timeout
                timer_thread = threading.Thread(target=command_mode_timer)
                timer_thread.daemon = True
                timer_thread.start()
                
            continue  # Skip further processing, wait for next voice input
        
        # If in command mode, process the command
        action = process_command(text)
        print(f"Action: {action}")
        
        # Exit if commanded
        if action == "Exiting":
            break
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.1)
    
    print("Voice Control stopped.")

if __name__ == "__main__":
    try:
        continuous_listening()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        tts_engine.stop()
        pygame.mixer.quit() 