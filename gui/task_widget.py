from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import Qt
import database

class TaskWidget(QWidget):
    def __init__(self, task_id, title, due_date, priority, description, completed):
        super().__init__()
        self.task_id = task_id
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)  # Adjust margins to zero
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Align vertically to the center

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(completed)
        self.checkbox.stateChanged.connect(self.mark_as_completed)

        self.title_label = QLabel(title)
        self.due_date_label = QLabel(f"Due: {due_date}")
        self.priority_label = QLabel(f"Priority: {priority}")

        label_style = "color: #ffffff; background-color: transparent;"
        for label in (self.title_label, self.due_date_label, self.priority_label):
            label.setStyleSheet(label_style)

        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.due_date_label)
        self.layout.addWidget(self.priority_label)

        self.setStyleSheet("background-color: transparent;")
        self.setFixedHeight(20)  # Set a fixed height for consistent sizing

    def mark_as_completed(self, state):
        database.mark_task_as_completed(self.task_id, state == Qt.CheckState.Checked)
        self.checkbox.setDisabled(state == Qt.CheckState.Checked)
