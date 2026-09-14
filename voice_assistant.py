"""
NEHA VOICE ASSISTANT — Advanced Edition
Oasis Infobyte Python Programming Internship — Voice Assistant Task

Core capabilities:
- Speech recognition + text-to-speech
- GUI conversation dashboard
- Date/time/day
- Web search
- Google / YouTube / GitHub / Gmail / Maps shortcuts
- Calculator expressions
- Open websites and Windows apps where available
- Notes: add/list/clear notes
- Tasks: add/list/complete/clear tasks
- Reminders with scheduled popups
- Weather via browser search (no API key required)
- Quick knowledge answers via Wikipedia page search
- Clipboard helper
- Command history
- Repeat last command
- Help / command suggestions
- Continuous listening mode

Install:
    py -m pip install SpeechRecognition pyttsx3 PyAudio
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import math
import operator
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from tkinter import messagebox

import tkinter as tk
from tkinter import ttk

import pyttsx3
import speech_recognition as sr


APP_NAME = "Neha Voice Assistant"
DATA_DIR = Path(__file__).resolve().parent / "data"
NOTES_FILE = DATA_DIR / "notes.json"
TASKS_FILE = DATA_DIR / "tasks.json"


def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]", encoding="utf-8")
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------- Safe calculator ----------
_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_ALLOWED_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_calculate(expression: str) -> float:
    expression = expression.lower().replace("x", "*").replace("÷", "/")
    expression = expression.replace("π", str(math.pi))
    expression = expression.replace("^", "**")

    allowed_names = {
        "pi": math.pi,
        "e": math.e,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log10,
        "ln": math.log,
        "abs": abs,
        "round": round,
    }

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = visit(node.left)
            right = visit(node.right)
            value = _ALLOWED_BINOPS[type(node.op)](left, right)
            if abs(value) > 1e100:
                raise ValueError("Result is too large.")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = allowed_names.get(node.func.id)
            if fn is None:
                raise ValueError("Function not allowed.")
            return fn(*(visit(arg) for arg in node.args))
        if isinstance(node, ast.Name) and node.id in allowed_names:
            return allowed_names[node.id]
        raise ValueError("Unsupported expression.")

    tree = ast.parse(expression, mode="eval")
    result = visit(tree)
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        raise ValueError("Invalid result.")
    return result


class VoiceAssistantApp:
    def __init__(self, root: tk.Tk):
        ensure_data_files()

        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1120x760")
        self.root.minsize(960, 680)

        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)

        self.running = True
        self.listening = False
        self.continuous_mode = False
        self.last_command = ""
        self.history = []
        self.reminders = []

        self.status = tk.StringVar(value="Ready")
        self.mic_status = tk.StringVar(value="Microphone: idle")
        self.command_preview = tk.StringVar(value="—")
        self.response_preview = tk.StringVar(value="—")
        self.voice_enabled = tk.BooleanVar(value=True)
        self.continuous_enabled = tk.BooleanVar(value=False)

        self.build_ui()
        self.write_log("Assistant", "Hello! I'm ready. Click Listen or enable Continuous Mode.")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------- UI ----------
    def build_ui(self):
        self.root.configure(bg="#090c12")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#090c12")
        style.configure("Card.TLabelframe", background="#111722", foreground="#f4f7fb",
                        padding=14)
        style.configure("Card.TLabelframe.Label", background="#111722",
                        foreground="#8fe8ff", font=("Segoe UI", 11, "bold"))
        style.configure("Title.TLabel", background="#090c12", foreground="#f5f7fb",
                        font=("Segoe UI", 25, "bold"))
        style.configure("Sub.TLabel", background="#090c12", foreground="#8894a8",
                        font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#111722", foreground="#7fe4ff",
                        font=("Segoe UI", 12, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=9)

        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="NEHA VOICE ASSISTANT", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Advanced Python assistant • Voice • Web • Productivity • Automation",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        dashboard = ttk.Frame(outer)
        dashboard.pack(fill="x")

        status_card = ttk.LabelFrame(dashboard, text="Assistant Status",
                                      style="Card.TLabelframe")
        status_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ttk.Label(status_card, textvariable=self.status,
                  style="Status.TLabel").pack(anchor="w")
        ttk.Label(status_card, textvariable=self.mic_status).pack(anchor="w", pady=(5, 0))

        control_card = ttk.LabelFrame(dashboard, text="Controls",
                                      style="Card.TLabelframe")
        control_card.pack(side="left", fill="both", expand=True, padx=(8, 8))

        ttk.Button(control_card, text="🎙 Listen", command=self.start_listening).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(control_card, text="Repeat", command=self.repeat_last).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(control_card, text="Clear Log", command=self.clear_log).pack(
            side="left"
        )

        options_card = ttk.LabelFrame(dashboard, text="Modes",
                                      style="Card.TLabelframe")
        options_card.pack(side="left", fill="both", expand=True, padx=(8, 0))

        ttk.Checkbutton(
            options_card, text="Voice response",
            variable=self.voice_enabled
        ).pack(anchor="w")
        ttk.Checkbutton(
            options_card, text="Continuous listening",
            variable=self.continuous_enabled,
            command=self.toggle_continuous
        ).pack(anchor="w")

        body = ttk.Panedwindow(outer, orient="horizontal")
        body.pack(fill="both", expand=True, pady=(18, 0))

        chat_frame = ttk.LabelFrame(body, text="Conversation", style="Card.TLabelframe")
        body.add(chat_frame, weight=4)

        self.log = tk.Text(
            chat_frame,
            wrap="word",
            font=("Consolas", 10.5),
            bg="#0a0f17",
            fg="#e9eef7",
            insertbackground="white",
            relief="flat",
            padx=14,
            pady=14,
            state="disabled",
        )
        self.log.pack(fill="both", expand=True)

        side = ttk.Frame(body)
        body.add(side, weight=2)

        info = ttk.LabelFrame(side, text="Latest Command", style="Card.TLabelframe")
        info.pack(fill="x")
        ttk.Label(info, textvariable=self.command_preview, wraplength=290).pack(anchor="w")

        info2 = ttk.LabelFrame(side, text="Latest Response", style="Card.TLabelframe")
        info2.pack(fill="x", pady=(12, 0))
        ttk.Label(info2, textvariable=self.response_preview, wraplength=290).pack(anchor="w")

        quick = ttk.LabelFrame(side, text="Quick Actions", style="Card.TLabelframe")
        quick.pack(fill="x", pady=(12, 0))

        actions = [
            ("Open Google", "open google"),
            ("Open YouTube", "open youtube"),
            ("Open GitHub", "open github"),
            ("Open Gmail", "open gmail"),
            ("Search Python", "search python programming"),
            ("Show Help", "help"),
        ]
        for label, command in actions:
            ttk.Button(
                quick, text=label, command=lambda c=command: self.process_command(c)
            ).pack(fill="x", pady=3)

        history_card = ttk.LabelFrame(side, text="Recent Commands",
                                      style="Card.TLabelframe")
        history_card.pack(fill="both", expand=True, pady=(12, 0))

        self.history_list = tk.Listbox(
            history_card,
            bg="#0a0f17",
            fg="#cbd5e1",
            relief="flat",
            highlightthickness=0,
        )
        self.history_list.pack(fill="both", expand=True)

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(
            footer,
            text="Try: 'calculate 25 times 4' • 'take a note' • 'add task' • 'remind me in 1 minute' • 'weather in Delhi'",
            style="Sub.TLabel",
        ).pack(anchor="w")

    # ---------- Conversation ----------
    def write_log(self, speaker: str, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", f"{speaker}: {text}\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.response_preview.set(text)

    def respond(self, text: str):
        self.root.after(0, lambda: self.write_log("Assistant", text))
        if self.voice_enabled.get():
            def speak():
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception:
                    pass
            threading.Thread(target=speak, daemon=True).start()

    def update_status(self, text: str):
        self.root.after(0, lambda: self.status.set(text))

    # ---------- Listening ----------
    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.mic_status.set("Microphone: listening…")
        self.status.set("Listening…")
        threading.Thread(target=self.listen_once, daemon=True).start()

    def listen_once(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=9)

            self.update_status("Recognizing…")
            command = self.recognizer.recognize_google(audio).lower().strip()
            self.root.after(0, lambda c=command: self.process_command(c))

        except sr.WaitTimeoutError:
            self.respond("I did not hear anything. Please try again.")
        except sr.UnknownValueError:
            self.respond("I could not understand that. Please speak clearly.")
        except sr.RequestError:
            self.respond("Speech recognition is unavailable right now. Check your internet connection.")
        except OSError:
            self.respond("I could not access the microphone. Please check Windows microphone permission.")
        finally:
            self.root.after(0, self.finish_listening)

    def finish_listening(self):
        self.listening = False
        self.mic_status.set("Microphone: idle")
        self.status.set("Ready")

        if self.continuous_enabled.get() and self.running:
            self.root.after(700, self.start_listening)

    def toggle_continuous(self):
        self.continuous_mode = self.continuous_enabled.get()
        if self.continuous_mode and not self.listening:
            self.start_listening()

    # ---------- Commands ----------
    def process_command(self, command: str):
        command = command.strip().lower()
        if not command:
            return

        self.last_command = command
        self.command_preview.set(command)
        self.history.insert(0, command)
        self.history = [command] + [x for x in self.history if x != command]
        self.history = self.history[:30]

        self.write_log("You", command)

        if command in {"help", "commands", "what can you do"}:
            self.respond(
                "I can handle web search, time and date, calculations, notes, tasks, "
                "reminders, weather search, Wikipedia lookup, browser shortcuts, "
                "clipboard, repeated commands and continuous listening."
            )
            return

        if command in {"repeat", "repeat last command"}:
            self.repeat_last()
            return

        if any(word in command for word in ("goodbye", "exit", "quit", "close assistant")):
            self.respond("Goodbye! See you next time.")
            self.close()
            return

        # Time/date
        if "time" in command and "timer" not in command:
            now = dt.datetime.now().strftime("%I:%M %p")
            self.respond(f"The current time is {now}.")
            return

        if "date" in command or "day is it" in command or "today" == command:
            today = dt.datetime.now().strftime("%A, %d %B %Y")
            self.respond(f"Today is {today}.")
            return

        # Open common services
        sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "gmail": "https://mail.google.com",
            "maps": "https://maps.google.com",
            "linkedin": "https://www.linkedin.com",
        }
        for key, url in sites.items():
            if command in {f"open {key}", key}:
                webbrowser.open(url)
                self.respond(f"Opening {key.capitalize()}.")
                return

        # Web search
        if command.startswith("search "):
            query = command[7:].strip()
            if query:
                webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
                self.respond(f"Searching the web for {query}.")
            return

        # Weather
        if command.startswith("weather"):
            location = command.replace("weather", "", 1).replace("in", "", 1).strip()
            if not location:
                location = "my location"
            query = f"weather {location}"
            webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
            self.respond(f"Showing weather information for {location}.")
            return

        # Wikipedia / knowledge lookup
        if command.startswith(("who is ", "what is ", "tell me about ")):
            phrase = command.replace("who is ", "", 1)
            phrase = phrase.replace("what is ", "", 1)
            phrase = phrase.replace("tell me about ", "", 1).strip()
            if phrase:
                webbrowser.open(
                    "https://en.wikipedia.org/w/index.php?search=" + phrase.replace(" ", "+")
                )
                self.respond(f"Opening a Wikipedia result for {phrase}.")
                return

        # Calculator
        calc_prefixes = ("calculate ", "what is ", "solve ")
        calc_text = None
        for prefix in calc_prefixes:
            if command.startswith(prefix):
                calc_text = command[len(prefix):]
                break
        if calc_text and any(ch.isdigit() for ch in calc_text):
            normalized = (
                calc_text.replace("plus", "+")
                .replace("minus", "-")
                .replace("multiplied by", "*")
                .replace("times", "*")
                .replace("divided by", "/")
                .replace("power of", "**")
            )
            try:
                result = safe_calculate(normalized)
                self.respond(f"The answer is {result:g}.")
            except Exception:
                self.respond("I could not calculate that expression safely.")
            return

        # Notes
        if command.startswith(("take a note ", "note ", "remember ")):
            text = command
            for prefix in ("take a note ", "note ", "remember "):
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            if text:
                notes = load_json(NOTES_FILE)
                notes.append({
                    "text": text,
                    "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_json(NOTES_FILE, notes)
                self.respond("Note saved successfully.")
            return

        if command in {"show notes", "list notes", "my notes"}:
            notes = load_json(NOTES_FILE)
            if not notes:
                self.respond("You do not have any saved notes.")
            else:
                latest = notes[-5:]
                summary = "; ".join(item["text"] for item in latest)
                self.respond(f"Your latest notes are: {summary}.")
            return

        if command in {"clear notes", "delete notes"}:
            save_json(NOTES_FILE, [])
            self.respond("All notes cleared.")
            return

        # Tasks
        if command.startswith(("add task ", "task ")):
            text = command.replace("add task ", "", 1).replace("task ", "", 1).strip()
            if text:
                tasks = load_json(TASKS_FILE)
                tasks.append({"text": text, "done": False, "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M")})
                save_json(TASKS_FILE, tasks)
                self.respond("Task added.")
            return

        if command in {"show tasks", "list tasks", "my tasks"}:
            tasks = load_json(TASKS_FILE)
            pending = [t["text"] for t in tasks if not t.get("done")]
            if not pending:
                self.respond("You have no pending tasks.")
            else:
                self.respond("Your pending tasks are: " + "; ".join(pending[:5]) + ".")
            return

        if command in {"complete task", "complete last task"}:
            tasks = load_json(TASKS_FILE)
            for item in reversed(tasks):
                if not item.get("done"):
                    item["done"] = True
                    save_json(TASKS_FILE, tasks)
                    self.respond(f"Completed task: {item['text']}.")
                    return
            self.respond("There is no pending task to complete.")
            return

        # Reminder: simple "in N minute(s)" / "in N hour(s)"
        if command.startswith("remind me in "):
            self.create_reminder_from_command(command)
            return

        # Clipboard
        if command.startswith("copy "):
            text = command[5:].strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            self.respond("Copied that text to the clipboard.")
            return

        if command in {"clear clipboard"}:
            self.root.clipboard_clear()
            self.respond("Clipboard cleared.")
            return

        self.respond(
            "I do not know that command yet. Try 'help' to see the main features."
        )

    # ---------- Reminder ----------
    def create_reminder_from_command(self, command: str):
        words = command.split()
        try:
            # command: remind me in <number> <unit> <message...>
            value = int(words[3])
            unit = words[4]
            message = " ".join(words[5:]).strip() or "Reminder"
            if unit.startswith("min"):
                seconds = value * 60
            elif unit.startswith("hour"):
                seconds = value * 3600
            else:
                raise ValueError

            self.respond(f"Okay. I will remind you in {value} {unit}.")
            threading.Thread(
                target=self.reminder_worker,
                args=(seconds, message),
                daemon=True,
            ).start()

        except (IndexError, ValueError):
            self.respond(
                "Use a reminder like: remind me in 5 minutes submit my internship task."
            )

    def reminder_worker(self, seconds: int, message: str):
        time.sleep(max(1, seconds))
        if not self.running:
            return
        self.root.after(0, lambda: self.show_reminder(message))

    def show_reminder(self, message: str):
        self.respond(f"Reminder: {message}")
        try:
            messagebox.showinfo("Neha Voice Assistant — Reminder", message)
        except tk.TclError:
            pass

    # ---------- Utility ----------
    def repeat_last(self):
        if self.last_command:
            self.respond(f"Repeating: {self.last_command}.")
            self.root.after(500, lambda: self.process_command(self.last_command))
        else:
            self.respond("There is no previous command yet.")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.command_preview.set("—")
        self.response_preview.set("—")

    def close(self):
        self.running = False
        try:
            self.engine.stop()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    VoiceAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
