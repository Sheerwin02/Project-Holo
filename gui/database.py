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
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, title TEXT, content TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, title TEXT, due_date TEXT, priority TEXT, description TEXT, recurring TEXT, completed INTEGER DEFAULT 0, notified INTEGER DEFAULT 0)''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        conn.close()

# Note functions
def save_note_to_db(user_id, title, content):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id FROM notes WHERE user_id = ? AND title = ?", (user_id, title))
        result = c.fetchone()
        if result:
            c.execute("UPDATE notes SET content = ? WHERE user_id = ? AND title = ?", (content, user_id, title))
        else:
            c.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (user_id, title, content))
        conn.commit()
        logging.info(f"Note saved successfully with title: {title} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error saving note: {e}")
    finally:
        conn.close()

def get_all_notes(user_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id, title FROM notes WHERE user_id = ? ORDER BY id ASC", (user_id,))
        notes = c.fetchall()
        logging.info("Notes retrieved successfully.")
        return notes
    except Exception as e:
        logging.error(f"Error retrieving notes: {e}")
        return []
    finally:
        conn.close()

def load_note_from_db(user_id, note_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT title, content FROM notes WHERE user_id = ? AND id = ?", (user_id, note_id))
        note = c.fetchone()
        logging.info(f"Note loaded successfully with ID: {note_id} for user: {user_id}")
        return note
    except Exception as e:
        logging.error(f"Error loading note: {e}")
        return None
    finally:
        conn.close()

def delete_note_from_db(user_id, note_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("DELETE FROM notes WHERE user_id = ? AND id = ?", (user_id, note_id))
        conn.commit()
        logging.info(f"Note deleted successfully with ID: {note_id} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error deleting note: {e}")
    finally:
        conn.close()

# Task functions
def save_task_to_db(user_id, title, due_date, priority, description, recurring):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT id FROM tasks WHERE user_id = ? AND title = ?", (user_id, title))
        result = c.fetchone()
        if result:
            c.execute("""
                UPDATE tasks 
                SET due_date = ?, priority = ?, description = ?, recurring = ?, notified = 0 
                WHERE user_id = ? AND title = ?
            """, (due_date, priority, description, recurring, user_id, title))
        else:
            c.execute("""
                INSERT INTO tasks (user_id, title, due_date, priority, description, recurring) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, title, due_date, priority, description, recurring))
        conn.commit()
        logging.info(f"Task saved successfully with title: {title} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error saving task: {e}")
    finally:
        conn.close()

def get_all_tasks(user_id, show_completed=False):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        if show_completed:
            c.execute("SELECT id, title, due_date, priority, description, completed FROM tasks WHERE user_id = ? ORDER BY due_date ASC, id ASC", (user_id,))
        else:
            c.execute("SELECT id, title, due_date, priority, description, completed FROM tasks WHERE user_id = ? AND completed = 0 ORDER BY due_date ASC, id ASC", (user_id,))
        tasks = c.fetchall()
        logging.info("Tasks retrieved successfully.")
        return tasks
    except Exception as e:
        logging.error(f"Error retrieving tasks: {e}")
        return []
    finally:
        conn.close()

def load_task_from_db(user_id, task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("SELECT title, due_date, priority, description, recurring, completed FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
        task = c.fetchone()
        logging.info(f"Task loaded successfully with ID: {task_id} for user: {user_id}")
        return task
    except Exception as e:
        logging.error(f"Error loading task: {e}")
        return None
    finally:
        conn.close()

def delete_task_from_db(user_id, task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
        conn.commit()
        logging.info(f"Task deleted successfully with ID: {task_id} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error deleting task: {e}")
    finally:
        conn.close()

def mark_task_as_notified(user_id, task_id):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET notified = 1 WHERE user_id = ? AND id = ?", (user_id, task_id))
        conn.commit()
        logging.info(f"Task marked as notified with ID: {task_id} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error marking task as notified: {e}")
    finally:
        conn.close()

def mark_task_as_completed(user_id, task_id, completed=True):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET completed = ? WHERE user_id = ? AND id = ?", (int(completed), user_id, task_id))
        conn.commit()
        logging.info(f"Task marked as {'completed' if completed else 'uncompleted'} with ID: {task_id} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error marking task as {'completed' if completed else 'uncompleted'}: {e}")
    finally:
        conn.close()

def update_task_due_date(user_id, task_id, new_due_date):
    try:
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("UPDATE tasks SET due_date = ? WHERE user_id = ? AND id = ?", (new_due_date, user_id, task_id))
        conn.commit()
        logging.info(f"Task due date updated with ID: {task_id} for user: {user_id}")
    except Exception as e:
        logging.error(f"Error updating task due date: {e}")
    finally:
        conn.close()
