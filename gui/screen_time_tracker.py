import time
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
import logging

class ScreenTimeTracker(QObject):
    screen_time_exceeded = pyqtSignal()
    screen_time_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.reminder_enabled = False
        self.start_time = time.time()
        self.screen_time_timer = QTimer()
        self.screen_time_timer.timeout.connect(self.check_screen_time)
        self.rest_reminder_interval = 3600  # Remind every hour
        self.break_duration = 300  # 5 minutes break
        self.break_timer = QTimer()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("ScreenTimeTracker initialized.")

    def toggle_reminder(self, enable):
        self.reminder_enabled = enable
        if self.reminder_enabled:
            self.screen_time_timer.start(1000)  # Check every second for real-time display
            logging.info("Screen time reminder enabled.")
        else:
            self.screen_time_timer.stop()
            self.break_timer.stop()
            self.start_time = time.time()  # Reset timer when disabled
            logging.info("Screen time reminder disabled.")

    def check_screen_time(self):
        if not self.reminder_enabled:
            return
        elapsed_time = time.time() - self.start_time
        self.update_screen_time_display(elapsed_time)
        logging.debug(f"Checking screen time: {elapsed_time} seconds elapsed.")
        if elapsed_time >= self.rest_reminder_interval:
            self.screen_time_exceeded.emit()
            logging.info("Screen time exceeded. Emitting reminder to rest.")
            self.start_time = time.time()  # Reset timer after showing reminder
            self.reminder_enabled = False  # Disable the reminder
            self.screen_time_timer.stop()  # Stop the timer

    def start_break_timer(self):
        self.break_timer.stop()
        self.break_timer.timeout.connect(self.end_break)
        self.break_timer.start(self.break_duration * 1000)  # Convert to milliseconds
        logging.info(f"Break started for {self.break_duration} seconds.")

    def end_break(self):
        self.break_timer.stop()
        logging.info("Break ended. User can resume work.")

    def set_reminder_interval(self, interval_seconds):
        self.rest_reminder_interval = interval_seconds
        logging.info(f"Rest reminder interval set to {interval_seconds} seconds.")

    def set_break_duration(self, duration_seconds):
        self.break_duration = duration_seconds
        logging.info(f"Break duration set to {duration_seconds} seconds.")

    def update_screen_time_display(self, elapsed_time):
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        self.screen_time_updated.emit(formatted_time)
        logging.debug(f"Screen time updated: {formatted_time}")

    def get_current_screen_time(self):
        elapsed_time = time.time() - self.start_time
        return self.format_time(elapsed_time)
    
    def set_rest_duration(self, duration):
        self.rest_duration = duration

    def get_rest_duration(self):
        return self.rest_duration

    def set_custom_message(self, message):
        self.custom_message = message

    def get_custom_message(self):
        return self.custom_message if hasattr(self, 'custom_message') else "Time to take a break!"

    @staticmethod
    def format_time(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
