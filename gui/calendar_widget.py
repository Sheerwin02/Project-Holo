import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QDateEdit, QDateTimeEdit,
    QHBoxLayout, QLineEdit, QTextEdit, QMessageBox, QSpacerItem, QSizePolicy, QFormLayout, QDialog, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QDate, QTimer, QDateTime, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from GoogleOAuth import get_upcoming_events, add_event, edit_event, delete_event
from assistant import get_completion, create_assistant, create_thread
from utils import get_current_location, get_weather, get_news_updates
import datetime
import pytz
from plyer import notification
import logging
import re

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Registering the functions
funcs = [get_current_location, get_weather, get_news_updates]

assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
thread_id = create_thread(debug=True)

class LoadingScreen(QDialog):
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setGeometry(400, 400, 200, 100)
        self.setStyleSheet("""
            QDialog {
                background-color: #E0FFFF;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 16px;
                color: #000000;
            }
        """)
        self.label = QLabel(message, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

class NotificationThread(QThread):
    notify = pyqtSignal(str, str)

    def __init__(self, event_time, event_summary, reminder_minutes):
        super().__init__()
        self.event_time = event_time
        self.event_summary = event_summary
        self.reminder_minutes = reminder_minutes
        self.logger = logging.getLogger(__name__)

    def run(self):
        time_to_wait = (self.event_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds() - (self.reminder_minutes * 60)
        if time_to_wait > 0:
            self.logger.info(f"Notification thread sleeping for {time_to_wait} seconds.")
            QThread.sleep(int(time_to_wait))  # Convert to integer by rounding
        self.logger.info(f"Triggering notification for event: {self.event_summary}")
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
            QPushButton#ai_schedule {
                background-color: #4169E1;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.notification_threads = {}
        self.logger = logging.getLogger(__name__)

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

        self.ai_schedule_button = QPushButton("AI Schedule Event", self)
        self.ai_schedule_button.setObjectName("ai_schedule")
        self.ai_schedule_button.clicked.connect(self.show_schedule_event_dialog)
        self.sidebar_layout.addWidget(self.ai_schedule_button)

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
        # Ensure proper layout setup
        if not hasattr(self, 'scroll_layout'):
            self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        events_list = get_upcoming_events()
        print(f"Fetched events: {events_list}")  # Debug statement

        # Get filter values
        filter_date = self.date_filter.date().toString("yyyy-MM-dd")
        search_text = self.search_bar.text().lower()

        # Check if date filter is set to today's date (default)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        is_date_filter_default = (filter_date == today)

        print(f"Filter date: {filter_date}, Is default: {is_date_filter_default}, Search text: {search_text}")  # Debug statement

        # Clear existing widgets
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        print(f"Events list type: {type(events_list)}, Length: {len(events_list)}")  # Debug statement

        if isinstance(events_list, list) and events_list and "Error" not in events_list[0]:
            myt = pytz.timezone('Asia/Kuala_Lumpur')  # Malaysia time zone
            now = datetime.datetime.now(myt)
            for event in events_list:
                print(f"Processing event: {event}")  # Debug statement
                try:
                    event_details = event.split(": ")
                    if len(event_details) < 2:
                        print(f"Skipping event due to insufficient details: {event}")  # Debug statement
                        continue

                    event_id = event_details[0]
                    event_datetime = datetime.datetime.fromisoformat(event_details[1].replace("Z", "+00:00")).astimezone(myt)
                    event_date_str = event_datetime.strftime("%Y-%m-%d")
                    event_day = event_datetime.strftime("%A")

                    days_left = (event_datetime - now).days

                    print(f"Event datetime: {event_datetime}, Event date str: {event_date_str}, Event day: {event_day}, Now: {now}, Days left: {days_left}")  # Debug statement

                    if len(event_details) > 3:
                        event_end = datetime.datetime.fromisoformat(event_details[3].replace("Z", "+00:00")).astimezone(myt)
                    else:
                        event_end = event_datetime + datetime.timedelta(hours=1)
                    duration = event_end - event_datetime

                    print(f"Event end: {event_end}, Duration: {duration}")  # Debug statement

                    if days_left < 0 and now <= event_end:
                        days_left_text = "Happening now"
                    elif days_left < 0:
                        days_left_text = f"{-days_left} days ago"
                    else:
                        days_left_text = f"{days_left} days"

                    # Only include events happening today or in the future
                    if event_datetime >= now:
                        if (is_date_filter_default or filter_date in event_date_str) and (not search_text or search_text in event.lower()):
                            print("Creating event frame...")  # Debug statement
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
                                Time: {event_details[1]} - {event_details[-1]}
                                Days Left: {days_left_text}
                                Duration: {duration}
                            """)
                            details_label.setWordWrap(True)
                            details_label.setStyleSheet("color: #000000; font-size: 14px;")
                            event_layout.addWidget(details_label)

                            event_frame.setLayout(event_layout)
                            event_frame.mousePressEvent = lambda e, event=event: self.show_event_details(event)

                            print("Adding event frame to scroll layout...")  # Debug statement
                            self.scroll_layout.addWidget(event_frame)

                            self.create_notification(event_id, event_datetime, event_details[-1], 10)  # Default reminder 10 minutes before
                        else:
                            print(f"Event not displayed due to filter conditions: {event}")  # Debug statement
                    else:
                        print(f"Skipping past event: {event}")  # Debug statement
                except Exception as e:
                    print(f"Error processing event: {event}, Error: {e}")  # Debug statement

        else:
            print("No events found or error in fetching events.")  # Debug statement
            no_event_label = QLabel("No upcoming events found.", self.scroll_content)
            no_event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_event_label.setStyleSheet("color: #808080; font-size: 14px;")
            self.scroll_layout.addWidget(no_event_label)

        print("Setting layout for scroll content...")  # Debug statement
        self.scroll_content.update()
        self.scroll_area.update()
        self.loading_label.hide()

        print("fetch_events method completed")  # Debug statement

    def create_notification(self, event_id, event_time, event_summary, reminder_minutes):
        if event_id not in self.notification_threads:
            self.logger.info(f"Creating notification for event: {event_summary} at {event_time} with a reminder {reminder_minutes} minutes before.")
            notification_thread = NotificationThread(event_time, event_summary, reminder_minutes)
            notification_thread.notify.connect(self.show_notification)
            notification_thread.start()
            self.notification_threads[event_summary] = notification_thread

    def show_notification(self, title, message):
        self.logger.info(f"Showing notification: {title}, {message}")
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
        if len(event_parts) < 4:
            print(f"Skipping event due to insufficient details: {event}")  # Debugging statement
            return

        event_id = event_parts[0]
        event_start = event_parts[1]
        event_description = event_parts[2]
        event_end = event_parts[3]

        # Create labels for each piece of information
        title_label = QLabel(f"<b>Title:</b> {event_description.splitlines()[0]}")
        start_label = QLabel(f"<b>Start:</b> {event_start}")
        end_label = QLabel(f"<b>End:</b> {event_end}")
        duration = datetime.datetime.fromisoformat(event_end.replace("Z", "+00:00")) - datetime.datetime.fromisoformat(event_start.replace("Z", "+00:00"))
        duration_label = QLabel(f"<b>Duration:</b> {duration}")
        id_label = QLabel(f"<b>Event ID:</b> {event_id}")
        description_label = QLabel(f"<b>Description:</b> {event_description}")

        # Add labels to the layout
        details_layout.addWidget(title_label)
        details_layout.addWidget(start_label)
        details_layout.addWidget(end_label)
        details_layout.addWidget(duration_label)
        details_layout.addWidget(id_label)
        details_layout.addWidget(description_label)

        # Add some spacing
        details_layout.addSpacing(20)

        # Get AI suggestion
        suggestion_prompt = f"Please provide a brief suggestion or tip for the event: {event_description.splitlines()[0]}"
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
            self.create_notification(datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(pytz.timezone('Asia/Kuala_Lumpur')), title, reminder_minutes)
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

    def show_schedule_event_dialog(self):
        ai_schedule_dialog = QDialog(self)
        ai_schedule_dialog.setWindowTitle("AI Schedule Event")
        ai_schedule_dialog.setGeometry(150, 150, 400, 350)

        form_layout = QFormLayout(ai_schedule_dialog)

        title_input = QLineEdit(ai_schedule_dialog)
        title_input.setStyleSheet("color: #000000;")
        
        duration_input = QSpinBox(ai_schedule_dialog)
        duration_input.setRange(1, 1440 * 30)  # Duration from 1 minute to 30 days
        duration_input.setValue(60)  # Default 60 minutes
        duration_input.setSingleStep(30)  # Step by 30 minutes
        duration_input.setSuffix(" minutes")
        duration_input.setStyleSheet("color: #000000; background-color: #ffffff;")

        date_range_start = QDateTimeEdit(QDateTime.currentDateTime(), ai_schedule_dialog)
        date_range_start.setCalendarPopup(True)
        date_range_start.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_range_start.setStyleSheet("color: #000000;")

        date_range_end = QDateTimeEdit(QDateTime.currentDateTime().addDays(7), ai_schedule_dialog)
        date_range_end.setCalendarPopup(True)
        date_range_end.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_range_end.setStyleSheet("color: #000000;")

        time_preference_input = QComboBox(ai_schedule_dialog)
        time_preference_input.addItems(["Morning", "Afternoon", "Evening", "No Preference"])
        time_preference_input.setStyleSheet("color: #000000; background-color: #ffffff;")

        description_input = QLineEdit(ai_schedule_dialog)
        description_input.setStyleSheet("color: #000000;")

        form_layout.addRow("Title:", title_input)
        form_layout.addRow("Duration:", duration_input)
        form_layout.addRow("Start Date:", date_range_start)
        form_layout.addRow("End Date:", date_range_end)
        form_layout.addRow("Time Preference:", time_preference_input)
        form_layout.addRow("Description:", description_input)

        button_layout = QHBoxLayout()

        schedule_button = QPushButton("Find Slot", ai_schedule_dialog)
        schedule_button.setObjectName("find_slot")
        schedule_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        schedule_button.clicked.connect(lambda: self.find_slot(title_input.text(), duration_input.value(), date_range_start.dateTime(), date_range_end.dateTime(), time_preference_input.currentText(), description_input.text(), ai_schedule_dialog))
        button_layout.addWidget(schedule_button)

        cancel_button = QPushButton("Cancel", ai_schedule_dialog)
        cancel_button.setObjectName("cancel")
        cancel_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        cancel_button.clicked.connect(ai_schedule_dialog.close)
        button_layout.addWidget(cancel_button)

        form_layout.addRow(button_layout)

        ai_schedule_dialog.setLayout(form_layout)
        ai_schedule_dialog.exec()

    def find_slot(self, title, duration, date_range_start, date_range_end, time_preference, description, dialog):
        loading_screen = LoadingScreen(self, "Finding available slot...")
        loading_screen.show()

        events_list = get_upcoming_events()
        events_details = "Upcoming Events:\n"
        for event in events_list:
            events_details += f"{event}\n"

        prompt = f"""
        Find an available slot of {duration} minutes for an event titled '{title}' between {date_range_start.toString('yyyy-MM-dd HH:mm')} and {date_range_end.toString('yyyy-MM-dd HH:mm')}.
        Current schedule: {events_details}. 
        Time preference: {time_preference}.
        Description: {description}.
        The output should be a JSON object with the following fields:
        {{
            "start": "yyyy-MM-ddTHH:mm:ssZ",
            "end": "yyyy-MM-ddTHH:mm:ssZ"
        }}
        """
        available_slot = get_completion(assistant_id, thread_id, prompt, funcs, debug=True)

        loading_screen.hide()

        logging.info(f"AI response: {available_slot}")

        try:
            json_start = available_slot.find('{')
            json_end = available_slot.rfind('}') + 1
            json_str = available_slot[json_start:json_end]

            slot_data = json.loads(json_str)
            start_time = slot_data["start"]
            end_time = slot_data["end"]
            
            slot_dialog = QDialog(dialog)
            slot_dialog.setWindowTitle("AI Suggested Slot")
            slot_dialog.setGeometry(150, 150, 400, 200)

            slot_layout = QVBoxLayout(slot_dialog)
            slot_label = QTextEdit(f"Start: {start_time}\nEnd: {end_time}")
            slot_label.setReadOnly(True)
            slot_label.setStyleSheet("color: #000000;")
            slot_layout.addWidget(slot_label)

            button_layout = QHBoxLayout()

            use_button = QPushButton("Use Slot", slot_dialog)
            use_button.setObjectName("use_slot")
            use_button.setStyleSheet("background-color: #32CD32;")
            use_button.clicked.connect(lambda: self.handle_slot_selection(title, duration, start_time, end_time, description, slot_dialog))
            button_layout.addWidget(use_button)

            cancel_button = QPushButton("Cancel", slot_dialog)
            cancel_button.setObjectName("cancel")
            cancel_button.setStyleSheet("background-color: #8B0000; color: #ffffff;")
            cancel_button.clicked.connect(slot_dialog.close)
            button_layout.addWidget(cancel_button)

            slot_layout.addLayout(button_layout)
            slot_dialog.setLayout(slot_layout)
            slot_dialog.exec()
            
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Error", f"Failed to decode AI response: {e}")


    def handle_slot_selection(self, title, duration, start_time, end_time, description, dialog):
        try:
            myt = pytz.timezone('Asia/Kuala_Lumpur')

            start_time_dt = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(myt)
            end_time_dt = datetime.datetime.fromisoformat(end_time.replace("Z", "+00:00")).astimezone(myt)

            # Adjust end time based on the duration
            end_time_dt = start_time_dt + datetime.timedelta(minutes=duration)

            start_time_str = start_time_dt.isoformat()
            end_time_str = end_time_dt.isoformat()

            result = add_event(title, start_time_str, end_time_str, description)

            QMessageBox.information(self, "Add Event", result)
            self.update_events()
            dialog.close()
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Error parsing slot time: {e}")
            dialog.close()

    def closeEvent(self, event):
        for thread in self.notification_threads.values():
            thread.terminate()
        self.hide()
        event.ignore()

