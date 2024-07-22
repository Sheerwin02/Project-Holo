import sys
import speech_recognition as sr
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

sys.path.append('../server') 
from assistant import get_completion
from utils import get_current_location, get_weather, get_news_updates

funcs = [get_current_location, get_weather, get_news_updates]

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

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def send_message(self):
        user_message = self.user_input.text()
        if user_message:
            self.user_input.clear()
            assistant_response = get_completion(self.assistant_id, self.thread_id, user_message, funcs, debug=True)
            self.response_received.emit(f"You: {user_message}")
            self.response_received.emit(f"Assistant: {assistant_response}")

    def speech_to_text(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        try:
            with microphone as source:
                self.response_received.emit("Listening...")
                audio = recognizer.listen(source)
            self.response_received.emit("Processing...")

            user_message = recognizer.recognize_google(audio)
            self.user_input.setText(user_message)
            self.response_received.emit(f"You (spoken): {user_message}")
            self.send_message()
        except sr.RequestError:
            self.response_received.emit("API unavailable")
            QMessageBox.warning(self, "Error", "API unavailable")
        except sr.UnknownValueError:
            self.response_received.emit("Unable to recognize speech")
            QMessageBox.warning(self, "Error", "Unable to recognize speech")

    def closeEvent(self, event):
        self.hide()
        event.ignore()
