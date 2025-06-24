import sys
import os
import uuid
import subprocess
import threading
import time
import requests
import webbrowser
import speech_recognition as sr

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal

# ========== ElevenLabs TTS ==========
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables for API keys
load_dotenv()

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

BRIAN_VOICE_ID = "N2lVS1w4EtoT3dr4eOWO"


def play_audio_ffplay(file_path):
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", file_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def speak(text):
    filename = f"jarvis_{uuid.uuid4().hex}.mp3"
    audio_generator = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=BRIAN_VOICE_ID,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128"
    )

    with open(filename, "wb") as f:
        f.write(b"".join(audio_generator))
    play_audio_ffplay(filename)
    os.remove(filename)


# ========== Music Library ==========
music = {
    "stealth": "https://www.youtube.com/watch?v=U47Tr9BB_wE",
    "believer": "https://www.youtube.com/watch?v=SBlotdJ_m6w",
    "titanium": "https://www.youtube.com/watch?v=hVXAVgKZmdE",
    "senorita": "https://www.youtube.com/watch?v=jolndjJptuU",
    "darkside": "https://www.youtube.com/watch?v=fbfXftG3ZwI",
    "royal": "https://www.youtube.com/watch?v=3u8HXTCDUe8",
    "dandelions": "https://www.youtube.com/watch?v=waWhUT6HSz0",
    "faded": "https://www.youtube.com/watch?v=ZQSIPD9ykq0",
    "wednesday": "https://www.youtube.com/watch?v=MsXdUtlDVhk",
    "mouse": "https://www.youtube.com/watch?v=UK-vT8iapA8&list=PLhzSo-ru1Zb-FidpXh8KOTDEjxQ5QZdUh&index=5",
    "battle": "https://www.youtube.com/watch?v=7OVMrhfXHfg&list=PLhzSo-ru1Zb-FidpXh8KOTDEjxQ5QZdUh&index=8",
    "singh": "https://www.youtube.com/watch?v=dtqI1LkI268&list=PLhzSo-ru1Zb-FidpXh8KOTDEjxQ5QZdUh&index=3",
    "race": "https://www.youtube.com/watch?v=SNq4VxhzaoQ",
    "princess": "https://www.youtube.com/watch?v=ICUMGYHYBKY",
    "go": "https://www.youtube.com/watch?v=L0MK7qz13bU",
    "found": "https://www.youtube.com/watch?v=dpza2z4jmDk",
    "show": "https://www.youtube.com/watch?v=nrZxwPwmgrw",
    "save": "https://www.youtube.com/watch?v=YDGNmqa8hO8"
}


# ========== OpenAI API ==========
from openai import OpenAI

OPENAI_API_KEY = os.getenv("Your Open Ai Api Key") or ""
client = OpenAI(
    api_key="Your Open Ai Api Key"
)


def ai_process(command):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "system", "content": "You are a virtual assistant named Jarvis, skilled in general tasks like Alexa and Google Cloud. Give short responses please."},
                {"role": "user", "content": command}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI processing error: {e}"


# ========== PyQt5 GUI Components ==========
class HoverButton(QtWidgets.QPushButton):
    def __init__(self, icon=None, text="", tooltip="", parent=None):
        super().__init__(text, parent=parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.icon_size = 32
        if icon:
            self.setIcon(icon)
            self.setIconSize(QtCore.QSize(self.icon_size, self.icon_size))
        self.setToolTip(tooltip)

        self.setCheckable(True)
        self.setStyleSheet(self.default_style())
        self.installEventFilter(self)

    def default_style(self):
        return """
            QPushButton {
                color: #c8d0e7;
                background: transparent;
                border: none;
                padding: 8px 16px;
                text-align: left;
                font: 14px 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 rgba(86, 180, 250, 0.6),
                                            stop:1 rgba(29, 79, 114, 0.8));
                color: #e0f0ff;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #3c7edb,
                                            stop:1 #1a3e72);
                color: white;
                font-weight: bold;
            }
        """

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.HoverEnter:
            self.setStyleSheet(self.default_style())
        elif event.type() == QtCore.QEvent.HoverLeave:
            if self.isChecked():
                self.setStyleSheet(self.default_style())
            else:
                self.setStyleSheet(self.default_style())
        return super().eventFilter(obj, event)


class JarvisGUI(QtWidgets.QMainWindow):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self):
        super(JarvisGUI, self).__init__()

        self.setWindowTitle("JARVIS - Futuristic Interface")
        self.setMinimumSize(1024, 640)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowSystemMenuHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.is_listening = False
        self.voice_thread = None

        # Central widget and layout
        central_widget = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Main frame with glass style
        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet("""
            #mainFrame {
                background: rgba(18, 18, 26, 0.85);
                border-radius: 16px;
                border: 1px solid rgba(86, 180, 250, 0.25);
            }
        """)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.main_frame.setLayout(main_layout)

        # Header bar (glass morphism)
        self.header = QtWidgets.QFrame()
        self.header.setObjectName("header")
        self.header.setFixedHeight(64)
        self.header.setStyleSheet("""
            #header {
                background: rgba(10, 10, 20, 0.6);
                border-bottom: 1px solid rgba(86, 180, 250, 0.35);
                backdrop-filter: blur(15px);
                -webkit-backdrop-filter: blur(15px);
            }
        """)
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(12)
        self.header.setLayout(header_layout)

        # Brand / Logo label
        self.brand_label = QtWidgets.QLabel("JARVIS")
        font = QtGui.QFont("Orbitron", 18, QtGui.QFont.Bold)
        self.brand_label.setFont(font)
        self.brand_label.setStyleSheet("color: #56b4fa; letter-spacing: 3px;")
        header_layout.addWidget(self.brand_label, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        header_layout.addStretch()

        # Header control buttons (min, max, close)
        self.min_button = QtWidgets.QPushButton("")
        self.min_button.setFixedSize(36, 36)
        self.min_button.setToolTip("Minimize")
        self.min_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarMinButton))
        self.min_button.setStyleSheet(self.header_button_style())
        self.min_button.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.min_button)

        self.max_button = QtWidgets.QPushButton("")
        self.max_button.setFixedSize(36, 36)
        self.max_button.setToolTip("Maximize")
        self.max_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarMaxButton))
        self.max_button.setStyleSheet(self.header_button_style())
        self.max_button.clicked.connect(self.toggle_max_restore)
        header_layout.addWidget(self.max_button)

        self.close_button = QtWidgets.QPushButton("")
        self.close_button.setFixedSize(36, 36)
        self.close_button.setToolTip("Close")
        self.close_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))
        self.close_button.setStyleSheet(self.header_button_style(close=True))
        self.close_button.clicked.connect(self.close)
        header_layout.addWidget(self.close_button)

        # Body container for sidebar and main content
        body_container = QtWidgets.QWidget()
        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_container.setLayout(body_layout)

        # Sidebar frame
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            #sidebar {
                background: rgba(5, 5, 10, 0.7);
                border-right: 1px solid rgba(86, 180, 250, 0.25);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
            }
        """)
        sidebar_layout = QtWidgets.QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(14)
        self.sidebar.setLayout(sidebar_layout)

        # Sidebar title
        sidebar_title = QtWidgets.QLabel("Modules")
        sidebar_title.setFont(QtGui.QFont("Orbitron", 14, QtGui.QFont.Bold))
        sidebar_title.setStyleSheet("color: #56b4fa; padding-left: 12px; letter-spacing: 2px; margin-bottom: 16px;")
        sidebar_layout.addWidget(sidebar_title)

        # Sidebar buttons
        def create_icon(icon_name):
            style = self.style()
            icon_map = {
                "home": style.standardIcon(QtWidgets.QStyle.SP_ComputerIcon),
                "search": style.standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView),
                "add": style.standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder),
                "edit": style.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView),
                "delete": style.standardIcon(QtWidgets.QStyle.SP_TrashIcon),
                "settings": style.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView),
                "person": style.standardIcon(QtWidgets.QStyle.SP_DirHomeIcon),
                "notifications": style.standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation),
                "help": style.standardIcon(QtWidgets.QStyle.SP_MessageBoxQuestion),
                "power": style.standardIcon(QtWidgets.QStyle.SP_BrowserStop)
            }
            return icon_map.get(icon_name, style.standardIcon(QtWidgets.QStyle.SP_FileIcon))

        buttons_info = [
            ("home", "Home"),
            ("search", "Search"),
            ("add", "Add Data"),
            ("edit", "Edit Data"),
            ("delete", "Delete Data"),
            ("settings", "Settings"),
            ("notifications", "Notifications"),
            ("help", "Help"),
            ("power", "Exit"),
        ]

        self.sidebar_buttons = []
        for icon_name, label_text in buttons_info:
            btn = HoverButton(icon=create_icon(icon_name), text=label_text, tooltip=label_text)
            btn.clicked.connect(self.sidebar_button_clicked)
            self.sidebar_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        # Add start/stop voice assistant button to sidebar
        self.btn_voice = HoverButton(text="Start Voice Assistant", tooltip="Start/stop Jarvis voice assistant")
        self.btn_voice.setCheckable(True)
        self.btn_voice.clicked.connect(self.toggle_voice_assistant)
        sidebar_layout.addWidget(self.btn_voice)

        sidebar_layout.addStretch()

        # Main content area
        self.content_area = QtWidgets.QFrame()
        self.content_area.setStyleSheet("""
            background: transparent;
            color: #c8d0e7;
            padding: 24px;
        """)
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        self.content_area.setLayout(content_layout)

        welcome_label = QtWidgets.QLabel("Welcome to JARVIS Interface")
        welcome_label.setFont(QtGui.QFont("Orbitron", 22, QtGui.QFont.Bold))
        welcome_label.setStyleSheet("color: #56b4fa; letter-spacing: 6px;")
        welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        content_layout.addWidget(welcome_label)

        # Info text area (multi-line)
        self.info_text = QtWidgets.QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QtGui.QFont("Consolas", 11))
        self.info_text.setStyleSheet("""
            background: rgba(20, 20, 30, 0.5);
            border: 2px solid rgba(86, 180, 250, 0.5);
            border-radius: 12px;
            color: #cfd8f1;
            padding: 12px;
        """)
        self.info_text.setText(
            "System status:\n\n"
            "- All systems operational\n"
            "- Awaiting commands\n\n"
            "Select a module from the sidebar or start voice assistant."
        )
        content_layout.addWidget(self.info_text)

        # Action buttons panel
        buttons_panel = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(24)
        buttons_panel.setLayout(buttons_layout)

        # Some example action buttons to show in GUI
        self.btn_show_time = HoverButton(text="Show Time", tooltip="Show current system time")
        self.btn_show_time.clicked.connect(self.action_show_time)
        buttons_layout.addWidget(self.btn_show_time)

        self.btn_clear_log = HoverButton(text="Clear Log", tooltip="Clear system status log")
        self.btn_clear_log.clicked.connect(self.action_clear_log)
        buttons_layout.addWidget(self.btn_clear_log)

        content_layout.addWidget(buttons_panel)

        # Footer bar
        self.footer = QtWidgets.QFrame()
        self.footer.setObjectName("footer")
        self.footer.setFixedHeight(44)
        self.footer.setStyleSheet("""
            #footer {
                background: rgba(10, 10, 20, 0.5);
                border-top: 1px solid rgba(86, 180, 250, 0.25);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                color: #7f8db0;
            }
        """)
        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.setContentsMargins(16, 0, 16, 0)
        self.footer.setLayout(footer_layout)

        self.status_label = QtWidgets.QLabel("Status: Ready")
        self.status_label.setFont(QtGui.QFont("Segoe UI", 10))
        footer_layout.addWidget(self.status_label, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # Social links (dummy)
        footer_layout.addStretch()
        social_icons = ["SP_MediaPlay", "SP_DialogHelpButton", "SP_BrowserReload"]
        for icon in social_icons:
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(32, 32)
            btn.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, icon)))
            btn.setFlat(True)
            btn.setToolTip(icon)
            footer_layout.addWidget(btn)

        # Compose main layout
        main_layout.addWidget(self.header)
        main_layout.addWidget(body_container)
        main_layout.addWidget(self.footer)

        central_layout.addWidget(self.main_frame)
        self.main_frame.layout().addWidget(self.header)
        self.main_frame.layout().addWidget(body_container)
        self.main_frame.layout().addWidget(self.footer)

        # Add sidebar and content area to body layout
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.content_area)

        self.setCentralWidget(central_widget)
        central_widget.setLayout(central_layout)

        # For dragging window (since frameless)
        self.old_pos = None

        # Track maximized state
        self.is_maximized = False

        # Connect signals
        self.log_signal.connect(self.append_log)
        self.status_signal.connect(self.set_status)

    def header_button_style(self, close=False):
        base = """
            QPushButton {
                border: none;
                background: transparent;
                color: #56b4fa;
            }
            QPushButton:hover {
                background-color: %s;
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """
        hover_color = "#ff5555" if close else "rgba(86, 180, 250, 0.3)"
        return base % hover_color

    def toggle_max_restore(self):
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
            self.max_button.setToolTip("Maximize")
        else:
            self.showMaximized()
            self.is_maximized = True
            self.max_button.setToolTip("Restore")

    def sidebar_button_clicked(self):
        sender = self.sender()
        if isinstance(sender, HoverButton):
            self.info_text.append(f"\n[Module Selected] {sender.text()}")

            if sender.text() == "Exit":
                self.close()

    def action_show_time(self):
        current_time = QtCore.QDateTime.currentDateTime().toString("dddd, MMMM d yyyy - hh:mm:ss AP")
        self.info_text.append(f"\n[Action] Current Time: {current_time}")
        self.status_label.setText("Status: Showing current time")
        try:
            speak(f"The current time is {current_time}")
        except Exception:
            pass

    def action_clear_log(self):
        self.info_text.clear()
        self.status_label.setText("Status: Log cleared")

    def append_log(self, message):
        self.info_text.append(f"\n{message}")

    def set_status(self, status):
        self.status_label.setText(f"Status: {status}")

    # Drag window logic for frameless window
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and event.y() <= 64:
            self.old_pos = event.globalPos()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        super().mouseReleaseEvent(event)

    def toggle_voice_assistant(self):
        if self.is_listening:
            self.stop_voice_assistant()
        else:
            self.start_voice_assistant()

    def start_voice_assistant(self):
        self.append_log("[System] Starting voice assistant...")
        self.status_signal.emit("Listening")
        self.is_listening = True
        self.btn_voice.setText("Stop Voice Assistant")
        self.btn_voice.setChecked(True)
        self.voice_thread = VoiceAssistantThread()
        self.voice_thread.log_signal.connect(self.append_log)
        self.voice_thread.status_signal.connect(self.set_status)
        self.voice_thread.finished.connect(self.voice_thread_finished)
        self.voice_thread.start()

    def stop_voice_assistant(self):
        self.append_log("[System] Stopping voice assistant...")
        self.status_signal.emit("Stopped")
        self.is_listening = False
        self.btn_voice.setText("Start Voice Assistant")
        self.btn_voice.setChecked(False)
        if self.voice_thread:
            self.voice_thread.request_interruption()
            self.voice_thread.wait()
            self.voice_thread = None

    def voice_thread_finished(self):
        self.append_log("[System] Voice assistant stopped.")
        self.status_signal.emit("Stopped")
        self.is_listening = False
        self.btn_voice.setText("Start Voice Assistant")
        self.btn_voice.setChecked(False)


# ========== Voice Assistant Thread ==========
class VoiceAssistantThread(QtCore.QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.jarvis_active = False
        self._stop_requested = False

    def run(self):
        # Adjust recognizer energy threshold once
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
        except Exception as e:
            self.log_signal.emit(f"[Voice] Microphone initialization error: {e}")
            return

        self.log_signal.emit("[Voice] Ready, waiting for wake word 'Jarvis'...")

        while not self.isInterruptionRequested() and not self._stop_requested:
            try:
                with self.microphone as source:
                    if not self.jarvis_active:
                        self.status_signal.emit("Waiting for wake word...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                        try:
                            text = self.recognizer.recognize_google(audio).lower()
                            self.log_signal.emit(f"[Voice] Heard: {text}")
                            if "jarvis" in text:
                                self.jarvis_active = True
                                self.status_signal.emit("Activated")
                                self.log_signal.emit("[Voice] Jarvis activated.")
                                speak("Yes sir, I am now active.")
                        except sr.UnknownValueError:
                            continue
                        except sr.RequestError as e:
                            self.log_signal.emit(f"[Voice] Speech recognition error: {e}")
                            self.status_signal.emit("Recognition error")
                            continue
                    else:
                        self.status_signal.emit("Listening for commands...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                        try:
                            text = self.recognizer.recognize_google(audio).lower()
                            self.log_signal.emit(f"[Voice] Command: {text}")

                            if any(kw in text for kw in ["exit", "quit", "goodbye", "sleep now"]):
                                self.jarvis_active = False
                                self.status_signal.emit("Deactivated")
                                self.log_signal.emit("[Voice] Jarvis deactivated.")
                                speak("Deactivating myself, sir. Say 'Jarvis' to wake me again.")
                                continue

                            self.process_command(text)
                        except sr.UnknownValueError:
                            self.log_signal.emit("[Voice] Didn't catch that.")
                            continue
                        except sr.RequestError as e:
                            self.log_signal.emit(f"[Voice] Speech recognition error: {e}")
                            self.status_signal.emit("Recognition error")
                            continue
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                self.log_signal.emit(f"[Voice] Error: {e}")

    def process_command(self, command):
        c = command.lower()
        if "open google" in c:
            speak("My dear sir, I am opening Google for you.")
            webbrowser.open("https://google.com")
            self.log_signal.emit("[Action] Opened Google.")
        elif "open facebook" in c:
            speak("Opening Facebook, my boss.")
            webbrowser.open("https://facebook.com")
            self.log_signal.emit("[Action] Opened Facebook.")
        elif "open youtube" in c:
            speak("Opening YouTube, sir.")
            webbrowser.open("https://youtube.com")
            self.log_signal.emit("[Action] Opened YouTube.")
        elif "open chat gpt" in c:
            speak("Opening ChatGPT, master.")
            webbrowser.open("https://chatgpt.com/")
            self.log_signal.emit("[Action] Opened ChatGPT.")
        elif "open premium plots" in c:
            speak("Opening Premium Plots, market's leader.")
            webbrowser.open("https://premiumplots.netlify.app")
            self.log_signal.emit("[Action] Opened Premium Plots.")
        elif "open plant" in c:
            speak("Opening plant information, my lord.")
            webbrowser.open("https://www.google.com/search?q=what+is+plant")
            self.log_signal.emit("[Action] Opened plant information.")
        elif c.startswith("play"):
            song = c.split(" ")[1] if len(c.split(" ")) > 1 else ""
            link = music.get(song)
            if link:
                webbrowser.open(link)
                speak(f"Playing song {song} for you, sir.")
                self.log_signal.emit(f"[Action] Playing song: {song}")
            else:
                speak(f"Sorry, I couldn't find the song {song}.")
                self.log_signal.emit(f"[Action] Unknown song requested: {song}")
        elif "news" in c:
            api_key = "810ce98daec6496baf3f1293577a4c03"
            try:
                r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}")
                if r.status_code == 200:
                    data = r.json()
                    articles = data.get("articles", [])
                    speak("Here are the top headlines.")
                    self.log_signal.emit("[News] Top Headlines:")
                    for i, article in enumerate(articles, 1):
                        headline = article.get("title", "No title")
                        self.log_signal.emit(f"{i}. {headline}")
                        speak(headline)
                else:
                    speak("Sorry, I couldn't fetch the news.")
                    self.log_signal.emit("[News] Failed to fetch news.")
            except Exception as e:
                self.log_signal.emit(f"[News] Exception: {e}")
                speak("Sorry, there was an error fetching the news.")
        else:
            output = ai_process(c)
            self.log_signal.emit(f"[AI] {output}")
            try:
                speak(output)
            except Exception:
                pass

    def request_interruption(self):
        self._stop_requested = True
        super().requestInterruption()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Load Orbitron font locally or fallback
    from pathlib import Path
    import urllib.request

    def load_orbitron():
        font_path = Path("Orbitron-Regular.ttf")
        if not font_path.exists():
            try:
                url = "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-Regular.ttf"
                urllib.request.urlretrieve(url, font_path)
            except:
                pass
        id_ = QtGui.QFontDatabase.addApplicationFont(str(font_path))
        families = QtGui.QFontDatabase.applicationFontFamilies(id_)
        # Use font if loaded
        if families:
            print(f"Loaded font: {families[0]}")

    load_orbitron()

    jarvis = JarvisGUI()
    jarvis.show()

    sys.exit(app.exec_())

