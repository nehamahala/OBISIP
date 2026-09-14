# Neha Voice Assistant — Browser Edition

## Oasis Infobyte Python Programming — Voice Assistant Task

This version avoids the PyAudio/Visual C++ setup problem by using the browser's built-in Speech Recognition for microphone input. The Python Flask backend handles command routing, calculations, and web actions.

### Features
- Voice input from browser microphone
- Text-to-speech responses
- Time/date
- Safe calculations
- Google, YouTube, GitHub, Gmail, Maps, LinkedIn
- Web search
- Weather search
- Built-in Help
- Quick-action dashboard
- Conversation log
- Responsive UI
- No PyAudio required

### Run

Install Flask:
```powershell
py -m pip install flask
```

Run:
```powershell
py app.py
```

The browser opens at:
`http://127.0.0.1:5002`

Use Chrome or Microsoft Edge and allow microphone access when asked.

### Demo commands
- What is the time?
- What is today's date?
- Calculate 25 times 4
- Open YouTube
- Search Python programming
- Weather in Delhi
- Help
