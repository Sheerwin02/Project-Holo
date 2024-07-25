from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QDateTimeEdit,
    QMessageBox, QLabel, QSystemTrayIcon, QMenu, QAbstractItemView, QComboBox, QCheckBox, QTextEdit, QListWidgetItem, QWidget, QInputDialog
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QIcon, QAction, QColor
import database
import logging
from task_widget import TaskWidget
from styles import style_sheet
from assistant import get_completion, create_assistant, create_thread
import json

assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
thread_id = create_thread(debug=True)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ToDoListDialog(QDialog):
    def __init__(self, user_id, assistant_id , thread_id):
        super().__init__()
        self.user_id = user_id  # Store the user_id
        self.assistant_id = assistant_id  # Store the assistant_id
        self.thread_id = thread_id  # Store the thread_id
        self.setWindowTitle("To-Do List")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('icons/todo.png'))
        
        self.layout = QVBoxLayout()

        self.title_label = QLabel("Task Title:", self)
        self.layout.addWidget(self.title_label)
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter task title")
        self.layout.addWidget(self.title_input)

        self.due_date_label = QLabel("Due Date and Time:", self)
        self.layout.addWidget(self.due_date_label)
        self.due_date_input = QDateTimeEdit(self)
        self.due_date_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_date_input.setDateTime(QDateTime.currentDateTime())
        self.due_date_input.setToolTip("Select the due date and time for the task")
        self.layout.addWidget(self.due_date_input)

        self.priority_label = QLabel("Priority:", self)
        self.layout.addWidget(self.priority_label)
        self.priority_input = QComboBox(self)
        self.priority_input.addItems(["High", "Medium", "Low"])
        self.layout.addWidget(self.priority_input)

        self.description_label = QLabel("Description:", self)
        self.layout.addWidget(self.description_label)
        self.description_input = QTextEdit(self)
        self.description_input.setPlaceholderText("Enter task description")
        self.layout.addWidget(self.description_input)

        self.recurring_label = QLabel("Recurring:", self)
        self.layout.addWidget(self.recurring_label)
        self.recurring_input = QComboBox(self)
        self.recurring_input.addItems(["None", "Daily", "Weekly", "Monthly"])
        self.layout.addWidget(self.recurring_input)

        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Task", self)
        self.add_button.setIcon(QIcon('icons/add.png'))
        self.add_button.clicked.connect(self.add_task)
        self.button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Task", self)
        self.edit_button.setIcon(QIcon('icons/edit.png'))
        self.edit_button.clicked.connect(self.edit_task)
        self.button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Task", self)
        self.delete_button.setIcon(QIcon('icons/delete.png'))
        self.delete_button.clicked.connect(self.delete_task)
        self.button_layout.addWidget(self.delete_button)

        self.auto_fill_button = QPushButton("AI Suggest", self)  # Add Auto Fill button
        self.auto_fill_button.setIcon(QIcon('icons/fill.png'))
        self.auto_fill_button.clicked.connect(self.auto_fill_fields)
        self.button_layout.addWidget(self.auto_fill_button)

        self.layout.addLayout(self.button_layout)

        self.show_completed_checkbox = QCheckBox("Show Completed Tasks", self)
        self.show_completed_checkbox.setChecked(False)
        self.show_completed_checkbox.stateChanged.connect(self.load_tasks_list)
        self.layout.addWidget(self.show_completed_checkbox)

        self.tasks_list = QListWidget(self)
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tasks_list.itemClicked.connect(self.display_task)
        self.tasks_list.setToolTip("Click on a task to view or edit it")
        self.tasks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tasks_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.tasks_list)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search tasks")
        self.search_bar.textChanged.connect(self.filter_tasks)
        self.layout.addWidget(self.search_bar)

        self.setLayout(self.layout)

        self.load_tasks_list()

        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Check every minute

        self.apply_styles()

    def load_tasks_list(self):
        try:
            self.tasks_list.clear()
            tasks = database.get_all_tasks(self.user_id, show_completed=self.show_completed_checkbox.isChecked())
            
            for task_id, title, due_date, priority, description, completed in tasks:
                print(f"Loading task: ID={task_id}, Title={title}")
                task_widget = TaskWidget(task_id, title, due_date, priority, description, completed)
                item = QListWidgetItem(self.tasks_list)
                item.setSizeHint(task_widget.sizeHint())
                self.tasks_list.setItemWidget(item, task_widget)
                
                due_datetime = QDateTime.fromString(due_date, "yyyy-MM-dd HH:mm")
                if completed:
                    item.setBackground(QColor("#2ecc71"))  # Green for completed tasks
                elif due_datetime < QDateTime.currentDateTime():
                    item.setBackground(QColor("#e74c3c"))  # Red for overdue tasks
                else:
                    item.setBackground(QColor("#34495e"))  # Default color
            
            self.tasks_list.setSpacing(10)
            logging.info(f"Tasks list loaded successfully. Total tasks: {self.tasks_list.count()}")
            print(f"Total tasks loaded: {self.tasks_list.count()}")  # Debug print
        except Exception as e:
            logging.error(f"Error loading tasks list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load tasks list: {e}")

    def display_task(self, item):
        task_widget = self.tasks_list.itemWidget(item)
        if task_widget:
            task_id = task_widget.task_id
            task = database.load_task_from_db(self.user_id, task_id)
            if task:
                title, due_date_str, priority, description, recurring, completed = task
                self.title_input.setText(title)
                self.due_date_input.setDateTime(QDateTime.fromString(due_date_str, "yyyy-MM-dd HH:mm"))
                self.priority_input.setCurrentText(priority)
                self.description_input.setText(description)
                self.recurring_input.setCurrentText(recurring)
                print(f"Displayed task: ID={task_id}, Title={title}, Due={due_date_str}")  # Debug print
            else:
                print(f"No task found with ID: {task_id}")  # Debug print
        else:
            print("No task widget found for the selected item")  # Debug print

    def save_task_to_db(self, title, due_date, priority, description, recurring):
        existing_tasks = database.get_all_tasks(self.user_id, show_completed=True)
        for task_id, task_title, _, _, _, _ in existing_tasks:  # Unpack the correct number of values
            if task_title == title:
                database.delete_task_from_db(self.user_id, task_id)  # Delete existing task with same title
        database.save_task_to_db(self.user_id, title, due_date, priority, description, recurring)

    def add_task(self):
        title = self.title_input.text()
        due_date = self.due_date_input.dateTime().toString("yyyy-MM-dd HH:mm")
        priority = self.priority_input.currentText()
        description = self.description_input.toPlainText()
        recurring = self.recurring_input.currentText()
        if title:
            self.save_task_to_db(title, due_date, priority, description, recurring)
            QMessageBox.information(self, "Task Added", "Your task has been added successfully.")
            self.load_tasks_list()
            logging.info(f"Task added with title: {title}")
            self.title_input.clear()
            self.due_date_input.setDateTime(QDateTime.currentDateTime())
            self.priority_input.setCurrentIndex(1)  # Set to "Medium"
            self.description_input.clear()
            self.recurring_input.setCurrentIndex(0)  # Set to "None"
        else:
            QMessageBox.warning(self, "Input Error", "Task title cannot be empty.")
            logging.warning("Attempted to add task with empty title.")

    def edit_task(self):
        selected_items = self.tasks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a task to edit.")
            logging.warning("Attempted to edit task with no selection.")
            return

        task_widget = self.tasks_list.itemWidget(selected_items[0])
        task_id = task_widget.task_id
        title = self.title_input.text()
        due_date = self.due_date_input.dateTime().toString("yyyy-MM-dd HH:mm")
        priority = self.priority_input.currentText()
        description = self.description_input.toPlainText()
        recurring = self.recurring_input.currentText()
        if title:
            database.delete_task_from_db(self.user_id, task_id)
            self.save_task_to_db(title, due_date, priority, description, recurring)
            QMessageBox.information(self, "Task Edited", "Your task has been edited successfully.")
            self.load_tasks_list()
            logging.info(f"Task edited with title: {title}")
            self.title_input.clear()
            self.due_date_input.setDateTime(QDateTime.currentDateTime())
            self.priority_input.setCurrentIndex(1)  # Set to "Medium"
            self.description_input.clear()
            self.recurring_input.setCurrentIndex(0)  # Set to "None"
        else:
            QMessageBox.warning(self, "Input Error", "Task title cannot be empty.")
            logging.warning("Attempted to edit task with empty title.")

    def delete_task(self):
        selected_items = self.tasks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a task to delete.")
            logging.warning("Attempted to delete task with no selection.")
            return

        task_widget = self.tasks_list.itemWidget(selected_items[0])
        task_id = task_widget.task_id
        reply = QMessageBox.question(self, "Delete Task", "Are you sure you want to delete this task?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            database.delete_task_from_db(self.user_id, task_id)
            QMessageBox.information(self, "Task Deleted", "Your task has been deleted successfully.")
            self.load_tasks_list()
            self.title_input.clear()
            self.due_date_input.setDateTime(QDateTime.currentDateTime())
            self.priority_input.setCurrentIndex(1)  # Set to "Medium"
            self.description_input.clear()
            self.recurring_input.setCurrentIndex(0)  # Set to "None"
            logging.info(f"Task deleted with ID: {task_id}")

    def filter_tasks(self):
        filter_text = self.search_bar.text().lower()
        for index in range(self.tasks_list.count()):
            item = self.tasks_list.item(index)
            task_widget = self.tasks_list.itemWidget(item)
            item.setHidden(filter_text not in task_widget.title_label.text().lower())

    def check_reminders(self):
        current_time = QDateTime.currentDateTime()
        tasks = database.get_all_tasks(self.user_id, show_completed=True)
        for task_id, title, due_date_str, priority, description, completed in tasks:
            if not due_date_str:
                continue
            due_datetime = QDateTime.fromString(due_date_str, "yyyy-MM-dd HH:mm")
            if current_time >= due_datetime and not completed:
                self.show_notification(title)
                database.mark_task_as_notified(self.user_id, task_id)
                if self.recurring_input.currentText() != "None":
                    self.handle_recurring_task(task_id, due_datetime)

    def handle_recurring_task(self, task_id, due_datetime):
        recurring = self.recurring_input.currentText()
        if recurring == "Daily":
            new_due_date = due_datetime.addDays(1)
        elif recurring == "Weekly":
            new_due_date = due_datetime.addDays(7)
        elif recurring == "Monthly":
            new_due_date = due_datetime.addMonths(1)
        else:
            return
        database.update_task_due_date(self.user_id, task_id, new_due_date.toString("yyyy-MM-dd HH:mm"))

    def show_notification(self, task_title):
        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon("icons/reminder.png"))
        tray_icon.show()
        tray_icon.showMessage("Task Reminder", f"Task '{task_title}' is due now!", QSystemTrayIcon.MessageIcon.Information, 3000)

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        edit_action = QAction("Edit Task", self)
        edit_action.setIcon(QIcon('icons/edit.png'))
        edit_action.triggered.connect(self.edit_task)
        delete_action = QAction("Delete Task", self)
        delete_action.setIcon(QIcon('icons/delete.png'))
        delete_action.triggered.connect(self.delete_task)
        complete_action = QAction("Mark as Completed", self)
        complete_action.setIcon(QIcon('icons/complete.png'))
        complete_action.triggered.connect(self.mark_task_as_completed)
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        context_menu.addAction(complete_action)
        context_menu.exec(self.tasks_list.mapToGlobal(position))

    def mark_task_as_completed(self):
        selected_items = self.tasks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a task to mark as completed.")
            logging.warning("Attempted to mark task as completed with no selection.")
            return

        task_widget = self.tasks_list.itemWidget(selected_items[0])
        task_id = task_widget.task_id
        database.mark_task_as_completed(self.user_id, task_id)
        QMessageBox.information(self, "Task Completed", "Your task has been marked as completed.")
        self.load_tasks_list()
        self.title_input.clear()
        self.due_date_input.setDateTime(QDateTime.currentDateTime())
        self.priority_input.setCurrentIndex(1)  # Set to "Medium"
        self.description_input.clear()
        self.recurring_input.setCurrentIndex(0)  # Set to "None"
        logging.info(f"Task marked as completed with ID: {task_id}")

    def auto_fill_fields(self):
        # Prompt the user to enter a suitable topic
        topic, ok = QInputDialog.getText(self, 'Input Topic', 'Enter a suitable topic for the task:')
        
        if ok and topic:
            prompt = f"""
            Generate suitable values for a task related to "{topic}" for university students. The output should be a JSON object with the following fields (The due date should not be earlier than the current date and time and must be logical) Examples:
            {{
                "title": "Example Title",
                "due_date": "2024-07-25 14:00",
                "priority": "Medium",
                "description": "This is an example task description.",
                "recurring": "None"
            }}
            """
            print("Sending prompt to AI for auto-fill fields...")
            response = get_completion(self.assistant_id, self.thread_id, prompt, funcs=[])

            print(f"AI Response: {response}")

            if response:
                try:
                    # Extract JSON part from the response
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    json_str = response[json_start:json_end]

                    print(f"Extracted JSON String: {json_str}")

                    task_data = json.loads(json_str)
                    print(f"Decoded JSON: {task_data}")

                    self.title_input.setText(task_data.get("title", "Default Title"))
                    self.due_date_input.setDateTime(QDateTime.fromString(task_data.get("due_date", QDateTime.currentDateTime().addDays(1).toString("yyyy-MM-dd HH:mm")), "yyyy-MM-dd HH:mm"))

                    priority_map = {"High": 0, "Medium": 1, "Low": 2}
                    self.priority_input.setCurrentIndex(priority_map.get(task_data.get("priority", "Medium"), 1))

                    self.description_input.setPlainText(task_data.get("description", "Default description for the task."))

                    recurring_map = {"None": 0, "Daily": 1, "Weekly": 2, "Monthly": 3}
                    self.recurring_input.setCurrentIndex(recurring_map.get(task_data.get("recurring", "None"), 0))

                    QMessageBox.information(self, "Auto Fill", "Fields have been auto-filled with AI-generated values.")
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}")
                    QMessageBox.warning(self, "Auto Fill Error", "Failed to decode AI response.")
            else:
                print("Failed to get response from AI.")
                QMessageBox.warning(self, "Auto Fill Error", "Failed to get response from AI.")
        else:
            print("User did not enter a topic.")
            QMessageBox.warning(self, "Input Error", "Please enter a suitable topic.")




    def closeEvent(self, event):
        self.hide()
        event.ignore()
        logging.info("To-do list dialog closed.")

    def apply_styles(self):
        self.setStyleSheet(style_sheet)
