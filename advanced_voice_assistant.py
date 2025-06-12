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
import json
import requests
from bs4 import BeautifulSoup
import googletrans
from googletrans import Translator

# Initialize Speech Recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 175)  # Speed of speech

# Initialize translator
translator = Translator()

# Initialize pygame for audio feedback
pygame.mixer.init()

# Control variables
last_action_time = 0
cooldown_time = 0.2  # seconds between actions to avoid repeated triggers
listening = True
active_mode = True  # Active by default, no need for trigger words
inactivity_timeout = 120  # 2 minutes of inactivity before going to sleep mode
last_interaction_time = time.time()
processing_command = False

# Your OpenAI API key - Replace with user's key securely
# IMPORTANT: In a real application, don't hardcode this
# Instead use environment variables or a secure configuration file
OPENAI_API_KEY = ""  # Fill this in through a secure method

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

# Message history for context
message_history = []
HISTORY_MAX_LENGTH = 10

def speak(text, language='en'):
    """Use text-to-speech to speak the given text"""
    print(f"🔊 Assistant: {text}")
    
    # Store message in history
    message_history.append({"role": "assistant", "content": text})
    if len(message_history) > HISTORY_MAX_LENGTH:
        message_history.pop(0)
    
    if language != 'en':
        try:
            # Translate text to specified language
            translated = translator.translate(text, dest=language)
            text = translated.text
        except Exception as e:
            print(f"Translation error: {e}")
    
    tts_engine.say(text)
    try:
        tts_engine.runAndWait()
    except RuntimeError:
        # Sometimes the TTS engine gets stuck, reset it
        tts_engine.stop()

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

def save_message(message, filename="conversation_history.txt"):
    """Save a message to a file"""
    try:
        with open(filename, 'a', encoding='utf-8') as file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"[{timestamp}] {message}\n")
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False

def detect_language(text):
    """Detect the language of the input text"""
    try:
        detection = translator.detect(text)
        return detection.lang
    except:
        return 'en'  # Default to English if detection fails

def listen_for_command():
    """Listen for a command and return the recognized text"""
    global last_interaction_time
    
    try:
        with microphone as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            
            # Update the last interaction time
            last_interaction_time = time.time()
            
            # Store user message in history
            message_history.append({"role": "user", "content": text})
            if len(message_history) > HISTORY_MAX_LENGTH:
                message_history.pop(0)
            
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Request error; {e}")
            return ""
    except Exception as e:
        print(f"Error listening: {e}")
        return ""

def extract_seconds(command_text):
    """Extract seconds from command text"""
    numbers = re.findall(r'\d+', command_text)
    if numbers:
        return int(numbers[0])
    return 5  # Default to 5 seconds if no number is specified

def extract_app_name(command_text):
    """Extract application name from command text"""
    for app_name in APPLICATIONS.keys():
        if app_name in command_text.lower():
            return app_name
    return None

def open_application(app_name):
    """Open the specified application"""
    try:
        app = APPLICATIONS.get(app_name.lower())
        if not app:
            speak(f"मुझे नहीं पता कैसे {app_name} खोलना है", 'hi')
            return False
        
        # Check if it's a URL
        if app.startswith("http"):
            webbrowser.open(app)
            speak(f"{app_name} ब्राउज़र में खोल रहा हूँ", 'hi')
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
        
        speak(f"{app_name} खोल रहा हूँ", 'hi')
        return True
    except Exception as e:
        print(f"Error opening application: {e}")
        speak(f"{app_name} नहीं खोल पाया", 'hi')
        return False

def youtube_search(query):
    """Search YouTube and get information about videos"""
    try:
        # Format the search query for a URL
        formatted_query = '+'.join(query.split())
        search_url = f"https://www.youtube.com/results?search_query={formatted_query}"
        
        # Open the search in the browser
        webbrowser.open(search_url)
        speak(f"यूट्यूब पर {query} के लिए खोज रहा हूँ", 'hi')
        
        return True
    except Exception as e:
        print(f"Error searching YouTube: {e}")
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
        
        speak(f"स्क्रीनशॉट पिक्चर्स फोल्डर में सेव कर दिया है", 'hi')
        return True
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def lock_computer():
    """Lock the computer screen"""
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.LockWorkStation()
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(['pmset', 'displaysleepnow'])
    else:  # Linux
        subprocess.call(['xdg-screensaver', 'lock'])
    return True

def get_battery_status():
    """Get battery percentage and charging status"""
    if not hasattr(psutil, "sensors_battery"):
        speak("इस सिस्टम पर बैटरी स्टेटस जानकारी उपलब्ध नहीं है", 'hi')
        return False
    
    battery = psutil.sensors_battery()
    if battery is None:
        speak("कोई बैटरी नहीं मिली। क्या आप डेस्कटॉप का उपयोग कर रहे हैं?", 'hi')
        return False
    
    percent = battery.percent
    charging = battery.power_plugged
    
    status = "चार्ज हो रही है" if charging else "डिस्चार्ज हो रही है"
    speak(f"बैटरी {percent} प्रतिशत है और {status}", 'hi')
    return True

def get_current_time():
    """Tell the current time"""
    current_time = datetime.now().strftime("%I:%M %p")
    speak(f"अभी का समय है {current_time}", 'hi')
    return True

def get_current_date():
    """Tell the current date"""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    speak(f"आज {current_date} है", 'hi')
    return True

def process_media_command(command_text):
    """Process media playback commands"""
    if "play" in command_text or "pause" in command_text or "चलाओ" in command_text or "रोको" in command_text:
        pyautogui.press('playpause')  # Play/pause media key
        return "Media Play/Pause"
    
    elif "volume up" in command_text or "louder" in command_text or "आवाज बढ़ाओ" in command_text:
        pyautogui.press('volumeup')  # Volume up
        return "Volume Up"
    
    elif "volume down" in command_text or "quieter" in command_text or "आवाज कम करो" in command_text:
        pyautogui.press('volumedown')  # Volume down
        return "Volume Down"
    
    elif "mute" in command_text or "unmute" in command_text or "म्यूट" in command_text:
        pyautogui.press('volumemute')  # Mute/Unmute
        return "Mute Toggle"
    
    elif "next" in command_text or "skip" in command_text or "अगला" in command_text:
        pyautogui.press('nexttrack')  # Next track
        return "Next Track"
    
    elif "previous" in command_text or "back" in command_text or "पिछला" in command_text:
        pyautogui.press('prevtrack')  # Previous track
        return "Previous Track"
    
    elif "forward" in command_text or "आगे" in command_text:
        seconds = extract_seconds(command_text)
        for _ in range(seconds):
            pyautogui.press('right')
            time.sleep(0.05)
        return f"Forward {seconds} seconds"
    
    elif "backward" in command_text or "rewind" in command_text or "पीछे" in command_text:
        seconds = extract_seconds(command_text)
        for _ in range(seconds):
            pyautogui.press('left')
            time.sleep(0.05)
        return f"Backward {seconds} seconds"
    
    elif "fullscreen" in command_text or "फुलस्क्रीन" in command_text:
        pyautogui.press('f')  # F key for fullscreen
        return "Fullscreen"
    
    return None

def is_system_command(text):
    """Determine if this is a system command or a general query"""
    system_keywords = [
        "open", "close", "volume", "brightness", "screenshot", "lock", "shutdown",
        "restart", "battery", "time", "date", "play", "pause", "next", "previous",
        "forward", "backward", "scroll", "copy", "paste", "cut", "undo", "redo",
        "save", "select", "minimize", "maximize", "mute", "unmute", "fullscreen",
        "खोलो", "बंद करो", "आवाज", "स्क्रीनशॉट", "लॉक", "शटडाउन", "रीस्टार्ट", 
        "बैटरी", "समय", "तारीख", "चलाओ", "रोको", "अगला", "पिछला", "आगे", "पीछे"
    ]
    
    return any(keyword in text.lower() for keyword in system_keywords)

def process_command(command_text):
    """Process the recognized command and perform corresponding action"""
    global last_interaction_time, active_mode, processing_command, last_action_time
    
    # Skip if we're already processing a command
    if processing_command:
        return "Still processing previous command"
    
    processing_command = True
    
    # Update the last interaction time
    last_interaction_time = time.time()
    
    # Detect language
    language = detect_language(command_text)
    is_hindi = language == 'hi'
    response_language = 'hi' if is_hindi else 'en'
    
    # Only perform actions if cooldown has passed
    current_time = time.time()
    if current_time - last_action_time < cooldown_time:
        processing_command = False
        return "Cooldown"
    
    # Reset last action time
    last_action_time = current_time
    
    try:
        # Save the user's message if it contains "save" or "सेव" or "मैसेज"
        if "save" in command_text.lower() or "सेव" in command_text or "मैसेज" in command_text:
            if save_message(command_text):
                speak("मैसेज सेव कर दिया गया है", response_language)
                processing_command = False
                return "Message Saved"
        
        # Check for stop/exit command
        if ("stop" in command_text.lower() or "exit" in command_text.lower() or "quit" in command_text.lower() or 
            "बंद करो" in command_text or "बाहर" in command_text):
            speak("वॉइस असिस्टेंट बंद कर रहा हूँ, अलविदा!", response_language)
            global listening
            listening = False
            processing_command = False
            return "Exiting"
        
        # YouTube specific commands
        if ("youtube" in command_text.lower() or "यूट्यूब" in command_text) and ("open" in command_text.lower() or "खोलो" in command_text):
            # Extract search query if present
            match = re.search(r"(?:search|खोज|find|about|के बारे में)(?:\s+for)?\s+(.+?)(?:\s+on youtube|$)", command_text.lower())
            if match:
                query = match.group(1).strip()
                youtube_search(query)
            else:
                open_application("youtube")
            processing_command = False
            return "YouTube Action"
        
        # SYSTEM CONTROLS
        
        # Open application
        if "open" in command_text.lower() or "खोलो" in command_text:
            app_name = extract_app_name(command_text)
            if app_name:
                open_application(app_name)
                processing_command = False
                return f"Opening {app_name}"
            else:
                # Try to extract app name following "open" or "खोलो"
                open_match = re.search(r"(?:open|खोलो)\s+([a-zा-ह\s]+)", command_text.lower())
                if open_match:
                    app_name = open_match.group(1).strip()
                    if app_name in APPLICATIONS:
                        open_application(app_name)
                        processing_command = False
                        return f"Opening {app_name}"
                    else:
                        speak(f"मुझे नहीं पता कैसे {app_name} खोलना है", response_language)
                        processing_command = False
                        return f"Unknown App: {app_name}"
        
        # Lock computer
        if ("lock" in command_text.lower() and ("computer" in command_text.lower() or "screen" in command_text.lower() or "laptop" in command_text.lower())) or "लॉक" in command_text:
            lock_computer()
            speak("कंप्यूटर लॉक कर रहा हूँ", response_language)
            processing_command = False
            return "Locked Computer"
        
        # Screenshot
        if "screenshot" in command_text.lower() or "screen shot" in command_text.lower() or "capture" in command_text.lower() or "स्क्रीनशॉट" in command_text:
            take_screenshot()
            processing_command = False
            return "Screenshot Taken"
        
        # Volume control
        if "volume up" in command_text.lower() or "increase volume" in command_text.lower() or "आवाज बढ़ाओ" in command_text:
            pyautogui.press('volumeup')
            speak("आवाज़ बढ़ा दी है", response_language)
            processing_command = False
            return "Volume Up"
        
        if "volume down" in command_text.lower() or "decrease volume" in command_text.lower() or "आवाज कम करो" in command_text:
            pyautogui.press('volumedown')
            speak("आवाज़ कम कर दी है", response_language)
            processing_command = False
            return "Volume Down"
        
        if ("mute" in command_text.lower() or "unmute" in command_text.lower() or "म्यूट" in command_text):
            pyautogui.press('volumemute')
            speak("म्यूट टॉगल कर दिया है", response_language)
            processing_command = False
            return "Mute Toggled"
        
        # INFORMATION QUERIES
        
        # Time
        if "time" in command_text.lower() or "समय" in command_text:
            get_current_time()
            processing_command = False
            return "Time"
        
        # Date
        if "date" in command_text.lower() or "day" in command_text.lower() or "तारीख" in command_text or "दिन" in command_text:
            get_current_date()
            processing_command = False
            return "Date"
        
        # Battery
        if "battery" in command_text.lower() or "बैटरी" in command_text:
            get_battery_status()
            processing_command = False
            return "Battery"
        
        # Media control commands
        media_action = process_media_command(command_text)
        if media_action:
            speak(f"मीडिया कंट्रोल: {media_action}", response_language)
            processing_command = False
            return media_action
        
        # NAVIGATION & WINDOW MANAGEMENT
        
        # Close window
        if "close" in command_text.lower() and ("window" in command_text.lower() or "application" in command_text.lower() or "tab" in command_text.lower()) or "बंद करो" in command_text:
            pyautogui.hotkey('alt', 'f4')
            speak("विंडो बंद कर रहा हूँ", response_language)
            processing_command = False
            return "Window Closed"
        
        # Process as a general query if no system command was identified
        if not is_system_command(command_text):
            # Here you would call the OpenAI API
            # For now, respond with a placeholder
            speak("मुझे यह कमांड समझ नहीं आया। कृपया दोबारा कोशिश करें।", response_language)
            processing_command = False
            return "Unrecognized Command"
        
        processing_command = False
        return "No action taken"
    
    except Exception as e:
        print(f"Error processing command: {e}")
        speak("कमांड प्रोसेस करने में त्रुटि हुई", response_language)
        processing_command = False
        return "Error"

def check_inactivity():
    """Check for inactivity and put system to sleep if timeout exceeded"""
    global active_mode, last_interaction_time
    
    while listening:
        current_time = time.time()
        if active_mode and (current_time - last_interaction_time) > inactivity_timeout:
            print(f"Inactive for {inactivity_timeout} seconds, going to sleep mode")
            speak("मैं सुनना बंद कर रहा हूँ। मुझे जगाने के लिए कोई कमांड दें।", 'hi')
            active_mode = False
        
        elif not active_mode and (current_time - last_interaction_time) <= inactivity_timeout:
            print("Detected activity, waking up")
            active_mode = True
        
        time.sleep(10)  # Check every 10 seconds to reduce CPU usage

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
    """Main function for continuously listening for commands"""
    global active_mode, listening, last_interaction_time, processing_command
    
    create_sounds_directory()
    print("Voice Assistant Started")
    speak("वॉइस असिस्टेंट चालू हो गया है, मैं आपकी सहायता के लिए तैयार हूँ", 'hi')
    
    print("\nUsage Guide:")
    print("- Just speak naturally to issue commands")
    print("- No need for trigger phrases")
    print("- The assistant will go to sleep after 2 minutes of inactivity")
    print("- Hindi commands are also supported")
    print("\nKeyboard shortcuts:")
    print("- Press 'q' key to quit the program")
    
    # Start inactivity monitoring thread
    inactivity_thread = threading.Thread(target=check_inactivity)
    inactivity_thread.daemon = True
    inactivity_thread.start()
    
    # Start keyboard monitoring thread
    keyboard_thread = threading.Thread(target=check_keyboard_quit)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    
    while listening:
        if active_mode and not processing_command:
            command_text = listen_for_command()
            if command_text:
                action = process_command(command_text)
                print(f"Action: {action}")
        else:
            # Check if we should wake up
            text = listen_for_command()
            if text:
                print("Waking up from sleep mode")
                speak("मैं फिर से सुन रहा हूँ", 'hi')
                active_mode = True
                last_interaction_time = time.time()
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.1)
    
    print("Voice Assistant stopped.")

if __name__ == "__main__":
    try:
        continuous_listening()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'tts_engine' in locals() or 'tts_engine' in globals():
            try:
                tts_engine.stop()
            except:
                pass
        pygame.mixer.quit() 