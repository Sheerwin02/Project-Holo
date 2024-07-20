from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QDateEdit, QDateTimeEdit,
    QHBoxLayout, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy, QFormLayout, QDialog, QSpinBox
)
from PyQt6.QtCore import Qt, QDate, QTimer, QDateTime, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from GoogleOAuth import get_upcoming_events, add_event, edit_event, delete_event
from assistant import get_completion, create_assistant, create_thread
from utils import get_current_location, get_weather, get_news_updates
import datetime
from plyer import notification

# Registering the functions
funcs = [get_current_location, get_weather, get_news_updates]

assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
thread_id = create_thread(debug=True)

class NotificationThread(QThread):
    notify = pyqtSignal(str, str)

    def __init__(self, event_time, event_summary, reminder_minutes):
        super().__init__()
        self.event_time = event_time
        self.event_summary = event_summary
        self.reminder_minutes = reminder_minutes

    def run(self):
        time_to_wait = (self.event_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds() - (self.reminder_minutes * 60)
        if time_to_wait > 0:
            QThread.sleep(int(time_to_wait))  # Convert to integer by rounding
        self.notify.emit("Event Reminder", f"Upcoming Event: {self.event_summary}")

class CalendarWidget(QWidget):
    notify_chat = pyqtSignal(str)



    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Miku Calendar")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #E0FFFF;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                color: #000000;
            }
            QLineEdit, QDateEdit, QDateTimeEdit, QSpinBox {
                font-size: 14px;
                color: #000000;
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            QDateEdit::drop-down, QDateTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                padding: 0 8px 0 0;
            }
            QDateEdit::down-arrow, QDateTimeEdit::down-arrow {
                image: url(down_arrow.png);
                width: 10px;
                height: 10px;
            }
            QDateEdit QAbstractItemView, QDateTimeEdit QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #00CCCC;
                selection-color: #000000;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 5px;
                padding: 5px 10px;
                color: #ffffff;
            }
            QPushButton#refresh {
                background-color: #00CCCC;
            }
            QPushButton#add {
                background-color: #009999;
            }
            QPushButton#edit {
                background-color: #FFC107;
            }
            QPushButton#delete {
                background-color: #F44336;
            }
            QPushButton#apply {
                background-color: #4CAF50;
            }
            QPushButton#save, QPushButton#cancel {
                color: #000000;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.notification_threads = []

        # Sidebar
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        self.date_filter = QDateEdit(self)
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setStyleSheet("color: #000000; background-color: #ffffff;")
        self.sidebar_layout.addWidget(self.create_label("Filter by Date:"))
        self.sidebar_layout.addWidget(self.date_filter)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search events...")
        self.sidebar_layout.addWidget(self.create_label("Search Events:"))
        self.sidebar_layout.addWidget(self.search_bar)

        self.apply_filter_button = QPushButton("Apply Filter", self)
        self.apply_filter_button.setObjectName("apply")
        self.apply_filter_button.clicked.connect(self.update_events)
        self.sidebar_layout.addWidget(self.apply_filter_button)

        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.setObjectName("refresh")
        self.refresh_button.clicked.connect(self.update_events)
        self.sidebar_layout.addWidget(self.refresh_button)

        self.add_event_button = QPushButton("Add Event", self)
        self.add_event_button.setObjectName("add")
        self.add_event_button.clicked.connect(self.show_add_event_dialog)
        self.sidebar_layout.addWidget(self.add_event_button)

        self.sidebar_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.sidebar_layout.addItem(self.sidebar_spacer)

        self.main_layout.addLayout(self.sidebar_layout)

        # Event List
        self.event_list_layout = QVBoxLayout()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #00CCCC;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #009999;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.scroll_content)

        self.event_list_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.event_list_layout)

        self.loading_label = QLabel("Loading events...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #000000; font-size: 14px;")
        self.event_list_layout.addWidget(self.loading_label)

        self.update_events()

    def closeEvent(self, event):
        for thread in self.notification_threads:
            thread.terminate()
        self.hide()
        event.ignore()

    def create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #000000;")
        return label

    def update_events(self):
        self.loading_label.show()
        QTimer.singleShot(500, self.fetch_events)

    def fetch_events(self):
        events_list = get_upcoming_events()
        print("Fetched events:", events_list)  # Debugging statement

        filter_date = self.date_filter.date().toString("yyyy-MM-dd")
        search_text = self.search_bar.text().lower()

        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if isinstance(events_list, list) and events_list and "Error" not in events_list[0]:
            for event in events_list:
                print(f"Processing event: {event}")  # Debugging statement
                event_details = event.split(": ")
                event_datetime = datetime.datetime.fromisoformat(event_details[1].replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
                event_date_str = event_datetime.strftime("%Y-%m-%d")
                event_day = event_datetime.strftime("%A")
                now = datetime.datetime.now(datetime.timezone.utc)
                days_left = (event_datetime - now).days
                if len(event_details) > 3:
                    event_end = datetime.datetime.fromisoformat(event_details[3].replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
                else:
                    event_end = event_datetime + datetime.timedelta(hours=1)
                duration = event_end - event_datetime

                if days_left < 0 and now <= event_end:
                    days_left_text = "Happening now"
                elif days_left < 0:
                    days_left_text = f"{-days_left} days ago"
                else:
                    days_left_text = f"{days_left} days"

                if (filter_date in event_date_str and search_text in event.lower()) or (not filter_date and not search_text):
                    event_frame = QFrame(self.scroll_content)
                    event_frame.setFrameShape(QFrame.Shape.StyledPanel)
                    event_frame.setStyleSheet("""
                        QFrame {
                            background-color: #ffffff;
                            border: 1px solid #d0d0d0;
                            border-radius: 5px;
                            padding: 10px;
                            margin-bottom: 10px;
                        }
                        QFrame:hover {
                            background-color: #E0FFFF;
                        }
                    """)

                    event_layout = QVBoxLayout(event_frame)
                    event_layout.setSpacing(5)

                    date_label = QLabel(f"<b>{event_date_str} ({event_day})</b>")
                    date_label.setStyleSheet("color: #000000; font-size: 16px;")
                    event_layout.addWidget(date_label)

                    details_label = QLabel(f"""
                    Days Left: {days_left_text}
                    Duration: {duration}
                    Summary: {event_details[-1]}
                    """)
                    details_label.setWordWrap(True)
                    details_label.setStyleSheet("color: #000000; font-size: 14px;")
                    event_layout.addWidget(details_label)

                    event_frame.setLayout(event_layout)
                    event_frame.mousePressEvent = lambda e, event=event: self.show_event_details(event)

                    self.scroll_layout.addWidget(event_frame)

                    self.create_notification(event_datetime, event_details[-1], 10)  # Default reminder 10 minutes before

        else:
            no_event_label = QLabel("No upcoming events found.", self.scroll_content)
            no_event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_event_label.setStyleSheet("color: #808080; font-size: 14px;")
            self.scroll_layout.addWidget(no_event_label)

        self.scroll_content.setLayout(self.scroll_layout)
        self.loading_label.hide()

    def create_notification(self, event_time, event_summary, reminder_minutes):
        notification_thread = NotificationThread(event_time, event_summary, reminder_minutes)
        notification_thread.notify.connect(self.show_notification)
        notification_thread.start()
        self.notification_threads.append(notification_thread)

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            timeout=10
        )
        self.notify_chat.emit(message)  # Signal to display in chat bubble

    def show_event_details(self, event):
        event_details_dialog = QDialog(self)
        event_details_dialog.setWindowTitle("Event Details")
        event_details_dialog.setGeometry(150, 150, 500, 400)  # Increased size to accommodate suggestion

        details_layout = QVBoxLayout(event_details_dialog)

        # Parse the event string to extract all details
        event_parts = event.split(": ")
        event_id = event_parts[0]
        event_start = datetime.datetime.fromisoformat(event_parts[1].replace("Z", "+00:00"))
        event_title = event_parts[-1]
        event_end = event_start + datetime.timedelta(hours=1)  # Default to 1 hour if end time not provided
        if len(event_parts) > 3:
            event_end = datetime.datetime.fromisoformat(event_parts[3].replace("Z", "+00:00"))
        
        duration = event_end - event_start

        # Create labels for each piece of information
        title_label = QLabel(f"<b>Title:</b> {event_title}")
        start_label = QLabel(f"<b>Start:</b> {event_start.strftime('%Y-%m-%d %H:%M')}")
        end_label = QLabel(f"<b>End:</b> {event_end.strftime('%Y-%m-%d %H:%M')}")
        duration_label = QLabel(f"<b>Duration:</b> {duration}")
        id_label = QLabel(f"<b>Event ID:</b> {event_id}")

        # Add labels to the layout
        details_layout.addWidget(title_label)
        details_layout.addWidget(start_label)
        details_layout.addWidget(end_label)
        details_layout.addWidget(duration_label)
        details_layout.addWidget(id_label)

        # Add some spacing
        details_layout.addSpacing(20)

        # Get AI suggestion
        suggestion_prompt = f"Please provide a brief suggestion or tip for the event: {event_title}"
        suggestion = get_completion(assistant_id, thread_id, suggestion_prompt, funcs, debug=True)

        suggestion_label = QLabel(f"<b>AI Suggestion:</b> {suggestion}")
        suggestion_label.setWordWrap(True)
        details_layout.addWidget(suggestion_label)

        # Add some spacing
        details_layout.addSpacing(20)

        button_layout = QHBoxLayout()

        edit_button = QPushButton("Edit", event_details_dialog)
        edit_button.setObjectName("edit")
        edit_button.clicked.connect(lambda: self.show_edit_event_dialog(event))
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete", event_details_dialog)
        delete_button.setObjectName("delete")
        delete_button.clicked.connect(lambda: self.delete_event(event))
        button_layout.addWidget(delete_button)

        details_layout.addLayout(button_layout)

        event_details_dialog.setLayout(details_layout)
        event_details_dialog.exec()

    def show_add_event_dialog(self):
        add_event_dialog = QDialog(self)
        add_event_dialog.setWindowTitle("Add Event")
        add_event_dialog.setGeometry(150, 150, 400, 300)

        form_layout = QFormLayout(add_event_dialog)

        title_input = QLineEdit(add_event_dialog)
        title_input.setStyleSheet("color: #000000;")
        start_input = QDateTimeEdit(QDateTime.currentDateTime(), add_event_dialog)
        start_input.setCalendarPopup(True)
        start_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        start_input.setStyleSheet("color: #000000;")
        end_input = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600), add_event_dialog)
        end_input.setCalendarPopup(True)
        end_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        end_input.setStyleSheet("color: #000000;")
        description_input = QLineEdit(add_event_dialog)
        description_input.setObjectName("description_input")
        description_input.setStyleSheet("color: #000000;")

        reminder_input = QSpinBox(add_event_dialog)
        reminder_input.setRange(0, 1440)  # 0 minutes to 24 hours
        reminder_input.setValue(10)  # Default 10 minutes before
        reminder_input.setSuffix(" minutes")
        reminder_input.setStyleSheet("color: #000000; background-color: #ffffff;")

        form_layout.addRow("Title:", title_input)
        form_layout.addRow("Start Time:", start_input)
        form_layout.addRow("End Time:", end_input)
        form_layout.addRow("Description:", description_input)
        form_layout.addRow("Reminder:", reminder_input)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Save", add_event_dialog)
        save_button.setObjectName("save")
        save_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        save_button.clicked.connect(lambda: self.add_event(title_input.text(), start_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), end_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), description_input.text(), reminder_input.value()))
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel", add_event_dialog)
        cancel_button.setObjectName("cancel")
        cancel_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        cancel_button.clicked.connect(add_event_dialog.close)
        button_layout.addWidget(cancel_button)

        form_layout.addRow(button_layout)

        add_event_dialog.setLayout(form_layout)
        add_event_dialog.exec()

    def show_edit_event_dialog(self, event):
        edit_event_dialog = QDialog(self)
        edit_event_dialog.setWindowTitle("Edit Event")
        edit_event_dialog.setGeometry(150, 150, 400, 300)

        form_layout = QFormLayout(edit_event_dialog)

        title_input = QLineEdit(event.split(": ")[1], edit_event_dialog)
        title_input.setStyleSheet("color: #000000;")
        start_input = QDateTimeEdit(QDateTime.currentDateTime(), edit_event_dialog)
        start_input.setCalendarPopup(True)
        start_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        start_input.setStyleSheet("color: #000000;")
        end_input = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600), edit_event_dialog)
        end_input.setCalendarPopup(True)
        end_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        end_input.setStyleSheet("color: #000000;")
        description_input = QLineEdit(edit_event_dialog)
        description_input.setObjectName("description_input")
        description_input.setStyleSheet("color: #000000;")

        form_layout.addRow("Title:", title_input)
        form_layout.addRow("Start Time:", start_input)
        form_layout.addRow("End Time:", end_input)
        form_layout.addRow("Description:", description_input)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Save", edit_event_dialog)
        save_button.setObjectName("save")
        save_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        save_button.clicked.connect(lambda: self.edit_event(event.split(": ")[0], title_input.text(), start_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), end_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), description_input.text()))
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel", edit_event_dialog)
        cancel_button.setObjectName("cancel")
        cancel_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        cancel_button.clicked.connect(edit_event_dialog.close)
        button_layout.addWidget(cancel_button)

        form_layout.addRow(button_layout)

        edit_event_dialog.setLayout(form_layout)
        edit_event_dialog.exec()

    def add_event(self, title, start_time, end_time, description, reminder_minutes):
        result = add_event(title, start_time, end_time, description)
        if "Event created" in result:
            self.create_notification(datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(datetime.timezone.utc), title, reminder_minutes)
        QMessageBox.information(self, "Add Event", result)
        self.update_events()

    def edit_event(self, event_id, title, start_time, end_time, description):
        result = edit_event(event_id, title, start_time, end_time, description)
        QMessageBox.information(self, "Edit Event", result)
        self.update_events()

    def delete_event(self, event):
        event_id = event.split(": ")[0]
        result = delete_event(event_id)
        QMessageBox.information(self, "Delete Event", result)
        self.update_events()
