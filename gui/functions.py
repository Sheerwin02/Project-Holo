import sys
sys.path.append('../server')

import os
import random
import webbrowser
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon, QLabel, QMessageBox, QVBoxLayout, QInputDialog
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCursor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from utils import get_current_location, get_weather, get_news_updates

from chat_dialog import ChatDialog
from sticky_note_dialog import StickyNoteDialog
from screen_time_tracker import ScreenTimeTracker
from to_do_list import ToDoListDialog
from assistant import create_assistant, create_thread, get_completion

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
        self.screen_time_update_timer = QTimer()

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

        self.screen_time_label = QLabel(self)  # Add this line
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

        self.to_do_list_dialog = ToDoListDialog()

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
        addPet = contextMenu.addAction("Add")
        removePet = contextMenu.addAction("Delete")
        chat = contextMenu.addAction("Chat")
        sticky_note = contextMenu.addAction("Sticky Note")
        to_do_list = contextMenu.addAction("To-Do List")
        toggle_reminder = contextMenu.addAction("Toggle Reminder")
        display_screen_time = contextMenu.addAction("Display Screen Time")  # New option
        about = contextMenu.addAction("About")
        quit = contextMenu.addAction("Quit")

        action = contextMenu.exec(event.globalPos())
        if action == addPet:
            addOnePet()
        elif action == removePet:
            delOnePet()
        elif action == chat:
            self.chatWithAssistant()
        elif action == sticky_note:
            self.open_sticky_note()
        elif action == to_do_list:
            self.to_do_list_dialog.show()
        elif action == toggle_reminder:
            self.toggle_screen_time_reminder()
        elif action == display_screen_time:  # Handle the new option
            self.screen_time_update_timer.timeout.connect(self.update_screen_time_from_tracker)
            self.screen_time_update_timer.start(1000) # Update every second
        elif action == about:
            aboutInfo()
        elif action == quit:
            os._exit(0)

    def open_sticky_note(self):
        self.sticky_note_dialog = StickyNoteDialog()
        self.sticky_note_dialog.show()
    
    def chatWithAssistant(self):
        user_input, ok = QInputDialog.getText(self, 'Chat with Assistant', 'Enter your message:')
        if ok and user_input:
            self.display_chat_bubble(f"You: {user_input}")
            self.chat_thread = ChatThread(assistant_id, thread_id, user_input)
            self.chat_thread.response_received.connect(self.handle_response)
            self.chat_thread.start()

    def display_chat_bubble(self, text):
        self.chat_bubble.setText(text)
        self.chat_bubble.adjustSize()
        self.chat_bubble.show()
        QTimer.singleShot(25000, self.chat_bubble.hide)  # Hide the chat bubble after 25 seconds

    def handle_response(self, response):
        self.display_chat_bubble(f"Assistant: {response}")
    
    ## Screen Time Tracker
    # def show_screen_time(self, formatted_time):
    #     self.display_chat_bubble(f"Current screen time: {formatted_time}")
    
    def toggle_screen_time_reminder(self):
        if not self.screen_time_tracker.reminder_enabled:
            interval, ok = QInputDialog.getInt(self, 'Set Rest Reminder Interval', 'Enter rest reminder interval in minutes:', value=60, min=1)
            if ok:
                self.screen_time_tracker.set_reminder_interval(interval * 60)  # Convert minutes to seconds
                self.screen_time_tracker.toggle_reminder(True)
                QMessageBox.information(self, "Reminder Enabled", f"Rest reminder set for {interval} minutes.")
        else:
            self.screen_time_tracker.toggle_reminder(False)
            QMessageBox.information(self, "Reminder Disabled", "Rest reminder has been disabled.")

    def remind_to_rest(self):
        self.display_chat_bubble("Time to take a break! Rest for a while.")
        QMessageBox.information(self, "Rest Reminder", "You have been working for an hour. It's time to take a 5-minute break.")
    
    def update_screen_time_label(self, formatted_time):
        self.screen_time_label.setText(f"Screen Time: {formatted_time}")
        self.screen_time_label.adjustSize()
        self.screen_time_label.show()

    def update_screen_time_from_tracker(self):
        formatted_time = self.screen_time_tracker.get_current_screen_time()
        self.update_screen_time_label(formatted_time)



def addOnePet():
    pets.append(myAssistant())

def delOnePet():
    if len(pets) == 0:
        return
    del pets[len(pets)-1]


def aboutInfo():
    webbrowser.open_new_tab("https://github.com/luxingwen/desktop-pet-miku")



# def chatWithAssistant():
#     chat_dialog = ChatDialog(assistant_id, thread_id)
#     chat_dialog.exec()
