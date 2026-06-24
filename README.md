# 💬 Real-Time Chat Application

A real-time chat application built with Flask and Socket.IO that allows users to host or join chat rooms for instant messaging conversations.

![Chat App Demo](https://img.shields.io/badge/demo-live-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-2.0+-red)
![Socket.IO](https://img.shields.io/badge/socket.io-4.5+-yellow)

## ✨ Features

- **Real-time messaging** with WebSocket technology
- **Host/participant roles** with host badges
- **Unique room IDs** for each conversation
- **User presence** - see who's online
- **Typing indicators** - know when someone is typing
- **Join/leave notifications**
- **Share room links** with others
- **Responsive design** - works on desktop and mobile
- **No database required** - lightweight and easy to deploy

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/chat-app.git
cd chat-app
Create a virtual environment (optional but recommended)

bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install dependencies

bash
pip install -r requirements.txt
Run the application

bash
python app.py
Open your browser and navigate to:

text
http://localhost:5000
📦 Requirements
Create a requirements.txt file with:

txt
Flask==2.3.2
Flask-SocketIO==5.3.4
eventlet==0.33.3
python-socketio==5.9.0
Install all requirements at once:
bash
pip install -r requirements.txt
🎯 How to Use
Host a Chat
Click "Host a Chat" on the homepage

You'll receive a unique Room ID

Share the Room ID or the join link with others

Start chatting!

Join a Chat
Click "Join a Chat" on the homepage

Enter the Room ID provided by the host

Enter your name

Click "Join Chat" and start talking!

🏗️ Project Structure
text
chat-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Git ignore file
├── templates/
│   ├── index.html        # Homepage
│   ├── join.html         # Join chat page
│   └── chat.html         # Chat room page
└── static/
    ├── style.css         # Shared styles
    ├── index.css         # Homepage styles
    ├── join.css          # Join page styles
    └── chat.css          # Chat page styles
🔧 Configuration
The app uses default settings, but you can customize:

In app.py:
python
# Change port or host
socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# Change secret key
app.config['SECRET_KEY'] = 'your-secret-key-here'
