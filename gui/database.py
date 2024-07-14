import sqlite3
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_db():
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        conn.close()

def save_note_to_db(title, content):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        # Check if the note with the same title already exists
        c.execute("SELECT id FROM notes WHERE title = ?", (title,))
        result = c.fetchone()
        if result:
            # Update the existing note
            c.execute("UPDATE notes SET content = ? WHERE title = ?", (content, title))
        else:
            # Insert a new note
            c.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        logging.info(f"Note saved successfully with title: {title}")
    except Exception as e:
        logging.error(f"Error saving note: {e}")
    finally:
        conn.close()

def get_all_notes():
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id, title FROM notes ORDER BY id ASC")
        notes = c.fetchall()
        logging.info("Notes retrieved successfully.")
        return notes
    except Exception as e:
        logging.error(f"Error retrieving notes: {e}")
        return []
    finally:
        conn.close()

def load_note_from_db(note_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))
        note = c.fetchone()
        logging.info(f"Note loaded successfully with ID: {note_id}")
        return note
    except Exception as e:
        logging.error(f"Error loading note: {e}")
        return None
    finally:
        conn.close()

def delete_note_from_db(note_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        logging.info(f"Note deleted successfully with ID: {note_id}")
    except Exception as e:
        logging.error(f"Error deleting note: {e}")
    finally:
        conn.close()
