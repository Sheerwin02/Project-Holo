from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt, QTimer
import database

class StickyNoteDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sticky Note")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter note title")
        self.layout.addWidget(self.title_input)

        self.note_display = QTextEdit(self)
        self.layout.addWidget(self.note_display)

        self.save_button = QPushButton("Save Note", self)
        self.save_button.clicked.connect(self.save_note)
        self.layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Note", self)
        self.load_button.clicked.connect(self.load_note)
        self.layout.addWidget(self.load_button)

        self.delete_button = QPushButton("Delete Note", self)
        self.delete_button.clicked.connect(self.delete_note)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

        self.load_notes_list()

        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_note)
        self.auto_save_timer.start(10000)  # Auto-save every 10 seconds

    def load_notes_list(self):
        self.notes_list = database.get_all_notes()

    def save_note(self):
        title = self.title_input.text()
        content = self.note_display.toPlainText()
        if not title:
            QMessageBox.warning(self, "No Title", "Please enter a title for the note.")
            return
        note_id = self.get_note_id_by_title(title)
        if note_id is None:
            database.save_note_to_db(title, content)
            QMessageBox.information(self, "Note Saved", "Your note has been saved successfully.")
        else:
            database.update_note_in_db(note_id, title, content)
            QMessageBox.information(self, "Note Updated", "Your note has been updated successfully.")
        self.load_notes_list()

    def load_note(self):
        titles = [note[1] for note in self.notes_list]
        if not titles:
            QMessageBox.warning(self, "No Notes Found", "No saved notes found.")
            return
        title, ok = QInputDialog.getItem(self, "Select Note", "Select a note to load:", titles, 0, False)
        if ok and title:
            note_id = self.get_note_id_by_title(title)
            if note_id is not None:
                note = database.load_note_from_db(note_id)
                self.title_input.setText(note[0])
                self.note_display.setPlainText(note[1])
                QMessageBox.information(self, "Note Loaded", "Your note has been loaded successfully.")
            else:
                QMessageBox.warning(self, "Load Error", "Could not load the selected note.")

    def delete_note(self):
        titles = [note[1] for note in self.notes_list]
        if not titles:
            QMessageBox.warning(self, "No Notes Found", "No saved notes found.")
            return
        title, ok = QInputDialog.getItem(self, "Select Note", "Select a note to delete:", titles, 0, False)
        if ok and title:
            note_id = self.get_note_id_by_title(title)
            if note_id is not None:
                database.delete_note_from_db(note_id)
                self.title_input.clear()
                self.note_display.clear()
                self.load_notes_list()
                QMessageBox.information(self, "Note Deleted", "Your note has been deleted successfully.")
            else:
                QMessageBox.warning(self, "Delete Error", "Could not delete the selected note.")

    def get_note_id_by_title(self, title):
        for note in self.notes_list:
            if note[1] == title:
                return note[0]
        return None

    def auto_save_note(self):
        title = self.title_input.text()
        content = self.note_display.toPlainText()
        if title:
            note_id = self.get_note_id_by_title(title)
            if note_id is None:
                database.save_note_to_db(title, content)
            else:
                database.update_note_in_db(note_id, title, content)

    def closeEvent(self, event):
        self.hide()
        event.ignore()
