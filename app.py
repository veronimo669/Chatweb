from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import secrets
from datetime import datetime
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
app.config['MAX_FORM_MEMORY_SIZE'] = 1024 * 1024 * 1024  # 1GB
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', 
                    ping_timeout=60, ping_interval=25)

# Store active rooms and users
rooms = {}
user_sessions = {}

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

print(f"📁 Files saved to: {UPLOAD_DIR}")

def get_file_icon(filename):
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    icons = {
        'txt': '📄', 'pdf': '📄', 'doc': '📝', 'docx': '📝',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
        'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬',
        'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
        'zip': '📦', 'rar': '📦', '7z': '📦',
        'py': '💻', 'js': '💻', 'html': '💻', 'css': '💻',
        'exe': '⚙️', 'msi': '⚙️'
    }
    return icons.get(ext, '📎')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host')
def host():
    room_id = secrets.token_hex(4)
    return render_template('chat.html', room_id=room_id, is_host=True)

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/chat/<room_id>')
def chat(room_id):
    return render_template('chat.html', room_id=room_id, is_host=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload - FIXED VERSION"""
    try:
        print("=" * 50)
        print("📤 Upload request received")
        
        # Get form data
        room_id = request.form.get('room_id', '')
        username = request.form.get('username', 'Unknown')
        
        print(f"📋 Room ID: {room_id}")
        print(f"📋 Username: {username}")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            print("❌ No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file details
        original_filename = file.filename
        print(f"📄 Original filename: {original_filename}")
        
        # Save file with unique name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = secrets.token_hex(4)
        safe_filename = f"{timestamp}_{unique_id}_{original_filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save file
        print(f"💾 Saving to: {file_path}")
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        print(f"✅ File saved successfully! Size: {file_size} bytes")
        
        # Broadcast to room via Socket.IO - FIXED
        if room_id and room_id in rooms:
            print(f"📢 Broadcasting to room: {room_id}")
            
            # Store file info in room
            if 'files' not in rooms[room_id]:
                rooms[room_id]['files'] = []
            
            file_info = {
                'filename': original_filename,
                'uploader': username,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'size': file_size,
                'icon': get_file_icon(original_filename),
                'file_id': safe_filename
            }
            rooms[room_id]['files'].append(file_info)
            
            # Use socketio.emit with room parameter - FIXED
            socketio.emit('receive_file_info', {
                'username': username,
                'filename': original_filename,
                'file_size': file_size,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'is_host': username == rooms[room_id].get('host'),
                'icon': get_file_icon(original_filename),
                'file_id': safe_filename
            }, room=room_id, namespace='/')
            
            print("✅ Broadcast complete")
        else:
            print(f"⚠️ Room {room_id} not found")
        
        print("=" * 50)
        return jsonify({
            'success': True,
            'filename': original_filename,
            'file_id': safe_filename,
            'size': file_size,
            'path': file_path
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    """Download uploaded file"""
    try:
        file_path = os.path.join(UPLOAD_DIR, file_id)
        if os.path.exists(file_path):
            parts = file_id.split('_', 2)
            original_filename = parts[2] if len(parts) > 2 else file_id
            return send_file(file_path, as_attachment=True, download_name=original_filename)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files')
def list_files():
    """List all uploaded files"""
    files = []
    for f in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(file_path):
            files.append({
                'name': f,
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            })
    return jsonify({
        'directory': UPLOAD_DIR,
        'count': len(files),
        'files': files
    })

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'🔌 Client connected: {request.sid}')
    user_sessions[request.sid] = {'room': None, 'username': None}

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in user_sessions:
        room = user_sessions[sid]['room']
        username = user_sessions[sid]['username']
        
        if room and room in rooms:
            if username in rooms[room]['users']:
                rooms[room]['users'].remove(username)
            socketio.emit('user_left', {
                'username': username,
                'user_count': len(rooms[room]['users'])
            }, room=room, namespace='/')
            
            if len(rooms[room]['users']) == 0:
                # Clean up files
                for file_info in rooms[room].get('files', []):
                    file_path = os.path.join(UPLOAD_DIR, file_info['file_id'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                del rooms[room]
        
        del user_sessions[sid]

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    username = data.get('username', f'User_{secrets.token_hex(3)}')
    is_host = data.get('is_host', False)
    
    if room_id not in rooms:
        rooms[room_id] = {
            'host': None,
            'users': [],
            'files': []
        }
        print(f"🏠 Created room: {room_id}")
    
    if is_host:
        rooms[room_id]['host'] = username
    
    if username not in rooms[room_id]['users']:
        rooms[room_id]['users'].append(username)
    
    user_sessions[request.sid]['room'] = room_id
    user_sessions[request.sid]['username'] = username
    
    join_room(room_id)
    
    emit('join_confirmation', {
        'username': username,
        'room_id': room_id,
        'is_host': is_host,
        'user_count': len(rooms[room_id]['users'])
    })
    
    emit('user_joined', {
        'username': username,
        'user_count': len(rooms[room_id]['users'])
    }, room=room_id)
    
    existing_users = [u for u in rooms[room_id]['users'] if u != username]
    if existing_users:
        emit('existing_users', {'users': existing_users})

@socketio.on('send_message')
def handle_send_message(data):
    room_id = data['room_id']
    username = data['username']
    message = data['message']
    timestamp = data.get('timestamp', '')
    
    emit('receive_message', {
        'username': username,
        'message': message,
        'timestamp': timestamp,
        'is_host': username == rooms[room_id]['host'] if room_id in rooms else False
    }, room=room_id)

@socketio.on('typing')
def handle_typing(data):
    room_id = data['room_id']
    username = data['username']
    is_typing = data.get('is_typing', False)
    
    emit('user_typing', {
        'username': username,
        'is_typing': is_typing
    }, room=room_id, include_self=False)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Chat Server Starting...")
    print(f"📁 Files saved to: {UPLOAD_DIR}")
    print(f"🌐 Server running at: http://localhost:4444")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=4444, debug=True, use_reloader=False)
