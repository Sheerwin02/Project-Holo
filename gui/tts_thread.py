import sys
from PyQt6.QtCore import QThread, pyqtSignal
from gradio_client import Client
import soundfile as sf
import sounddevice as sd

# API_URL = "https://xzjosh-azuma-bert-vits2-0-2.hf.space/--replicas/v0fs1/"
# API_URL = "https://xzjosh-azuma-bert-vits2-0-2.hf.space/--replicas/lyypv/"
API_URL = "https://xzjosh-azuma-bert-vits2-2-3.hf.space/--replicas/ys8hc/"
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
                0.5,  # float (numeric value between 0.1 and 2) 
                0.9,  # 音素长度 slider value
                1.0,  # 语速 slider value
                "EN",  # Language type
                False,  # bool 
                0.2,  # float (numeric value between 0 and 10) 
                1,  # float (numeric value between 0 and 5) in 
                api_name="/tts_split"
            )
            audio_path = result[1]  # The audio file path
            self.audio_ready.emit(audio_path, self.text)  # Emit the signal with the audio path and text
        except Exception as e:
            self.error_occurred.emit(f"Error in TTS: {e}")
