import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QLabel, QInputDialog, QMessageBox, QFormLayout, QTextEdit, QDateEdit, QComboBox, QWidget, QListWidgetItem, QTabWidget, QCalendarWidget, QProgressBar
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap, QColor
from fpdf import FPDF
import matplotlib.pyplot as plt
import webbrowser
import sys
import os
import re
sys.path.append('../server')
from assistant import get_completion, create_assistant, create_thread
from utils import get_current_location, get_weather, get_news_updates

DATABASE = 'goals.db'

funcs = [get_current_location, get_weather, get_news_updates]

assistant_id = create_assistant(name="Holo", instructions="You are a helpful assistant.", model="gpt-4o")
thread_id = create_thread(debug=True)

def normalize_text(text):
    # Replace or remove unsupported characters
    replacements = {
        "’": "'",  # Replace right single quotation mark
        "–": "-",  # Replace en dash
        "—": "-",  # Replace em dash
        "“": '"',  # Replace left double quotation mark
        "”": '"',  # Replace right double quotation mark
        "…": "..." # Replace ellipsis
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining unsupported characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text
    
class GoalSetting:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE)
        self.create_table()

    def create_table(self):
        """Create the goals table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                priority INTEGER,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                user_id TEXT NOT NULL,
                category TEXT,
                progress REAL DEFAULT 0,
                archived BOOLEAN DEFAULT 0
            )
        ''')
        self.conn.commit()

    def add_goal(self, title, description, deadline, priority, user_id, category):
        """Add a new goal to the database with validation."""
        if not title:
            raise ValueError("Title is required.")
        if priority not in range(1, 6):
            raise ValueError("Priority must be between 1 and 5.")
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Deadline must be in YYYY-MM-DD format.")

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO goals (title, description, deadline, priority, status, created_at, user_id, category) 
            VALUES (?, ?, ?, ?, 'incomplete', ?, ?, ?)
        ''', (title, description, deadline, priority, datetime.now().isoformat(), user_id, category))
        self.conn.commit()

    def get_goals(self, user_id, include_archived=False):
        """Retrieve goals from the database."""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM goals WHERE user_id = ?'
        if not include_archived:
            query += ' AND archived = 0'
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

    def complete_goal(self, goal_id):
        """Mark a goal as complete."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE goals SET status = 'complete', completed_at = ? WHERE id = ?
        ''', (datetime.now().isoformat(), goal_id))
        self.conn.commit()

    def delete_goal(self, goal_id):
        """Delete a goal from the database."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        self.conn.commit()

    def update_progress(self, goal_id, progress):
        """Update the progress of a goal."""
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")
        cursor = self.conn.cursor()
        cursor.execute('UPDATE goals SET progress = ? WHERE id = ?', (progress, goal_id))
        self.conn.commit()

    def archive_goal(self, goal_id):
        """Archive a goal."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE goals SET archived = 1 WHERE id = ?', (goal_id,))
        self.conn.commit()

    def unarchive_goal(self, goal_id):
        """Unarchive a goal."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE goals SET archived = 0 WHERE id = ?', (goal_id,))
        self.conn.commit()

    def get_goals_by_category(self, user_id, category):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM goals WHERE user_id = ? AND category = ?', (user_id, category))
        return cursor.fetchall()

    def get_upcoming_deadlines(self, user_id, days=7):
        cursor = self.conn.cursor()
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        cursor.execute('SELECT * FROM goals WHERE user_id = ? AND deadline BETWEEN ? AND ?', 
                       (user_id, today.isoformat(), future_date.isoformat()))
        return cursor.fetchall()

    def generate_report(self, user_id, start_date=None, end_date=None):
        """Generate a report of goals within the specified date range."""
        cursor = self.conn.cursor()
        
        if start_date and end_date:
            query = 'SELECT * FROM goals WHERE user_id = ? AND created_at BETWEEN ? AND ?'
            cursor.execute(query, (user_id, start_date, end_date))
        else:
            query = 'SELECT * FROM goals WHERE user_id = ?'
            cursor.execute(query, (user_id,))
        
        goals = cursor.fetchall()
        
        report_path = None
        if goals:
            # Generate progress chart if goals exist
            titles = [goal[1] for goal in goals]
            progress = [goal[10] for goal in goals]

            plt.figure(figsize=(10, 6))
            plt.barh(titles, progress, color='skyblue')
            plt.xlabel('Progress (%)')
            plt.title('Goals Progress Report')
            plt.tight_layout()
            report_path = 'progress_report.png'
            plt.savefig(report_path)
            plt.close()

            # Calculate additional insights
            total_goals = len(goals)
            completed_goals = sum(1 for goal in goals if goal[5] == 'complete')
            average_progress = sum(progress) / total_goals
            overdue_goals = sum(1 for goal in goals if goal[3] < datetime.now().strftime('%Y-%m-%d') and goal[5] != 'complete')
            
            category_count = {}
            for goal in goals:
                category = goal[9]
                if category in category_count:
                    category_count[category] += 1
                else:
                    category_count[category] = 1
            
            # Save report content to a text file for AI analysis
            report_content = "\n".join([
                f"ID: {goal[0]}, Title: {goal[1]}, Status: {goal[5]}, Progress: {goal[10]}%, Deadline: {goal[3]}, Category: {goal[9]}"
                for goal in goals
            ])
            report_content += "\n\n"
            report_content += f"Total Goals: {total_goals}\n"
            report_content += f"Completed Goals: {completed_goals}\n"
            report_content += f"Average Progress: {average_progress:.2f}%\n"
            report_content += f"Overdue Goals: {overdue_goals}\n"
            report_content += "Goals per Category:\n"
            for category, count in category_count.items():
                report_content += f"  {category}: {count}\n"

            with open("report_content.txt", "w") as report_file:
                report_file.write(report_content)
        
        return goals, report_path

    def export_report_to_pdf(self, user_id):
        goals = self.get_goals(user_id)
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Goal Report", 0, 1, 'C')
        pdf.ln(10)
        
        # Add goals table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(10, 10, "ID", 1)
        pdf.cell(50, 10, "Title", 1)
        pdf.cell(30, 10, "Status", 1)
        pdf.cell(30, 10, "Progress", 1)
        pdf.cell(40, 10, "Deadline", 1)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for goal in goals:
            pdf.cell(10, 10, str(goal[0]), 1)
            pdf.cell(50, 10, str(goal[1]), 1)
            pdf.cell(30, 10, str(goal[5]), 1)
            pdf.cell(30, 10, f"{str(goal[10])}%", 1)
            pdf.cell(40, 10, str(goal[3]), 1)
            pdf.ln()
        
        # Calculate additional insights
        total_goals = len(goals)
        completed_goals = sum(1 for goal in goals if goal[5] == 'complete')
        average_progress = sum(goal[10] for goal in goals) / total_goals if total_goals > 0 else 0
        overdue_goals = sum(1 for goal in goals if goal[3] < datetime.now().strftime('%Y-%m-%d') and goal[5] != 'complete')
        
        category_count = {}
        for goal in goals:
            category = goal[9]
            if category in category_count:
                category_count[category] += 1
            else:
                category_count[category] = 1

        # Add insights to PDF
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Insights", 0, 1)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Total Goals: {total_goals}", 0, 1)
        pdf.cell(0, 10, f"Completed Goals: {completed_goals}", 0, 1)
        pdf.cell(0, 10, f"Average Progress: {average_progress:.2f}%", 0, 1)
        pdf.cell(0, 10, f"Overdue Goals: {overdue_goals}", 0, 1)
        
        pdf.cell(0, 10, "Goals per Category:", 0, 1)
        for category, count in category_count.items():
            pdf.cell(0, 10, f"  {category}: {count}", 0, 1)

        if total_goals > 0:
            # Generate charts
            report_path = 'progress_report.png'
            titles = [goal[1] for goal in goals]
            progress = [goal[10] for goal in goals]
            
            plt.figure(figsize=(10, 6))
            plt.barh(titles, progress, color='skyblue')
            plt.xlabel('Progress (%)')
            plt.title('Goals Progress Report')
            plt.tight_layout()
            plt.savefig(report_path)
            plt.close()
            
            # Add charts to PDF
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Progress Chart", 0, 1)
            
            pdf.image(report_path, x=10, y=30, w=180)

        # Get AI suggestions
        try:
            report_content = "\n".join([f"ID: {goal[0]}, Title: {goal[1]}, Description: {goal[2]}, Status: {goal[5]}, Progress: {goal[10]}%" for goal in goals])
            user_input = f"Analyze the following goal report and provide professional suggestions\n\n{report_content}"
            suggestions = get_completion(assistant_id, thread_id, user_input, funcs, debug=True)
        except Exception as e:
            suggestions = "AI analysis not available due to an error."

        # Normalize suggestions to replace unsupported characters
        suggestions = normalize_text(suggestions)

        # Add AI suggestions to PDF
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "AI Suggestions", 0, 1)
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, suggestions)

        # Get AI-generated motivational quote
        try:
            quote_input = "Provide a motivational quote to inspire productivity and goal achievement."
            motivational_quote = get_completion(assistant_id, thread_id, quote_input, funcs, debug=True)
        except Exception as e:
            motivational_quote = "Keep pushing forward and never give up on your dreams."

        # Normalize motivational quote to replace unsupported characters
        motivational_quote = normalize_text(motivational_quote)

        # Add a motivational quote to the bottom of the last page
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 12)
        pdf.multi_cell(0, 10, motivational_quote)
        
        # Save PDF
        pdf_path = "goal_report.pdf"
        pdf.output(pdf_path)
        return pdf_path

class DashboardWidget(QWidget):
    def __init__(self, goal_setting, user_id):
        super().__init__()
        self.goal_setting = goal_setting
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Overview section
        self.overview_label = QLabel("Goal Overview")
        self.layout.addWidget(self.overview_label)

        self.overview_details = QLabel()
        self.layout.addWidget(self.overview_details)
        self.update_overview()

        # Search and Filter section
        filter_layout = QHBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search goals...")
        self.search_bar.textChanged.connect(self.filter_goals)
        filter_layout.addWidget(self.search_bar)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Personal", "Professional", "Health", "Finance", "Other"])
        self.category_filter.currentTextChanged.connect(self.filter_goals)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)

        self.sort_filter = QComboBox()
        self.sort_filter.addItems(["Priority", "Deadline", "Title"])
        self.sort_filter.currentTextChanged.connect(self.filter_goals)
        filter_layout.addWidget(QLabel("Sort by:"))
        filter_layout.addWidget(self.sort_filter)

        self.layout.addLayout(filter_layout)

        # Goals list section
        self.goal_list = QListWidget()
        self.layout.addWidget(self.goal_list)

        # Upcoming deadlines section
        upcoming_label = QLabel("Upcoming Deadlines")
        self.layout.addWidget(upcoming_label)

        self.upcoming_list = QListWidget()

        self.layout.addWidget(self.upcoming_list)

        self.load_goals()
        self.load_upcoming_goals()

    def update_overview(self):
        goals = self.goal_setting.get_goals(self.user_id)
        total_goals = len(goals)
        completed_goals = len([g for g in goals if g[5] == 'complete'])
        overview_text = f"Total Goals: {total_goals}\nCompleted Goals: {completed_goals}"
        self.overview_details.setText(overview_text)

    def load_goals(self):
        self.goal_list.clear()
        goals = self.goal_setting.get_goals(self.user_id)
        sorted_goals = self.sort_goals(goals)
        for goal in sorted_goals:
            item = QListWidgetItem(f"{goal[1]} - {goal[5]} - Progress: {goal[10]}%")
            item.setData(Qt.ItemDataRole.UserRole, goal[0])
            # Color-code based on priority
            if goal[4] == 1:
                item.setBackground(QColor(255, 200, 200))  # Light red for high priority
            elif goal[4] == 2:
                item.setBackground(QColor(255, 255, 200))  # Light yellow for medium priority
            progress_bar = QProgressBar()
            progress_bar.setValue(int(goal[10]))
            self.goal_list.addItem(item)
            self.goal_list.setItemWidget(item, progress_bar)
        self.goal_list.itemClicked.connect(self.goal_clicked)

    def load_upcoming_goals(self):
        self.upcoming_list.clear()
        upcoming_goals = self.goal_setting.get_upcoming_deadlines(self.user_id)
        for goal in upcoming_goals:
            item = QListWidgetItem(f"{goal[1]} - Due: {goal[3]}")
            item.setData(Qt.ItemDataRole.UserRole, goal[0])
            self.upcoming_list.addItem(item)
        self.upcoming_list.itemClicked.connect(self.goal_clicked)

    def filter_goals(self):
        search_text = self.search_bar.text().lower()
        category = self.category_filter.currentText()

        self.goal_list.clear()
        goals = self.goal_setting.get_goals(self.user_id)
        filtered_goals = [
            goal for goal in goals
            if (search_text in goal[1].lower() and (category == "All" or category == goal[9]))
        ]
        sorted_goals = self.sort_goals(filtered_goals)
        for goal in sorted_goals:
            item = QListWidgetItem(f"{goal[1]} - {goal[5]} - Progress: {goal[10]}%")
            item.setData(Qt.ItemDataRole.UserRole, goal[0])
            if goal[4] == 1:
                item.setBackground(QColor(255, 200, 200))
            elif goal[4] == 2:
                item.setBackground(QColor(255, 255, 200))
            progress_bar = QProgressBar()
            progress_bar.setValue(int(goal[10]))
            self.goal_list.addItem(item)
            self.goal_list.setItemWidget(item, progress_bar)
        self.goal_list.itemClicked.connect(self.goal_clicked)

    def sort_goals(self, goals):
        sort_by = self.sort_filter.currentText()
        if sort_by == "Priority":
            return sorted(goals, key=lambda x: x[4])
        elif sort_by == "Deadline":
            return sorted(goals, key=lambda x: x[3])
        elif sort_by == "Title":
            return sorted(goals, key=lambda x: x[1].lower())
        return goals

    def goal_clicked(self, item):
        goal_id = item.data(Qt.ItemDataRole.UserRole)
        goal = self.goal_setting.get_goals(self.user_id, include_archived=True)
        goal = next((g for g in goal if g[0] == goal_id), None)
        if goal:
            details_dialog = QDialog(self)
            details_dialog.setWindowTitle('Goal Details')
            layout = QVBoxLayout()

            layout.addWidget(QLabel(f"Title: {goal[1]}"))
            layout.addWidget(QLabel(f"Description: {goal[2]}"))
            layout.addWidget(QLabel(f"Deadline: {goal[3]}"))
            layout.addWidget(QLabel(f"Priority: {goal[4]}"))
            layout.addWidget(QLabel(f"Status: {goal[5]}"))
            layout.addWidget(QLabel(f"Created At: {goal[6]}"))
            layout.addWidget(QLabel(f"Completed At: {goal[7]}"))
            layout.addWidget(QLabel(f"Category: {goal[9]}"))
            layout.addWidget(QLabel(f"Progress: {goal[10]}%"))

            if goal[5] != 'complete':
                complete_button = QPushButton('Mark as Complete')
                complete_button.clicked.connect(lambda: self.mark_as_complete(goal_id, details_dialog))
                layout.addWidget(complete_button)
            
            edit_button = QPushButton('Edit Goal')
            edit_button.clicked.connect(lambda: self.edit_goal(goal_id, details_dialog))
            layout.addWidget(edit_button)

            details_dialog.setLayout(layout)
            details_dialog.exec()

    def mark_as_complete(self, goal_id, dialog):
        confirmation = QMessageBox.question(self, "Confirm Completion", "Are you sure you want to mark this goal as complete?")
        if confirmation == QMessageBox.StandardButton.Yes:
            self.goal_setting.complete_goal(goal_id)
            self.refresh_dashboard()
            dialog.close()

    def edit_goal(self, goal_id, dialog):
        goal = self.goal_setting.get_goals(self.user_id, include_archived=True)
        goal = next((g for g in goal if g[0] == goal_id), None)
        if goal:
            form_layout = QFormLayout()

            title_edit = QLineEdit(self)
            title_edit.setText(goal[1])
            form_layout.addRow('Title:', title_edit)

            description_edit = QTextEdit(self)
            description_edit.setText(goal[2])
            form_layout.addRow('Description:', description_edit)

            deadline_edit = QDateEdit(self)
            deadline_edit.setDisplayFormat('yyyy-MM-dd')
            deadline_edit.setDate(QDate.fromString(goal[3], 'yyyy-MM-dd'))
            form_layout.addRow('Deadline:', deadline_edit)

            priority_combo = QComboBox(self)
            priority_combo.addItems([str(i) for i in range(1, 6)])
            priority_combo.setCurrentText(str(goal[4]))
            form_layout.addRow('Priority:', priority_combo)

            category_combo = QComboBox(self)
            category_combo.addItems(["Personal", "Professional", "Health", "Finance", "Other"])
            category_combo.setCurrentText(goal[9])
            form_layout.addRow('Category:', category_combo)

            edit_dialog = QDialog(self)
            edit_dialog.setWindowTitle('Edit Goal')
            edit_dialog.setLayout(form_layout)
            edit_dialog.setFixedSize(300, 250)

            buttons_layout = QHBoxLayout()
            save_button = QPushButton('Save', edit_dialog)
            cancel_button = QPushButton('Cancel', edit_dialog)
            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)
            form_layout.addRow(buttons_layout)

            save_button.clicked.connect(lambda: self.save_goal_edit(goal_id, title_edit, description_edit, deadline_edit, priority_combo, category_combo, edit_dialog, dialog))
            cancel_button.clicked.connect(edit_dialog.reject)

            edit_dialog.exec()

    def save_goal_edit(self, goal_id, title_edit, description_edit, deadline_edit, priority_combo, category_combo, edit_dialog, details_dialog):
        try:
            title = title_edit.text()
            description = description_edit.toPlainText()
            deadline = deadline_edit.date().toString('yyyy-MM-dd')
            priority = int(priority_combo.currentText())
            category = category_combo.currentText()

            self.goal_setting.add_goal(title, description, deadline, priority, self.user_id, category)
            self.goal_setting.delete_goal(goal_id)

            self.refresh_dashboard()

            edit_dialog.close()
            details_dialog.close()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def refresh_dashboard(self):
        self.load_goals()
        self.load_upcoming_goals()
        self.update_overview()

class GoalSettingDialog(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.goal_setting = GoalSetting()
        self.setWindowTitle("Goal Setting Application")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_goals_tab(), "Goals")
        self.dashboard_tab = DashboardWidget(self.goal_setting, self.user_id)
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.create_calendar_tab(), "Calendar")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Ensure goals are loaded initially
        self.load_goals()
        self.dashboard_tab.load_goals()
        self.dashboard_tab.load_upcoming_goals()

    def create_goals_tab(self):
        goals_widget = QWidget()
        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search goals...")
        self.search_bar.textChanged.connect(self.filter_goals)
        layout.addWidget(self.search_bar)

        # Filters
        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Personal", "Professional", "Health", "Finance", "Other"])
        self.category_filter.currentTextChanged.connect(self.filter_goals)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)

        self.goal_list = QListWidget()
        layout.addWidget(self.goal_list)
        self.load_goals()

        button_layout = QHBoxLayout()
        buttons = [
            ("Add Goal", self.add_goal),
            ("Complete Goal", self.complete_goal),
            ("Delete Goal", self.delete_goal),
            ("Update Progress", self.update_progress),
            ("Archive Goal", self.archive_goal),
            ("Generate Report", self.generate_report),
            ("Export Report", self.export_report_to_pdf),
            ("Analyze Report", self.analyze_report)  
        ]
        for button_text, button_function in buttons:
            button = QPushButton(button_text)
            button.clicked.connect(button_function)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        goals_widget.setLayout(layout)
        return goals_widget

    def create_calendar_tab(self):
        calendar_widget = QWidget()
        layout = QVBoxLayout()
        
        calendar = QCalendarWidget()
        calendar.selectionChanged.connect(self.show_goals_for_date)
        layout.addWidget(calendar)
        
        self.date_goals_list = QListWidget()
        layout.addWidget(self.date_goals_list)
        
        calendar_widget.setLayout(layout)
        return calendar_widget

    def show_goals_for_date(self):
        selected_date = self.sender().selectedDate().toString("yyyy-MM-dd")
        goals = self.goal_setting.get_goals(self.user_id)
        date_goals = [goal for goal in goals if goal[3] == selected_date]
        
        self.date_goals_list.clear()
        for goal in date_goals:
            self.date_goals_list.addItem(f"{goal[1]} - {goal[5]}")

    def load_goals(self):
        self.goal_list.clear()
        goals = self.goal_setting.get_goals(self.user_id)
        for goal in goals:
            item = QListWidgetItem(f"{goal[0]}: {goal[1]} - {goal[5]} - Progress: {goal[10]}%")
            # Color-code based on priority
            if goal[4] == 1:
                item.setBackground(QColor(255, 200, 200))  # Light red for high priority
            elif goal[4] == 2:
                item.setBackground(QColor(255, 255, 200))  # Light yellow for medium priority
            self.goal_list.addItem(item)

    def filter_goals(self):
        search_text = self.search_bar.text().lower()
        category = self.category_filter.currentText()
        
        self.goal_list.clear()
        goals = self.goal_setting.get_goals(self.user_id)
        for goal in goals:
            if (search_text in goal[1].lower() and 
                (category == "All" or category == goal[9])):
                item = QListWidgetItem(f"{goal[0]}: {goal[1]} - {goal[5]} - Progress: {goal[10]}%")
                if goal[4] == 1:
                    item.setBackground(QColor(255, 200, 200))
                elif goal[4] == 2:
                    item.setBackground(QColor(255, 255, 200))
                self.goal_list.addItem(item)

        button_layout = QHBoxLayout()

        self.add_goal_button = QPushButton("Add Goal", self)
        self.add_goal_button.clicked.connect(self.add_goal)
        button_layout.addWidget(self.add_goal_button)

        self.complete_goal_button = QPushButton("Complete Goal", self)
        self.complete_goal_button.clicked.connect(self.complete_goal)
        button_layout.addWidget(self.complete_goal_button)

        self.delete_goal_button = QPushButton("Delete Goal", self)
        self.delete_goal_button.clicked.connect(self.delete_goal)
        button_layout.addWidget(self.delete_goal_button)

        self.update_progress_button = QPushButton("Update Progress", self)
        self.update_progress_button.clicked.connect(self.update_progress)
        button_layout.addWidget(self.update_progress_button)

        self.archive_goal_button = QPushButton("Archive Goal", self)
        self.archive_goal_button.clicked.connect(self.archive_goal)
        button_layout.addWidget(self.archive_goal_button)

        self.report_button = QPushButton("Generate Report", self)
        self.report_button.clicked.connect(self.generate_report)
        button_layout.addWidget(self.report_button)

        self.export_report_button = QPushButton("Export Report to PDF", self)
        self.export_report_button.clicked.connect(self.export_report_to_pdf)
        button_layout.addWidget(self.export_report_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def load_goals(self, include_archived=False):
        """Load goals from the database and display them in the list widget."""
        self.goal_list.clear()
        goals = self.goal_setting.get_goals(self.user_id, include_archived)
        for goal in goals:
            self.goal_list.addItem(f"{goal[0]}: {goal[1]} - {goal[5]} - Progress: {goal[10]}%")

    def add_goal(self):
        """Prompt the user for goal details and add the goal to the database."""
        try:
            form_layout = QFormLayout()

            title_edit = QLineEdit(self)
            form_layout.addRow('Title:', title_edit)

            description_edit = QTextEdit(self)
            form_layout.addRow('Description:', description_edit)

            deadline_edit = QDateEdit(self)
            deadline_edit.setDisplayFormat('yyyy-MM-dd')
            deadline_edit.setDate(QDate.currentDate())
            form_layout.addRow('Deadline:', deadline_edit)

            priority_combo = QComboBox(self)
            priority_combo.addItems([str(i) for i in range(1, 6)])
            form_layout.addRow('Priority:', priority_combo)

            category_combo = QComboBox(self)
            category_combo.addItems(["Personal", "Professional", "Health", "Finance", "Other"])
            form_layout.addRow('Category:', category_combo)

            dialog = QDialog(self)
            dialog.setWindowTitle('Add Goal')
            dialog.setLayout(form_layout)
            dialog.setFixedSize(300, 250)

            buttons_layout = QHBoxLayout()
            save_button = QPushButton('Save', dialog)
            cancel_button = QPushButton('Cancel', dialog)
            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)
            form_layout.addRow(buttons_layout)

            save_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                title = title_edit.text()
                description = description_edit.toPlainText()
                deadline = deadline_edit.date().toString('yyyy-MM-dd')
                priority = int(priority_combo.currentText())
                category = category_combo.currentText()

                self.goal_setting.add_goal(title, description, deadline, priority, self.user_id, category)
                self.refresh_all_tabs()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def complete_goal(self):
        """Mark the selected goal as complete."""
        selected_goal = self.goal_list.currentItem()
        if selected_goal:
            goal_id = int(selected_goal.text().split(':')[0])
            self.goal_setting.complete_goal(goal_id)
            self.refresh_all_tabs()
        else:
            QMessageBox.warning(self, "Select Goal", "Please select a goal to mark as complete.")

    def delete_goal(self):
        """Delete the selected goal from the database."""
        selected_goal = self.goal_list.currentItem()
        if selected_goal:
            goal_id = int(selected_goal.text().split(':')[0])
            self.goal_setting.delete_goal(goal_id)
            self.refresh_all_tabs()
        else:
            QMessageBox.warning(self, "Select Goal", "Please select a goal to delete.")

    def update_progress(self):
        """Update the progress of the selected goal."""
        selected_goal = self.goal_list.currentItem()
        if selected_goal:
            goal_id = int(selected_goal.text().split(':')[0])
            progress, ok = QInputDialog.getDouble(self, "Update Progress", "Enter progress (0-100):", 0, 0, 100, 2)
            if ok:
                try:
                    self.goal_setting.update_progress(goal_id, progress)
                    self.refresh_all_tabs()
                except ValueError as e:
                    QMessageBox.warning(self, "Input Error", str(e))
        else:
            QMessageBox.warning(self, "Select Goal", "Please select a goal to update progress.")

    def archive_goal(self):
        """Archive the selected goal."""
        selected_goal = self.goal_list.currentItem()
        if selected_goal:
            goal_id = int(selected_goal.text().split(':')[0])
            self.goal_setting.archive_goal(goal_id)
            self.refresh_all_tabs()
        else:
            QMessageBox.warning(self, "Select Goal", "Please select a goal to archive.")

    def generate_report(self):
        """Generate and display a report of all goals."""
        # Create a dialog to get the date range
        date_dialog = QDialog(self)
        date_dialog.setWindowTitle("Select Date Range")

        layout = QVBoxLayout()

        # Add start date input
        start_date_edit = QDateEdit(date_dialog)
        start_date_edit.setDisplayFormat('yyyy-MM-dd')
        start_date_edit.setDate(QDate.currentDate().addMonths(-1))  # Default to one month ago
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(start_date_edit)

        # Add end date input
        end_date_edit = QDateEdit(date_dialog)
        end_date_edit.setDisplayFormat('yyyy-MM-dd')
        end_date_edit.setDate(QDate.currentDate())  # Default to today
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(end_date_edit)

        # Add OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", date_dialog)
        cancel_button = QPushButton("Cancel", date_dialog)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        date_dialog.setLayout(layout)

        # Connect button signals to dialog accept/reject
        ok_button.clicked.connect(date_dialog.accept)
        cancel_button.clicked.connect(date_dialog.reject)

        # Show the dialog and get user input
        if date_dialog.exec() == QDialog.DialogCode.Accepted:
            start_date = start_date_edit.date().toString('yyyy-MM-dd')
            end_date = end_date_edit.date().toString('yyyy-MM-dd')

            try:
                goals, report_path = self.goal_setting.generate_report(self.user_id, start_date, end_date)

                if not goals:
                    QMessageBox.information(self, "No Data", "No goals found for the specified date range.")
                    return

                # Include descriptions in the report content
                report_content = "\n".join([f"ID: {goal[0]}, Title: {goal[1]}, Description: {goal[2]}, Status: {goal[5]}, Progress: {goal[10]}%" for goal in goals])

                # Save report content to a text file for AI analysis
                with open("report_content.txt", "w") as report_file:
                    report_file.write(report_content)

                report_dialog = QDialog(self)
                report_dialog.setWindowTitle('Goal Report')
                report_layout = QVBoxLayout()
                report_label = QLabel(report_content)
                report_layout.addWidget(report_label)

                if report_path:
                    report_image = QLabel()
                    report_image.setPixmap(QPixmap(report_path))
                    report_layout.addWidget(report_image)

                analyze_button = QPushButton('Analyze Report', report_dialog)
                analyze_button.clicked.connect(self.analyze_report)
                report_layout.addWidget(analyze_button)

                close_button = QPushButton('Close', report_dialog)
                close_button.clicked.connect(report_dialog.accept)
                report_layout.addWidget(close_button)

                report_dialog.setLayout(report_layout)
                report_dialog.exec()

            except ValueError as e:
                QMessageBox.warning(self, "Date Error", str(e))

    def export_report_to_pdf(self):
        pdf_path = self.goal_setting.export_report_to_pdf(self.user_id)
        if os.path.exists(pdf_path):
            webbrowser.open(pdf_path)  # Open the PDF file with the default PDF viewer
            QMessageBox.information(self, "Export Report", f"Report has been exported to {pdf_path}")
        else:
            QMessageBox.warning(self, "Export Report", "Failed to export report. Please try again.")

    def analyze_report(self):
        """Analyze the generated report using AI."""
        try:
            # Read the report content from the file
            with open("report_content.txt", "r") as report_file:
                report_content = report_file.read()

            # Prepare the user input for AI analysis
            user_input = f"Please analyze the following goal report and provide professional suggestions:\n\n{report_content}"

            # Get AI analysis and suggestions
            try:
                suggestions = get_completion(assistant_id, thread_id, user_input, funcs, debug=True)
            except Exception as e:
                QMessageBox.critical(self, "AI Analysis Error", f"An error occurred during AI analysis: {str(e)}")
                return

            # Display the analysis and suggestions in a dialog window
            analysis_dialog = QDialog(self)
            analysis_dialog.setWindowTitle('AI Analysis and Suggestions')
            layout = QVBoxLayout()
            
            analysis_label = QLabel(suggestions)
            layout.addWidget(analysis_label)
            
            close_button = QPushButton('Close', analysis_dialog)
            close_button.clicked.connect(analysis_dialog.accept)
            layout.addWidget(close_button)
            
            analysis_dialog.setLayout(layout)
            analysis_dialog.exec()
        except FileNotFoundError:
            QMessageBox.critical(self, "File Not Found", "The report content file 'report_content.txt' was not found.")
        except IOError as e:
            QMessageBox.critical(self, "File Error", f"An error occurred while reading the report content file: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred: {str(e)}")

    def refresh_all_tabs(self):
        self.dashboard_tab.refresh_dashboard()
        self.load_goals()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
