from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QHBoxLayout, QTextEdit, QFormLayout, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from GoogleOAuth import fetch_emails, send_email, quick_reply, get_email_details, delete_email
from assistant import get_completion, create_assistant, create_thread
import os
import logging

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class FetchEmailsThread(QThread):
    emails_fetched = pyqtSignal(list)

    def run(self):
        emails = fetch_emails()
        self.emails_fetched.emit(emails)

class LoadingScreen(QDialog):
    def __init__(self, parent=None):
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
        self.label = QLabel("Fetching emails...", self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

class EmailManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.fetch_emails_thread = None
        self.loading_screen = None
        self.assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
        self.thread_id = create_thread(debug=True)
        self.fetch_emails()

    def initUI(self):
        self.setWindowTitle("Email Manager")
        self.setGeometry(300, 300, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #E0FFFF;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 16px;
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
            QPushButton#fetch {
                background-color: #00CCCC;
            }
            QPushButton#send {
                background-color: #009999;
            }
            QPushButton#reply {
                background-color: #FFC107;
            }
            QPushButton#delete {
                background-color: #F44336;
            }
            QPushButton#search {
                background-color: #4CAF50;
            }
            QPushButton#close {
                background-color: #8B0000;
            }
            QPushButton#view_reply {
                background-color: #32CD32;
            }
            QPushButton#ai_suggest {
                background-color: #4169E1;
            }
        """)

        self.layout = QVBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search emails...")
        self.layout.addWidget(self.search_bar)

        self.email_list = QListWidget(self)
        self.email_list.itemClicked.connect(self.view_email)
        self.layout.addWidget(self.email_list)

        button_layout = QHBoxLayout()
        self.fetch_button = QPushButton("Fetch Emails", self)
        self.fetch_button.setObjectName("fetch")
        self.fetch_button.clicked.connect(self.fetch_emails)
        button_layout.addWidget(self.fetch_button)

        self.send_button = QPushButton("Send Email", self)
        self.send_button.setObjectName("send")
        self.send_button.clicked.connect(self.send_email_dialog)
        button_layout.addWidget(self.send_button)

        self.reply_button = QPushButton("Quick Reply", self)
        self.reply_button.setObjectName("reply")
        self.reply_button.clicked.connect(self.quick_reply_dialog)
        button_layout.addWidget(self.reply_button)

        self.delete_button = QPushButton("Delete Email", self)
        self.delete_button.setObjectName("delete")
        self.delete_button.clicked.connect(self.delete_email_dialog)
        button_layout.addWidget(self.delete_button)

        self.search_button = QPushButton("Search", self)
        self.search_button.setObjectName("search")
        self.search_button.clicked.connect(self.search_emails)
        button_layout.addWidget(self.search_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def fetch_emails(self):
        self.loading_screen = LoadingScreen(self)
        self.loading_screen.show()

        self.fetch_emails_thread = FetchEmailsThread()
        self.fetch_emails_thread.emails_fetched.connect(self.display_emails)
        self.fetch_emails_thread.start()

    def display_emails(self, emails):
        self.loading_screen.hide()
        self.email_list.clear()
        if isinstance(emails, list) and emails and "Error" not in emails[0]:
            for email in emails:
                item = f"Subject: {email['subject']}\nSnippet: {email['snippet']}"
                list_item = QListWidgetItem(item)
                list_item.setData(Qt.ItemDataRole.UserRole, email['id'])
                self.email_list.addItem(list_item)
        else:
            self.email_list.addItem(emails[0] if emails else "Failed to fetch emails.")

    def view_email(self, item):
        email_id = item.data(Qt.ItemDataRole.UserRole)
        email_details = get_email_details(email_id)
        if email_details:
            view_dialog = QDialog(self)
            view_dialog.setWindowTitle("View Email")
            view_dialog.setGeometry(150, 150, 600, 400)

            form_layout = QFormLayout(view_dialog)
            subject_label = QLabel(email_details['subject'])
            from_label = QLabel(email_details['from'])
            date_label = QLabel(email_details['date'])
            body_label = QTextEdit(email_details['body'])
            body_label.setReadOnly(True)
            body_label.setStyleSheet("color: #000000;")

            form_layout.addRow("Subject:", subject_label)
            form_layout.addRow("From:", from_label)
            form_layout.addRow("Date:", date_label)
            form_layout.addRow("Body:", body_label)

            button_layout = QHBoxLayout()

            reply_button = QPushButton("Reply", view_dialog)
            reply_button.setObjectName("view_reply")
            reply_button.clicked.connect(lambda: self.reply_email(email_id, email_details['subject'], email_details['from']))
            button_layout.addWidget(reply_button)

            ai_suggest_button = QPushButton("AI Suggest", view_dialog)
            ai_suggest_button.setObjectName("ai_suggest")
            ai_suggest_button.clicked.connect(lambda: self.ai_suggest_reply(email_details['body'], email_id, email_details['subject'], email_details['from'], view_dialog))
            button_layout.addWidget(ai_suggest_button)

            close_button = QPushButton("Close", view_dialog)
            close_button.setObjectName("close")
            close_button.clicked.connect(view_dialog.close)
            button_layout.addWidget(close_button)

            form_layout.addRow(button_layout)

            view_dialog.setLayout(form_layout)
            view_dialog.exec()

    def ai_suggest_reply(self, email_body, email_id, subject, recipient, parent_dialog):
        prompt = f"Provide a brief, professional reply to the following email:\n\n{email_body}"
        suggestion = get_completion(self.assistant_id, self.thread_id, prompt, funcs=[])
        
        suggestion_dialog = QDialog(parent_dialog)
        suggestion_dialog.setWindowTitle("AI Suggestion")
        suggestion_dialog.setGeometry(150, 150, 600, 300)

        suggestion_layout = QVBoxLayout(suggestion_dialog)
        suggestion_label = QTextEdit(suggestion)
        suggestion_label.setStyleSheet("color: #000000;")
        suggestion_layout.addWidget(suggestion_label)

        button_layout = QHBoxLayout()
        
        use_button = QPushButton("Use Suggestion", suggestion_dialog)
        use_button.setStyleSheet("background-color: #32CD32;")
        use_button.clicked.connect(lambda: self.reply_with_suggestion(email_id, subject, recipient, suggestion_label.toPlainText(), suggestion_dialog))
        button_layout.addWidget(use_button)

        cancel_button = QPushButton("Cancel", suggestion_dialog)
        cancel_button.setStyleSheet("background-color: #8B0000; color: #ffffff;")
        cancel_button.clicked.connect(suggestion_dialog.close)
        button_layout.addWidget(cancel_button)

        suggestion_layout.addLayout(button_layout)
        suggestion_dialog.setLayout(suggestion_layout)
        suggestion_dialog.exec()

    def reply_with_suggestion(self, email_id, subject, recipient, reply_text, dialog):
        # Ensure the recipient is correct
        recipient = recipient.split('<')[-1].replace('>', '')
        result = send_email(recipient, f"Re: {subject}", reply_text)
        QMessageBox.information(self, "Reply Email", result)
        dialog.close()

    def reply_email(self, email_id, subject, recipient):
        reply_text, ok = QInputDialog.getText(self, 'Reply Email', f'Reply to {subject}:')
        if ok and reply_text:
            # Ensure the recipient is correct
            recipient = recipient.split('<')[-1].replace('>', '')
            result = send_email(recipient, f"Re: {subject}", reply_text)
            QMessageBox.information(self, "Reply Email", result)

    def send_email_dialog(self):
        send_dialog = QDialog(self)
        send_dialog.setWindowTitle("Send Email")
        send_dialog.setGeometry(150, 150, 600, 400)

        form_layout = QFormLayout(send_dialog)

        recipient_input = QLineEdit(send_dialog)
        subject_input = QLineEdit(send_dialog)
        body_input = QTextEdit(send_dialog)
        attachments = []

        form_layout.addRow("Recipient:", recipient_input)
        form_layout.addRow("Subject:", subject_input)
        form_layout.addRow("Body:", body_input)

        attach_button = QPushButton("Attach File", send_dialog)
        attach_button.clicked.connect(lambda: self.attach_file(attachments))
        form_layout.addRow(attach_button)

        button_layout = QHBoxLayout()

        send_button = QPushButton("Send", send_dialog)
        send_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        send_button.clicked.connect(lambda: self.send_email(recipient_input.text(), subject_input.text(), body_input.toPlainText(), attachments, send_dialog))
        button_layout.addWidget(send_button)

        cancel_button = QPushButton("Cancel", send_dialog)
        cancel_button.setStyleSheet("color: #000000; background-color: #ffffff;")
        cancel_button.clicked.connect(send_dialog.close)
        button_layout.addWidget(cancel_button)

        form_layout.addRow(button_layout)

        send_dialog.setLayout(form_layout)
        send_dialog.exec()

    def attach_file(self, attachments):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Attachment", "", "All Files (*);;Text Files (*.txt);;Images (*.png *.jpg);;PDF Files (*.pdf)", options=options)
        if file_path:
            attachments.append(file_path)

    def send_email(self, recipient, subject, body, attachments, dialog):
        result = send_email(recipient, subject, body, attachments)
        QMessageBox.information(self, "Send Email", result)
        dialog.close()

    def quick_reply_dialog(self):
        selected_items = self.email_list.selectedItems()
        if selected_items:
            email_subject = selected_items[0].text().split('\n')[0].replace("Subject: ", "")
            email_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            reply_text, ok = QInputDialog.getText(self, 'Quick Reply', f'Reply to {email_subject}:')
            if ok and reply_text:
                result = quick_reply(email_id, reply_text)
                QMessageBox.information(self, "Quick Reply", result)
        else:
            QMessageBox.warning(self, "Quick Reply", "Please select an email to reply to.")

    def delete_email_dialog(self):
        selected_items = self.email_list.selectedItems()
        if selected_items:
            email_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            result = delete_email(email_id)
            QMessageBox.information(self, "Delete Email", result)
            self.fetch_emails()  # Refresh the email list
        else:
            QMessageBox.warning(self, "Delete Email", "Please select an email to delete.")

    def search_emails(self):
        search_text = self.search_bar.text().lower()
        if search_text:
            self.email_list.clear()
            emails = fetch_emails()  # Fetch emails again to search within them
            if isinstance(emails, list) and emails and "Error" not in emails[0]:
                for email in emails:
                    if search_text in email['subject'].lower() or search_text in email['snippet'].lower():
                        item = f"Subject: {email['subject']}\nSnippet: {email['snippet']}"
                        list_item = QListWidgetItem(item)
                        list_item.setData(Qt.ItemDataRole.UserRole, email['id'])
                        self.email_list.addItem(list_item)
            else:
                self.email_list.addItem(emails[0] if emails else "Failed to fetch emails.")
        else:
            self.fetch_emails()  # Show all emails if search text is cleared

    def closeEvent(self, event):
        self.hide()
        event.ignore()

