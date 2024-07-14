import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QPushButton
sys.path.append('../server') 
from assistant import get_completion
from utils import get_current_location, get_weather, get_news_updates

funcs = [get_current_location, get_weather, get_news_updates]

class ChatDialog(QDialog):
    def __init__(self, assistant_id, thread_id):
        super().__init__()
        self.assistant_id = assistant_id
        self.thread_id = thread_id

        self.setWindowTitle("Chat with Assistant")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.user_input = QLineEdit(self)
        self.layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)

        self.setLayout(self.layout)

    def send_message(self):
        user_message = self.user_input.text()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            self.user_input.clear()
            assistant_response = get_completion(self.assistant_id, self.thread_id, user_message, funcs, debug=True)
            self.chat_display.append(f"Assistant: {assistant_response}")


