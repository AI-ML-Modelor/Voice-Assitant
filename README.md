# Advanced Voice Assistant

A natural and conversational voice assistant that can control your laptop and perform various tasks without requiring trigger phrases.

## Features

- Natural conversation in both English and Hindi
- No trigger phrases required (always listening)
- System controls (volume, screenshot, etc.)
- Media playback controls
- Application launching
- YouTube search integration
- Automatic sleep mode after inactivity
- Message saving

## Requirements

- Python 3.7 or higher
- Microphone
- Internet connection (for speech recognition and translation)

## Installation

1. Install required packages:

```
pip install -r requirements.txt
```

2. Run the program:

```
python advanced_voice_assistant.py
```

## How It Works

1. The assistant is always active and listening for commands
2. Speak naturally in English or Hindi
3. The system will automatically detect your language and respond accordingly
4. After 2 minutes of inactivity, it goes into sleep mode to save resources
5. Any voice command will wake it up again

## Command Examples

### System Controls in English
- "Open Chrome"
- "Lock my computer"
- "Take a screenshot"
- "Volume up" or "Increase volume"
- "Volume down" or "Decrease volume"
- "Mute"

### System Controls in Hindi
- "क्रोम खोलो" (Open Chrome)
- "कंप्यूटर लॉक करो" (Lock computer)
- "स्क्रीनशॉट लो" (Take screenshot)
- "आवाज बढ़ाओ" (Volume up)
- "आवाज कम करो" (Volume down)
- "म्यूट करो" (Mute)

### YouTube Commands
- "Open YouTube and search for how to make pasta"
- "यूट्यूब खोलो और ताजमहल के बारे में खोजो" (Open YouTube and search about Taj Mahal)

### Information Queries
- "What time is it?"
- "What's today's date?"
- "Battery status"
- "समय क्या है?" (What time is it?)
- "आज कौन सा दिन है?" (What day is today?)
- "बैटरी स्टेटस" (Battery status)

### Save Messages
- "Save this message: remember to call mom"
- "मैसेज सेव करो: कल मीटिंग है" (Save message: there's a meeting tomorrow)

## Exiting the Program

- Say "Stop", "Exit", or "Quit" to stop the program
- Say "बंद करो" (Close) or "बाहर" (Exit) in Hindi
- Press the 'q' key on your keyboard

## Note

For optimal performance, ensure you have a good quality microphone and a quiet environment. 
Hindi support requires an internet connection for translation services. 