# NEHA VOICE ASSISTANT — Advanced Edition

## Oasis Infobyte — Python Programming Internship
### Task 1: Voice Assistant

A feature-rich Python voice assistant with a desktop GUI.

### Core features
- Speech recognition with `SpeechRecognition`
- Text-to-speech with `pyttsx3`
- Continuous listening mode
- Time, date and day
- Google / YouTube / GitHub / Gmail / Maps / LinkedIn
- Web search
- Weather search without an API key
- Wikipedia lookup
- Safe mathematical calculator
- Notes stored locally
- Task list stored locally
- Simple reminders
- Clipboard helper
- Command history
- Repeat last command
- Built-in help
- Friendly microphone/internet error handling
- Non-blocking background listening and reminders

## Installation

Open the project folder in VS Code and run:

```powershell
py -m pip install SpeechRecognition pyttsx3 PyAudio
```

## Run

```powershell
py voice_assistant.py
```

A desktop GUI will open.

## Demo script

For a clean demo, try these commands:

1. `What is the time?`
2. `What is today's date?`
3. `Calculate 25 times 4`
4. `Open YouTube`
5. `Search Python programming`
6. `Weather in Delhi`
7. `Take a note submit internship`
8. `Show notes`
9. `Add task upload GitHub`
10. `Show tasks`
11. `Remind me in 1 minute demo reminder`
12. `Help`

## Notes

Speech recognition uses an online speech-recognition service, so internet access is needed for voice-to-text.
The app stores notes and tasks locally in the `data` folder.
