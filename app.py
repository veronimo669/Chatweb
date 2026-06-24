from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active rooms and users
rooms = {}
user_sessions = {}

@app.route('/')
def index():
    """Main page - user chooses to host or join"""
    return render_template('index.html')

@app.route('/host')
def host():
    """Host page - creates a chat room"""
    room_id = secrets.token_hex(4)  # Generate unique room ID
    return render_template('chat.html', room_id=room_id, is_host=True)

@app.route('/join')
def join():
    """Join page - user enters room ID to join"""
    return render_template('join.html')

@app.route('/chat/<room_id>')
def chat(room_id):
    """Chat page for participants"""
    return render_template('chat.html', room_id=room_id, is_host=False)

@socketio.on('connect')
def handle_connect():
    """Handle user connection"""
    print(f'Client connected: {request.sid}')
    user_sessions[request.sid] = {
        'room': None,
        'username': None
    }

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    sid = request.sid
    if sid in user_sessions:
        room = user_sessions[sid]['room']
        username = user_sessions[sid]['username']
        
        if room and room in rooms:
            if username in rooms[room]['users']:
                rooms[room]['users'].remove(username)
            
            # Notify others in the room
            emit('user_left', {
                'username': username,
                'user_count': len(rooms[room]['users'])
            }, room=room)
            
            # Delete room if empty
            if len(rooms[room]['users']) == 0:
                del rooms[room]
        
        del user_sessions[sid]

@socketio.on('join_room')
def handle_join_room(data):
    """Handle user joining a room"""
    room_id = data['room_id']
    username = data.get('username', f'User_{secrets.token_hex(3)}')
    is_host = data.get('is_host', False)
    
    # Create room if it doesn't exist
    if room_id not in rooms:
        rooms[room_id] = {
            'host': None,
            'users': []
        }
    
    # If host, set as host
    if is_host:
        rooms[room_id]['host'] = username
    
    # Add user to room
    if username not in rooms[room_id]['users']:
        rooms[room_id]['users'].append(username)
    
    # Store user info
    user_sessions[request.sid]['room'] = room_id
    user_sessions[request.sid]['username'] = username
    
    # Join the socket.io room
    join_room(room_id)
    
    # Send join confirmation to the user
    emit('join_confirmation', {
        'username': username,
        'room_id': room_id,
        'is_host': is_host,
        'user_count': len(rooms[room_id]['users'])
    })
    
    # Notify others in the room
    emit('user_joined', {
        'username': username,
        'user_count': len(rooms[room_id]['users'])
    }, room=room_id)
    
    # Send existing users to the new user
    existing_users = [u for u in rooms[room_id]['users'] if u != username]
    if existing_users:
        emit('existing_users', {
            'users': existing_users
        })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle incoming messages"""
    room_id = data['room_id']
    username = data['username']
    message = data['message']
    timestamp = data.get('timestamp', '')
    
    # Broadcast message to everyone in the room
    emit('receive_message', {
        'username': username,
        'message': message,
        'timestamp': timestamp,
        'is_host': username == rooms[room_id]['host'] if room_id in rooms else False
    }, room=room_id)

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    room_id = data['room_id']
    username = data['username']
    is_typing = data.get('is_typing', False)
    
    emit('user_typing', {
        'username': username,
        'is_typing': is_typing
    }, room=room_id, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=4444, debug=True)
