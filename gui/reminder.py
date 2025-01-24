from PyQt6.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QLineEdit
from PyQt6.QtCore import QTimer, Qt

class ReminderSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screen Time Reminder Settings")
        layout = QVBoxLayout()

        # Reminder interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Reminder interval (minutes):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 240)
        self.interval_spinbox.setValue(60)
        interval_layout.addWidget(self.interval_spinbox)
        layout.addLayout(interval_layout)

        # Rest duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Rest duration (minutes):"))
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 60)
        self.duration_spinbox.setValue(5)
        duration_layout.addWidget(self.duration_spinbox)
        layout.addLayout(duration_layout)

        # Custom message
        message_layout = QHBoxLayout()
        message_layout.addWidget(QLabel("Custom reminder message:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Time to take a break!")
        message_layout.addWidget(self.message_input)
        layout.addLayout(message_layout)

        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)