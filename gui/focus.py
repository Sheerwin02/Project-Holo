import sys
import os
import subprocess
import ctypes
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class FocusTimer(QDialog):
    focus_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.is_focus = True
        self.focus_time = 25 * 60  # 25 minutes
        self.break_time = 5 * 60   # 5 minutes
        self.remaining_time = self.focus_time
        self.blocked_websites = []

        # Check for admin privileges on Windows
        if sys.platform == "win32" and not self.is_admin():
            self.request_admin_permissions()
        
        # Load blocked websites from storage
        self.load_blocked_websites()

    def initUI(self):
        self.setWindowTitle("Focus Mode")
        self.setGeometry(300, 300, 400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #E0FFFF;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 20px;
                color: #000000;
            }
            QLineEdit {
                font-size: 14px;
                color: #000000;
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget {
                font-size: 14px;
                color: #000000;
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 5px;
                padding: 5px 10px;
                color: #ffffff;
            }
            QPushButton#start {
                background-color: #00CCCC;
            }
            QPushButton#pause {
                background-color: #009999;
            }
            QPushButton#reset {
                background-color: #F44336;
            }
            QPushButton#block {
                background-color: #00CCCC;
            }
            QPushButton#unblock {
                background-color: #F44336;
            }
        """)

        self.layout = QVBoxLayout()

        self.timer_label = QLabel("25:00", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.timer_label)

        self.session_label = QLabel("Focus", self)
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.session_label)

        self.start_button = QPushButton("Start", self)
        self.start_button.setObjectName("start")
        self.start_button.clicked.connect(self.start_timer)
        self.layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setObjectName("pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("reset")
        self.reset_button.clicked.connect(self.reset_timer)
        self.layout.addWidget(self.reset_button)

        # Distraction Blocker
        self.blocked_websites_list = QListWidget(self)
        self.layout.addWidget(self.blocked_websites_list)

        self.block_input = QLineEdit(self)
        self.block_input.setPlaceholderText("Enter website to block")
        self.layout.addWidget(self.block_input)

        button_layout = QHBoxLayout()
        self.block_button = QPushButton("Block", self)
        self.block_button.setObjectName("block")
        self.block_button.clicked.connect(self.block_website)
        button_layout.addWidget(self.block_button)

        self.unblock_button = QPushButton("Unblock Selected", self)
        self.unblock_button.setObjectName("unblock")
        self.unblock_button.clicked.connect(self.unblock_website)
        button_layout.addWidget(self.unblock_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def request_admin_permissions(self):
        try:
            if not self.is_admin():
                # Restart the program with admin rights
                script = os.path.abspath(sys.argv[0])
                params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
                sys.exit()
        except Exception as e:
            print(f"Error requesting admin permissions: {e}")

    def start_timer(self):
        self.timer.start(1000)
        self.focus_message.emit("Focus session started. Let's get to work!")

    def pause_timer(self):
        self.timer.stop()
        self.focus_message.emit("Focus session paused. Take a short break.")

    def reset_timer(self):
        self.timer.stop()
        self.remaining_time = self.focus_time if self.is_focus else self.break_time
        self.update_timer_label()
        self.focus_message.emit("Timer reset. Ready to start again?")

    def update_timer(self):
        self.remaining_time -= 1
        self.update_timer_label()

        if self.remaining_time <= 0:
            self.timer.stop()
            if self.is_focus:
                QMessageBox.information(self, "Focus Timer", "Focus session complete. Time for a break!")
                self.focus_message.emit("Focus session complete. Time for a break!")
                self.remaining_time = self.break_time
                self.session_label.setText("Break")
            else:
                QMessageBox.information(self, "Focus Timer", "Break session complete. Time to focus!")
                self.focus_message.emit("Break session complete. Time to focus!")
                self.remaining_time = self.focus_time
                self.session_label.setText("Focus")

            self.is_focus = not self.is_focus
            self.update_timer_label()

    def update_timer_label(self):
        minutes, seconds = divmod(self.remaining_time, 60)
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def block_website(self):
        website = self.block_input.text()
        if website and website not in self.blocked_websites:
            self.blocked_websites.append(website)
            self.blocked_websites_list.addItem(website)
            self.block_input.clear()
            self.apply_blocked_websites()

    def unblock_website(self):
        selected_items = self.blocked_websites_list.selectedItems()
        for item in selected_items:
            website = item.text()
            self.run_privileged_script("unblock", website)
            self.blocked_websites.remove(website)
            self.blocked_websites_list.takeItem(self.blocked_websites_list.row(item))
        self.apply_blocked_websites()

    def load_blocked_websites(self):
        blocked_websites = self.run_privileged_script("load")
        self.blocked_websites = blocked_websites.split("\n") if blocked_websites else []
        for website in self.blocked_websites:
            self.blocked_websites_list.addItem(website)

    def apply_blocked_websites(self):
        for website in self.blocked_websites:
            self.run_privileged_script("block", website)

    def run_privileged_script(self, action, website=""):
        command = [sys.executable, "focus_helper.py", action]
        if website:
            command.append(website)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing script: {result.stderr}")
        return result.stdout

    def closeEvent(self, event):
        self.run_privileged_script("unblock_all")
        self.pause_timer()
        event.ignore()
        self.hide()
