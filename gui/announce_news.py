import soundfile as sf
import sounddevice as sd
import sys
import logging
from retrying import retry
from PyQt6.QtCore import QObject, pyqtSignal

# Function imports from other modules
sys.path.append('../server')
from utils import get_news_updates
from tts_thread import TextToSpeechThread

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NewsAnnouncer(QObject):
    announcement_complete = pyqtSignal(str)
    news_text_ready = pyqtSignal(str)  # Add this signal

    def __init__(self, topic="technology"):
        super().__init__()
        self.topic = topic
        self.tts_thread = None

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def fetch_news(self):
        logging.info(f"Fetching news updates for topic: {self.topic}")
        news_updates = get_news_updates(self.topic)
        if not news_updates:
            logging.error("Unable to retrieve news updates.")
            raise Exception("Unable to retrieve news updates.")

        # Limit the number of articles or length of text
        max_articles = 3  # Limit to 3 articles
        max_length = 500  # Limit to 500 characters
        truncated_updates = "\n\n".join([article[:max_length] for article in news_updates.split('\n\n')[:max_articles]])
        
        logging.info("News updates fetched and truncated successfully.")
        return truncated_updates

    def announce_news(self):
        logging.info("Starting the news announcement process.")
        try:
            news_updates = self.fetch_news()
        except Exception as e:
            logging.error(f"Failed to fetch news updates after multiple attempts: {e}")
            return

        logging.info(f"News updates: {news_updates}")

        # Emit the news text ready signal
        self.news_text_ready.emit(news_updates)

        # Use TTS to announce news updates
        self.tts_thread = TextToSpeechThread(news_updates)
        self.tts_thread.audio_ready.connect(self.play_audio)
        self.tts_thread.error_occurred.connect(self.handle_error)
        self.tts_thread.start()
        logging.info("TTS process started.")

    def play_audio(self, audio_path, text):
        try:
            logging.info("Playing audio for the news updates.")
            # Play the audio
            data, samplerate = sf.read(audio_path)
            logging.info(f"Audio data read successfully from {audio_path}.")
            sd.play(data, samplerate)
            sd.wait()
            logging.info("Audio playback finished.")
            self.announcement_complete.emit("Announcement complete.")
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def handle_error(self, error_message):
        logging.error(f"Error in TTS process: {error_message}")
        self.announcement_complete.emit("Error occurred during announcement.")
