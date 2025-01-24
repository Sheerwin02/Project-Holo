import sys

sys.path.append('../server')

import os
import random
import webbrowser
import hashlib
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon, QLabel, QMessageBox, QVBoxLayout, QInputDialog
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCursor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from utils import get_current_location, get_weather, get_news_updates

from chat_dialog import ChatDialog
from sticky_note_dialog import StickyNoteDialog
from screen_time_tracker import ScreenTimeTracker
from to_do_list import ToDoListDialog
from assistant import create_assistant, create_thread, get_completion, analyze_file

# from GoogleOAuth import GoogleOAuth
from GoogleOAuth import connect_to_google_account, get_user_email, get_upcoming_events
from calendar_widget import CalendarWidget

from focus import FocusTimer

from email_management import EmailManager

from goal_setting import GoalSettingDialog

from httplib2 import Credentials
from googleapiclient.discovery import build

from ocr_feedback import OCRThread

from reminder import ReminderSettingsDialog

# Registering the functions
funcs = [get_current_location, get_weather, get_news_updates]

assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
thread_id = create_thread(debug=True)

pets = []

class ChatThread(QThread):
    response_received = pyqtSignal(str)

    def __init__(self, assistant_id, thread_id, user_input):
        super().__init__()
        self.assistant_id = assistant_id
        self.thread_id = thread_id
        self.user_input = user_input

    def run(self):
        response = get_completion(self.assistant_id, self.thread_id, self.user_input, funcs, debug=True)
        self.response_received.emit(response)


class myAssistant(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.assistant_id = assistant_id
        self.thread_id = thread_id
        self.screen_time_update_timer = QTimer()
        self.google_connected = False
        self.screen_time_displayed = False
        self.ocr_feedback_enabled = False 
        self.user_id = None
        self.ocr_feedback_timer = QTimer()
        # Focus Mode
        self.focus_timer = FocusTimer()
        self.email_manager = EmailManager()  
        self.screen_time_tracker = ScreenTimeTracker()
        self.screen_time_tracker.screen_time_exceeded.connect(self.remind_to_rest)
        self.screen_time_tracker.screen_time_updated.connect(self.update_screen_time_label)

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 200, 200)
        self.repaint()
        self.img = QLabel(self)
        self.chat_bubble = QLabel(self)
        self.chat_bubble.setWordWrap(True)
        self.chat_bubble.setStyleSheet("background-color: black; border: 1px solid black; border-radius: 10px; padding: 5px;")
        self.chat_bubble.hide()

        self.screen_time_label = QLabel(self)
        self.screen_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_time_label.setFixedSize(150, 30)
        self.screen_time_label.setStyleSheet("background-color: black; border: 1px solid black; padding: 5px;")
        self.screen_time_label.hide()  # Initially hide the label

        layout = QVBoxLayout()
        layout.addWidget(self.img)
        layout.addWidget(self.chat_bubble)
        layout.addWidget(self.screen_time_label)
        self.setLayout(layout)
        self.actionDatas = []
        self.initData()
        self.index = 0
        self.setPic("shime1.png")
        self.resize(128, 128)
        self.show()
        self.runing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.actionRun)
        self.timer.start(500)
        self.randomPos()
        
        self.screen_time_tracker = ScreenTimeTracker()
        self.screen_time_tracker.screen_time_exceeded.connect(self.remind_to_rest)
        self.screen_time_tracker.screen_time_updated.connect(self.update_screen_time_label)

        # self.to_do_list_dialog = ToDoListDialog()

        self.calendar_widget = CalendarWidget() 

    def getImgs(self, pics):
        listPic = []
        for item in pics:
            img = QImage()
            img.load('img/'+item)
            listPic.append(img)
        return listPic

    def initData(self):
        imgs = self.getImgs(["shime1b.png", "shime2b.png", "shime1b.png", "shime3b.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime11.png", "shime15.png", "shime16.png", "shime17.png", "shime16.png", "shime17.png", "shime16.png", "shime17.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime54.png", "shime55.png", "shime26.png", "shime27.png", "shime28.png", "shime29.png","shime26.png", "shime27.png", "shime28.png", "shime29.png","shime26.png", "shime27.png", "shime28.png", "shime29.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime31.png", "shime32.png", "shime31.png", "shime33.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime18.png", "shime19.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime34b.png", "shime35b.png", "shime34b.png", "shime36b.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime14.png", "shime14.png", "shime52.png", "shime13.png", "shime13.png", "shime13.png", "shime52.png", "shime14.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime42.png", "shime43.png", "shime44.png", "shime45.png", "shime46.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime1.png", "shime38.png", "shime39.png", "shime40.png", "shime41.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime25.png", "shime25.png", "shime53.png", "shime24.png", "shime24.png", "shime24.png", "shime53.png", "shime25.png"])
        self.actionDatas.append(imgs)
        imgs = self.getImgs(["shime20.png", "shime21.png", "shime20.png", "shime21.png", "shime20.png"])
        self.actionDatas.append(imgs)

    def actionRun(self):
        if not self.runing:
            self.action = random.randint(0, len(self.actionDatas)-1)
            self.index = 0
            self.runing = True
        self.runFunc(self.actionDatas[self.action])

    def setPic(self, pic):
        img = QImage()
        img.load('img/'+pic)
        self.img.setPixmap(QPixmap.fromImage(img))

    def runFunc(self, imgs):
        if self.index >= len(imgs):
            self.index = 0
            self.runing = False
        self.img.setPixmap(QPixmap.fromImage(imgs[self.index]))
        self.index += 1

    def randomPos(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size =  self.geometry()
        self.move(int((screen.width()-size.width())*random.random()), int((screen.height()-size.height())*random.random()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPosition().toPoint() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.m_drag:
            self.move(event.globalPosition().toPoint() - self.m_DragPosition)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.m_drag = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)
        
        chat = contextMenu.addAction("Chat")
        sticky_note = contextMenu.addAction("Sticky Note")
        to_do_list = contextMenu.addAction("To-Do List")
        set_goals = contextMenu.addAction("Set Goals") 
        toggle_reminder = contextMenu.addAction("Toggle Reminder" if not self.screen_time_tracker.reminder_enabled else "Disable Reminder")
        toggle_ocr_feedback = contextMenu.addAction("Disable Feedback" if self.ocr_feedback_enabled else "Enable Feedback")
        display_screen_time = contextMenu.addAction("Hide Screen Time" if self.screen_time_displayed else "Display Screen Time")  
        connect_google = contextMenu.addAction("Disconnect Google Account" if self.google_connected else "Connect Google Account")
        show_calendar = contextMenu.addAction("Show Calendar")
        email_management = contextMenu.addAction("Email Management")
        focus_mode = contextMenu.addAction("Focus Mode")
        about = contextMenu.addAction("About")
        quit = contextMenu.addAction("Quit")

        action = contextMenu.exec(event.globalPos())

        if action == chat:
            self.chatWithAssistant()
        elif action == sticky_note:
            self.open_sticky_note()
        elif action == to_do_list:
            self.open_todo_list() 
        elif action == set_goals:
            self.open_goal_setting() 
        elif action == toggle_reminder:
            self.toggle_screen_time_reminder()
        elif action == toggle_ocr_feedback:
            self.toggle_ocr_feedback()
        elif action == display_screen_time:
            self.toggle_screen_time_display() 
            self.screen_time_update_timer.start(1000) # Update every second
        elif action == connect_google:
            if self.google_connected:
                self.disconnect_google_account()
            else:
                self.connect_to_google_account()
        elif action == show_calendar:
            self.show_calendar_widget()
        elif action == email_management:
            self.show_email_management()
        elif action == focus_mode:
            self.show_focus_timer()
        elif action == about:
            aboutInfo()
        elif action == quit:
            os._exit(0)
    
    def toggle_ocr_feedback(self):
        self.ocr_feedback_enabled = not self.ocr_feedback_enabled
        if self.ocr_feedback_enabled:
            self.start_ocr_feedback()
            QMessageBox.information(self, "OCR Feedback", "OCR Feedback is now enabled. Please wait for a few seconds!")
        else:
            self.stop_ocr_feedback()
            QMessageBox.information(self, "OCR Feedback", "OCR Feedback is now disabled")

    def start_ocr_feedback(self):
        logging.info("Starting OCR feedback thread.")
        self.ocr_feedback_timer.timeout.connect(self.run_ocr_feedback)
        self.ocr_feedback_timer.start(10000)  # Run every 10 seconds

    def stop_ocr_feedback(self):
        self.ocr_feedback_timer.stop()
        logging.info("OCR feedback stopped.")

    def run_ocr_feedback(self):
        self.ocr_thread = OCRThread()
        self.ocr_thread.feedback_received.connect(self.display_chat_bubble)
        self.ocr_thread.start()


    def toggle_screen_time_display(self):
        if self.screen_time_displayed:
            self.screen_time_label.hide()
            self.screen_time_update_timer.stop()
            self.screen_time_update_timer.timeout.disconnect(self.update_screen_time_from_tracker)
        else:
            self.screen_time_update_timer.timeout.connect(self.update_screen_time_from_tracker)
            self.screen_time_update_timer.start(1000) # Update every second
        self.screen_time_displayed = not self.screen_time_displayed

    def open_goal_setting(self):
        user_email = get_user_email()
        if not user_email:
            QMessageBox.warning(self, "Error", "Failed to retrieve user email.")
            return
        user_id = self.generate_user_id(user_email)
        if hasattr(self, 'goal_dialog') and self.goal_dialog.isVisible():
            self.goal_dialog.raise_()
        else:
            self.goal_dialog = GoalSettingDialog(user_id)
            self.goal_dialog.show()
          
    def open_sticky_note(self):
        user_email = get_user_email()
        if not user_email:
            QMessageBox.warning(self, "Error", "Failed to retrieve user email. Please Connect To Your Google Account.")
            return
        user_id = self.generate_user_id(user_email)
        self.sticky_note_dialog = StickyNoteDialog(self.user_id)
        self.sticky_note_dialog.show()
    
    def open_todo_list(self):
        if not self.user_id:
            user_email = get_user_email()
            if not user_email:
                QMessageBox.warning(self, "Error", "Failed to retrieve user email. Please Connect To Your Google Account.")
                return
            self.user_id = self.generate_user_id(user_email)
        self.to_do_list_dialog = ToDoListDialog(self.user_id, self.assistant_id, self.thread_id)
        self.to_do_list_dialog.show()
    
    def chatWithAssistant(self):
        self.chat_dialog = ChatDialog(assistant_id, thread_id)
        self.chat_dialog.response_received.connect(self.display_chat_bubble)
        self.chat_dialog.show()

    def display_chat_bubble(self, text):
        self.chat_bubble.setText(text)
        self.chat_bubble.adjustSize()
        self.chat_bubble.show()
        QTimer.singleShot(55000, self.hide_chat_bubble)  # Hide the chat bubble after 55 seconds

    def hide_chat_bubble(self):
        self.chat_bubble.hide()
        self.chat_bubble.resize(0, 0)  # Reset the size when hidden

### Screen Time Reminder
    ## Screen Time Tracker
    def toggle_screen_time_reminder(self):
        if not self.screen_time_tracker.reminder_enabled:
            dialog = ReminderSettingsDialog(self)
            if dialog.exec():
                interval = dialog.interval_spinbox.value()
                rest_duration = dialog.duration_spinbox.value()
                custom_message = dialog.message_input.text()
                
                self.screen_time_tracker.set_reminder_interval(interval * 60)  # Convert minutes to seconds
                self.screen_time_tracker.set_rest_duration(rest_duration * 60)  # Convert minutes to seconds
                self.screen_time_tracker.set_custom_message(custom_message)
                self.screen_time_tracker.toggle_reminder(True)
                
                QMessageBox.information(self, "Reminder Enabled", 
                    f"Rest reminder set for every {interval} minutes with {rest_duration} minutes rest.")
            else:
                # User cancelled the dialog, don't enable the reminder
                return
        else:
            # Disable the reminder
            self.disable_reminder()

    def disable_reminder(self):
        confirm = QMessageBox.question(self, "Disable Reminder", 
                                       "Are you sure you want to disable the screen time reminder?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.screen_time_tracker.toggle_reminder(False)
            QMessageBox.information(self, "Reminder Disabled", "Screen time reminder has been disabled.")

    def remind_to_rest(self):
        custom_message = self.screen_time_tracker.get_custom_message()
        rest_duration = self.screen_time_tracker.get_rest_duration() // 60  # Convert seconds to minutes
        
        self.display_chat_bubble(custom_message)
        
        reminder_dialog = QMessageBox(self)
        reminder_dialog.setWindowTitle("Rest Reminder")
        reminder_dialog.setText(f"{custom_message}\nIt's time to take a {rest_duration}-minute break.")
        reminder_dialog.setIcon(QMessageBox.Icon.Information)
        
        snooze_button = reminder_dialog.addButton("Snooze (5 min)", QMessageBox.ButtonRole.ActionRole)
        take_break_button = reminder_dialog.addButton("Take Break", QMessageBox.ButtonRole.AcceptRole)
        reminder_dialog.setDefaultButton(take_break_button)
        
        reminder_dialog.exec()
        
        if reminder_dialog.clickedButton() == snooze_button:
            QTimer.singleShot(5 * 60 * 1000, self.remind_to_rest)  # Snooze for 5 minutes
        else:
            self.start_break_timer(rest_duration)

    def start_break_timer(self, duration):
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.end_break)
        self.break_timer.start(duration * 60 * 1000)  # Convert minutes to milliseconds
        
        self.display_chat_bubble(f"Enjoy your {duration}-minute break!")

    def end_break(self):
        self.break_timer.stop()
        self.display_chat_bubble("Break time is over. Back to work!")
        QMessageBox.information(self, "Break Ended", "Your break time is over. Feel refreshed and ready to continue?")

    def update_screen_time_label(self, formatted_time):
        if hasattr(self, 'screen_time_label'):
            self.screen_time_label.setText(f"Screen Time: {formatted_time}")
            self.screen_time_label.adjustSize()
            self.screen_time_label.show()

    def update_screen_time_from_tracker(self):
        formatted_time = self.screen_time_tracker.get_current_screen_time()
        self.update_screen_time_label(formatted_time)
    
    def connect_to_google_account(self):
        message, connected = connect_to_google_account()
        self.google_connected = connected
        if connected:
            user_email = get_user_email()
            self.user_id = self.generate_user_id(user_email)
        QMessageBox.information(self, "Google Account Connection", message)
    
    def disconnect_google_account(self):
        os.remove('token.json')
        self.google_connected = False
        self.user_id = None
        QMessageBox.information(self, "Google Account Connection", "Google account disconnected successfully.")

    def show_upcoming_events(self):
        events = get_upcoming_events()
        QMessageBox.information(self, "Upcoming Events", events)
    
    def show_calendar_widget(self):
        self.calendar_widget.update_events()
        self.calendar_widget.show()
    
    def show_focus_timer(self):  # Method to show the Focus Timer
        self.focus_timer.show()

    def show_email_management(self):
        self.email_manager.show()
    
    def generate_user_id(self, email):
        """Generate a consistent user ID based on the email address using SHA-256."""
        return hashlib.sha256(email.encode()).hexdigest()

def addOnePet():
    pets.append(myAssistant())

def delOnePet():
    if len(pets) == 0:
        return
    del pets[len(pets)-1]


def aboutInfo():
    webbrowser.open_new_tab("https://github.com/Sheerwin02/Project-Holo")
