from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QMessageBox
from PyQt6.QtCore import Qt
import database
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class StickyNoteDialog(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Sticky Notes")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter note title")
        self.layout.addWidget(self.title_input)

        self.note_display = QTextEdit(self)
        self.layout.addWidget(self.note_display)

        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Note", self)
        self.save_button.clicked.connect(self.save_note)
        self.button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton("Delete Note", self)
        self.delete_button.clicked.connect(self.delete_note)
        self.button_layout.addWidget(self.delete_button)

        self.load_button = QPushButton("Load Note", self)
        self.load_button.clicked.connect(self.load_note)
        self.button_layout.addWidget(self.load_button)

        self.layout.addLayout(self.button_layout)

        self.notes_list = QListWidget(self)
        self.notes_list.itemClicked.connect(self.display_note)
        self.layout.addWidget(self.notes_list)

        self.setLayout(self.layout)

        self.load_notes_list()

        # Removed the auto-save timer

    def load_notes_list(self):
        try:
            self.notes_list.clear()
            notes = database.get_all_notes(self.user_id)
            for note_id, title in notes:
                self.notes_list.addItem(f"{note_id}: {title}")
            logging.info("Notes list loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading notes list: {e}")


    def display_note(self, item):
        note_id = int(item.text().split(":")[0])
        note = database.load_note_from_db(self.user_id, note_id)
        if note:
            title, content = note
            self.title_input.setText(title)
            self.note_display.setPlainText(content)
            logging.info(f"Displayed note with ID: {note_id}")

    def save_note_to_db(self, title, content):
        existing_notes = database.get_all_notes(self.user_id)
        for note_id, note_title in existing_notes:
            if note_title == title:
                database.delete_note_from_db(self.user_id, note_id)  # Delete existing note with same title
        database.save_note_to_db(self.user_id, title, content)

    def save_note(self):
        title = self.title_input.text()
        content = self.note_display.toPlainText()
        if title and content:
            self.save_note_to_db(title, content)
            QMessageBox.information(self, "Note Saved", "Your note has been saved successfully.")
            self.load_notes_list()
            logging.info(f"Note saved with title: {title}")
        else:
            QMessageBox.warning(self, "Input Error", "Title and note content cannot be empty.")
            logging.warning("Attempted to save note with empty title or content.")

    def delete_note(self):
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a note to delete.")
            logging.warning("Attempted to delete note with no selection.")
            return

        note_id = int(selected_items[0].text().split(":")[0])
        database.delete_note_from_db(self.user_id, note_id)
        QMessageBox.information(self, "Note Deleted", "Your note has been deleted successfully.")
        self.load_notes_list()
        self.title_input.clear()
        self.note_display.clear()
        logging.info(f"Note deleted with ID: {note_id}")

    def load_note(self):
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a note to load.")
            logging.warning("Attempted to load note with no selection.")
            return

        note_id = int(selected_items[0].text().split(":")[0])
        note = database.load_note_from_db(self.user_id, note_id)
        if note:
            title, content = note
            self.title_input.setText(title)
            self.note_display.setPlainText(content)
            logging.info(f"Note loaded with ID: {note_id}")


    def closeEvent(self, event):
        self.hide()
        event.ignore()
        logging.info("Sticky note dialog closed.")
