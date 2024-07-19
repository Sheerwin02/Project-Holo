from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QDateEdit, QDateTimeEdit,
    QHBoxLayout, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt, QDate, QTimer, QDateTime
from PyQt6.QtGui import QFont
from GoogleOAuth import get_upcoming_events, add_event, edit_event, delete_event

class CalendarWidget(QWidget):
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
            QLineEdit, QDateEdit, QDateTimeEdit, QLineEdit#description_input {
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
                background-color: #ffffff;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        
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
                event_date = event_details[1][:10]  # Extract date from event
                event_summary = event_details[-1]
                
                if (filter_date in event_date and search_text in event.lower()) or (not filter_date and not search_text):
                    event_frame = QFrame(self.scroll_content)
                    event_frame.setFrameShape(QFrame.Shape.StyledPanel)
                    event_frame.setStyleSheet("""
                        QFrame {
                            background-color: #ffffff;
                            border: 1px solid #d0d0d0;
                            border-radius: 5px;
                            padding: 10px;
                        }
                        QFrame:hover {
                            background-color: #E0FFFF;
                        }
                    """)
                    event_frame.mousePressEvent = lambda e, event=event: self.show_event_details(event)
                    
                    event_label = QLabel(f"{event_date}: {event_summary}", event_frame)
                    event_label.setWordWrap(True)
                    event_label.setStyleSheet("color: #000000; font-size: 14px;")
                    
                    event_layout = QVBoxLayout(event_frame)
                    event_layout.addWidget(event_label)
                    event_frame.setLayout(event_layout)
                    
                    self.scroll_layout.addWidget(event_frame)
        else:
            no_event_label = QLabel("No upcoming events found.", self.scroll_content)
            no_event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_event_label.setStyleSheet("color: #808080; font-size: 14px;")
            self.scroll_layout.addWidget(no_event_label)
        
        self.scroll_content.setLayout(self.scroll_layout)
        self.loading_label.hide()
    
    def show_event_details(self, event):
        event_details_dialog = QDialog(self)
        event_details_dialog.setWindowTitle("Event Details")
        event_details_dialog.setGeometry(150, 150, 400, 300)
        
        details_layout = QVBoxLayout(event_details_dialog)
        
        event_label = QLabel(event, event_details_dialog)
        event_label.setWordWrap(True)
        event_label.setStyleSheet("color: #000000; font-size: 14px;")
        details_layout.addWidget(event_label)
        
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
        
        form_layout.addRow("Title:", title_input)
        form_layout.addRow("Start Time:", start_input)
        form_layout.addRow("End Time:", end_input)
        form_layout.addRow("Description:", description_input)
        
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save", add_event_dialog)
        save_button.setObjectName("save")
        save_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        save_button.clicked.connect(lambda: self.add_event(title_input.text(), start_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), end_input.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ"), description_input.text()))
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
    
    def add_event(self, title, start_time, end_time, description):
        result = add_event(title, start_time, end_time, description)
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
