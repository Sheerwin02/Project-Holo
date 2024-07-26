import sys
from PyQt6.QtCore import QThread, pyqtSignal
from gradio_client import Client
import soundfile as sf
import sounddevice as sd

API_URL = "https://xzjosh-azuma-bert-vits2-0-2.hf.space/--replicas/v0fs1/"
# Initialize the Gradio client
try:
    print(f"Connecting to API at {API_URL}")
    client = Client(API_URL)
    print("Connected successfully.")
except ValueError as e:
    print(f"Error connecting to API: {e}")
    sys.exit(1)


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
                0.5,  # float (numeric value between 0.1 and 2) in '感情' Slider component
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
