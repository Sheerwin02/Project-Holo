import sys
import speech_recognition as sr
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QCheckBox
from PyQt6.QtCore import pyqtSignal, QThread
from gradio_client import Client
import soundfile as sf
import sounddevice as sd

sys.path.append('../server')
from assistant import get_completion
from utils import get_current_location, get_weather, get_news_updates

funcs = [get_current_location, get_weather, get_news_updates]

API_URL = "https://xzjosh-azuma-bert-vits2-0-2.hf.space/--replicas/v0fs1/"
# Initialize the Gradio client
try:
    print(f"Connecting to API at {API_URL}")
    client = Client(API_URL)
    print("Connected successfully.")
except ValueError as e:
    print(f"Error connecting to API: {e}")
    sys.exit(1)


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


class TextToSpeechThread(QThread):
    error_occurred = pyqtSignal(str)
    audio_ready = pyqtSignal(str, str)  # Include text in the signal

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            result = client.predict(
                self.text,  # input text
                "东雪莲",  # voice type
                0.2,  # SDP/DP slider value
                0.7,  # float (numeric value between 0.1 and 2) in '感情' Slider component
                0.9,  # 音素长度 slider value
                1.0,  # 语速 slider value
                "EN",  # Language type
                False,  # bool  in '按句切分    在按段落切分的基础上再按句子切分文本' Checkbox component
                0.2,  # float (numeric value between 0 and 10) in '段间停顿(秒)，需要大于句间停顿才有效' Slider component
                1,  # float (numeric value between 0 and 5) in '句间停顿(秒)，勾选按句切分才生效' Slider component
                api_name="/tts_split"
            )
            audio_path = result[1]  # The audio file path
            self.audio_ready.emit(audio_path, self.text)  # Emit the signal with the audio path and text
        except Exception as e:
            self.error_occurred.emit(f"Error in TTS: {e}")


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

        self.audio_checkbox = QCheckBox("Enable Audio", self)
        self.audio_checkbox.setChecked(True)
        button_layout.addWidget(self.audio_checkbox)

        self.layout.addLayout(button_layout)
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
            # Display the chat bubble first
            self.response_received.emit(f"Assistant: {text}")

            # Play the audio
            data, samplerate = sf.read(audio_path)
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            self.handle_error(f"Error playing audio: {e}")

    def closeEvent(self, event):
        self.hide()
        event.ignore()
