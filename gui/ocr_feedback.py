import sys
import pyautogui
import logging
from PyQt6.QtCore import QThread, pyqtSignal
import base64
from openai import OpenAI
sys.path.append('../server')
from assistant import analyze_image

class OCRThread(QThread):
    feedback_received = pyqtSignal(str)

    def run(self):
        try:
            # Capture screen
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.png")
            logging.info("Screenshot captured and saved as screenshot.png.")

            # Read the image file and encode to base64
            with open("screenshot.png", "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                logging.info("Image successfully encoded to base64.")

            # Analyze the image
            response = analyze_image(encoded_image)
            logging.info(f"Image analysis response: {response}")

            # Emit feedback received
            self.feedback_received.emit(response)
        except Exception as e:
            error_message = f"Error capturing screen: {e}"
            logging.error(error_message)
            self.feedback_received.emit(error_message)
