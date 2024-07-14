import sys
from PyQt6.QtWidgets import QApplication
from functions import myAssistant

if __name__ == "__main__":
    global pets
    pets = []
    app = QApplication(sys.argv)
    w = myAssistant()
    sys.exit(app.exec())
