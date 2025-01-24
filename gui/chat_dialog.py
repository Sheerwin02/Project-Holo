import sys
import speech_recognition as sr
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QCheckBox, QInputDialog, QLabel
from PyQt6.QtCore import pyqtSignal, QThread, Qt
import soundfile as sf
import sounddevice as sd
import logging

sys.path.append('../server')
from assistant import get_completion
from utils import get_current_location, get_weather, get_news_updates
from announce_news import NewsAnnouncer
from tts_thread import TextToSpeechThread

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

funcs = [get_current_location, get_weather, get_news_updates]

class SpeechToTextThread(QThread):
    recognized_text = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def run(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        try:
            with microphone as source:
                audio = recognizer.listen(source)
            user_message = recognizer.recognize_google(audio)
            self.recognized_text.emit(user_message)
        except sr.RequestError:
            self.error_occurred.emit("API unavailable")
        except sr.UnknownValueError:
            self.error_occurred.emit("Unable to recognize speech")

class NewsAnnouncementThread(QThread):
    announcement_complete = pyqtSignal(str)
    news_text_ready = pyqtSignal(str)

    def __init__(self, topic, use_audio):
        super().__init__()
        self.topic = topic
        self.use_audio = use_audio
        self.news_announcer = NewsAnnouncer(topic)
        self.news_announcer.announcement_complete.connect(self.announcement_complete.emit)
        self.news_announcer.news_text_ready.connect(self.news_text_ready.emit)

    def run(self):
        if self.use_audio:
            self.news_announcer.announce_news()
        else:
            news_text = self.news_announcer.fetch_news()
            self.news_text_ready.emit(news_text)
            self.announcement_complete.emit("Announcement complete.")

class ChatDialog(QDialog):
    response_received = pyqtSignal(str)

    def __init__(self, assistant_id, thread_id):
        super().__init__()
        self.assistant_id = assistant_id
        self.thread_id = thread_id

        self.setWindowTitle("Chat with Assistant")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.user_input = QLineEdit(self)
        self.layout.addWidget(self.user_input)

        button_layout = QHBoxLayout()

        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)

        self.speech_button = QPushButton("Speak", self)
        self.speech_button.clicked.connect(self.speech_to_text)
        button_layout.addWidget(self.speech_button)

        self.announce_news_button = QPushButton("Announce News", self)
        self.announce_news_button.clicked.connect(self.announce_news)
        button_layout.addWidget(self.announce_news_button)

        self.audio_checkbox = QCheckBox("Enable Audio", self)
        self.audio_checkbox.setChecked(True)
        button_layout.addWidget(self.audio_checkbox)

        self.layout.addLayout(button_layout)

        # Add loading label
        self.loading_label = QLabel("Holo is currently finding the news for you", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide()
        self.layout.addWidget(self.loading_label)

        self.setLayout(self.layout)

    def send_message(self):
        user_message = self.user_input.text()
        if user_message:
            self.user_input.clear()
            self.response_received.emit(f"You: {user_message}")
            assistant_response = get_completion(self.assistant_id, self.thread_id, user_message, funcs, debug=True)
            if self.audio_checkbox.isChecked():
                self.tts_thread = TextToSpeechThread(assistant_response)
                self.tts_thread.audio_ready.connect(self.play_audio_and_display_bubble)
                self.tts_thread.error_occurred.connect(self.handle_error)
                self.tts_thread.start()
            else:
                self.response_received.emit(f"Assistant: {assistant_response}")

    def speech_to_text(self):
        self.speech_thread = SpeechToTextThread()
        self.speech_thread.recognized_text.connect(self.handle_recognized_text)
        self.speech_thread.error_occurred.connect(self.handle_error)
        self.speech_thread.start()

    def handle_recognized_text(self, text):
        self.user_input.setText(text)
        self.response_received.emit(f"You (spoken): {text}")
        self.send_message()

    def handle_error(self, error_message):
        self.response_received.emit(error_message)
        QMessageBox.warning(self, "Error", error_message)

    def play_audio_and_display_bubble(self, audio_path, text):
        try:
            self.response_received.emit(f"Assistant: {text}")

            data, samplerate = sf.read(audio_path)
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            self.handle_error(f"Error playing audio: {e}")

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def announce_news(self):
        topic, ok = QInputDialog.getText(self, "News Topic", "Enter the topic for news updates:")
        if ok and topic:
            logging.info(f"Announcing news for topic: {topic}")
            self.loading_label.show()
            self.news_thread = NewsAnnouncementThread(topic, self.audio_checkbox.isChecked())
            self.news_thread.announcement_complete.connect(self.display_announcement_status)
            self.news_thread.news_text_ready.connect(self.display_news_text)
            self.news_thread.start()

    def display_news_text(self, news_text):
        self.response_received.emit(f"News: {news_text}")

    def display_announcement_status(self, status):
        self.loading_label.hide()
        QMessageBox.information(self, "Announcement Status", status)
