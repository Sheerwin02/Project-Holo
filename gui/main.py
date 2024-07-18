import sys
import database
from PyQt6.QtWidgets import QApplication
from functions import myAssistant

# Initialize the database
database.initialize_db()

if __name__ == "__main__":
    # global pets
    # pets = []
    app = QApplication(sys.argv)
    w = myAssistant()
    sys.exit(app.exec())
