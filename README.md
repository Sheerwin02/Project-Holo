# Project Holo: Personal AI Virtual Assistant

![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)

Project Holo is an AI-powered virtual assistant designed to enhance productivity for university students by addressing information overload, poor time management, and stress. It leverages Natural Language Processing (NLP) and interactive features to provide a personalized, engaging experience.

---

## 📺 Demo

Watch the system in action: [YouTube Demo](https://youtu.be/pZEmARMFG9c)

## ✨ Features

- **AI Assistant Chat**: Text-to-speech and speech-to-text communication.
- **Task Management**: Create, track, and prioritize tasks.
- **Reminders & Notifications**: Customizable alerts for deadlines and events.
- **Focus Mode**: Minimize distractions during study sessions.
- **Calendar Integration**: Sync schedules and manage deadlines.
- **Goal Setting & Tracking**: Break down long-term goals into actionable steps.
- **OCR Feedback**: Extract and analyze text from images/documents.
- **Sticky Notes**: Digital notes for quick ideas and reminders.
- **Screen Time Tracker**: Monitor daily app and website usage.

---

## 🛠️ Technologies Used

- **Programming Language**: Python 3.10+
- **GUI Framework**: PyQt
- **Database**: SQLite3
- **IDE**: VS Code
- **Methodology**: V-Model Development
- **Operating System**: Windows 11

---

## 📥 Installation

### Prerequisites

- Python 3.10+
- Windows 11 (recommended)
- Stable internet connection (for initial setup)

### Steps

1. Clone the repository:

```bash
git clone https://github.com/Sheerwin02/Project-Holo.git
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

## 🚀 Running the Project

### Backend Server

1. Navigate to the `server` directory:

```bash
cd server

```

2. Start the FastAPI server:

```bash
uvicorn run:app --reload
```

The server will run at http://localhost:8000.

### GUI Interface

1. Open a new terminal (keep the backend server running)

2. Navigate to the GUI directory

```bash
cd GUI
```

3. Launch the PyQt interface

```bash
python main.py
```

### Limitations

1. Limited customization options for avatars and voice (If there's runtime error in voice api it cannot run).

2. Dependency on third-party integrations (e.g., Google Calendar).

3. Requires internet connectivity for full functionality.
