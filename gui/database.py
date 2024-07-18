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
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, due_date TEXT, priority TEXT, description TEXT, recurring TEXT, completed INTEGER DEFAULT 0, notified INTEGER DEFAULT 0)''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        conn.close()

# Note functions
def save_note_to_db(title, content):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id FROM notes WHERE title = ?", (title,))
        result = c.fetchone()
        if result:
            c.execute("UPDATE notes SET content = ? WHERE title = ?", (content, title))
        else:
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

# Task functions
def save_task_to_db(title, due_date, priority, description, recurring):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id FROM tasks WHERE title = ?", (title,))
        result = c.fetchone()
        if result:
            c.execute("""
                UPDATE tasks 
                SET due_date = ?, priority = ?, description = ?, recurring = ?, notified = 0 
                WHERE title = ?
            """, (due_date, priority, description, recurring, title))
        else:
            c.execute("""
                INSERT INTO tasks (title, due_date, priority, description, recurring) 
                VALUES (?, ?, ?, ?, ?)
            """, (title, due_date, priority, description, recurring))
        conn.commit()
        logging.info(f"Task saved successfully with title: {title}")
    except Exception as e:
        logging.error(f"Error saving task: {e}")
    finally:
        conn.close()

def get_all_tasks(show_completed=False):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        if show_completed:
            c.execute("SELECT id, title, due_date, priority, description, completed FROM tasks ORDER BY due_date ASC, id ASC")
        else:
            c.execute("SELECT id, title, due_date, priority, description, completed FROM tasks WHERE completed = 0 ORDER BY due_date ASC, id ASC")
        tasks = c.fetchall()
        logging.info("Tasks retrieved successfully.")
        return tasks
    except Exception as e:
        logging.error(f"Error retrieving tasks: {e}")
        return []
    finally:
        conn.close()

def load_task_from_db(task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT title, due_date, priority, description, recurring, completed FROM tasks WHERE id = ?", (task_id,))
        task = c.fetchone()
        logging.info(f"Task loaded successfully with ID: {task_id}")
        return task
    except Exception as e:
        logging.error(f"Error loading task: {e}")
        return None
    finally:
        conn.close()

def delete_task_from_db(task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        logging.info(f"Task deleted successfully with ID: {task_id}")
    except Exception as e:
        logging.error(f"Error deleting task: {e}")
    finally:
        conn.close()

def mark_task_as_notified(task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET notified = 1 WHERE id = ?", (task_id,))
        conn.commit()
        logging.info(f"Task marked as notified with ID: {task_id}")
    except Exception as e:
        logging.error(f"Error marking task as notified: {e}")
    finally:
        conn.close()

def mark_task_as_completed(task_id, completed=True):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(completed), task_id))
        conn.commit()
        logging.info(f"Task marked as {'completed' if completed else 'uncompleted'} with ID: {task_id}")
    except Exception as e:
        logging.error(f"Error marking task as {'completed' if completed else 'uncompleted'}: {e}")
    finally:
        conn.close()

def update_task_due_date(task_id, new_due_date):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (new_due_date, task_id))
        conn.commit()
        logging.info(f"Task due date updated with ID: {task_id}")
    except Exception as e:
        logging.error(f"Error updating task due date: {e}")
    finally:
        conn.close()
