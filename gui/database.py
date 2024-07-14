import sqlite3

def initialize_db():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_note_to_db(title, content):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('INSERT INTO notes (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()

def load_note_from_db(note_id):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('SELECT title, content FROM notes WHERE id = ?', (note_id,))
    note = c.fetchone()
    conn.close()
    return note

def get_all_notes():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('SELECT id, title FROM notes')
    notes = c.fetchall()
    conn.close()
    return notes

def update_note_in_db(note_id, title, content):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('UPDATE notes SET title = ?, content = ? WHERE id = ?', (title, content, note_id))
    conn.commit()
    conn.close()

def delete_note_from_db(note_id):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

initialize_db()
