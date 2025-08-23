from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import os

app = Flask(__name__)

# Database setup for local development
def init_db():
    """Initialize SQLite database for local development"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def save_to_database(user_message, bot_response):
    """Save message to SQLite database (local only)"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_message, bot_response)
        VALUES (?, ?)
    ''', (user_message, bot_response))
    conn.commit()
    conn.close()

def get_chat_history():
    """Get chat history from SQLite database"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_message, bot_response, timestamp FROM messages ORDER BY timestamp')
    history = cursor.fetchall()
    conn.close()
    return history

def clear_chat_history():
    """Clear all chat history from database"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages')
    conn.commit()
    conn.close()

# Simple bot response generator (NO API integrations)
def generate_bot_response(user_message):
    """Generate simple bot responses without any external APIs"""
    
    # Enhanced responses dictionary
    responses = {
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! What can I do for you?",
        "hey": "Hey! How's it going? What would you like to chat about?",
        "how are you": "I'm doing great! Thanks for asking. How can I assist you?",
        "what is your name": "I'm ChatBot, your AI assistant. What would you like to know?",
        "who are you": "I'm an AI chatbot created to help answer your questions and have conversations!",
        "what can you do": "I can chat with you, answer basic questions, and help with simple tasks. What would you like to explore?",
        "bye": "Goodbye! Have a great day!",
        "goodbye": "See you later! Thanks for chatting with me!",
        "thanks": "You're welcome! Is there anything else I can help you with?",
        "thank you": "My pleasure! Feel free to ask me anything else.",
        "help": "I'm here to help! You can ask me questions, have a conversation, or just chat about anything you'd like.",
        "about": "I'm a simple ChatGPT-like chatbot demo. I can respond to basic questions and maintain our conversation history!",
        "weather": "I don't have access to real-time weather data, but you can check your local weather forecast online!",
        "time": f"I don't have access to real-time data, but you sent this message at {datetime.datetime.now().strftime('%H:%M:%S')}",
        "date": f"Today's date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
        "how old are you": "I'm an AI, so I don't have an age in the traditional sense. I exist to help and chat with you!",
        "where are you from": "I exist in the digital realm, running on servers to help users like you!",
        "good morning": "Good morning! Hope you're having a great start to your day. How can I help?",
        "good afternoon": "Good afternoon! What brings you here today?",
        "good evening": "Good evening! How has your day been?",
        "good night": "Good night! Sleep well and have sweet dreams!",
        "how do you work": "I work by processing your text input and responding with pre-programmed responses. I'm a simple chatbot demo!",
        "are you real": "I'm a computer program designed to chat with you. I'm not human, but I'm here to help!",
        "tell me a joke": "Why don't scientists trust atoms? Because they make up everything! 😄",
        "what's your favorite color": "I don't see colors, but if I could, I think I'd like blue - it seems calm and trustworthy!",
        "do you like music": "I can't hear music, but I understand it brings joy to many people! What's your favorite genre?",
        "tell me about yourself": "I'm a friendly chatbot created to demonstrate basic conversational AI. I love chatting with users like you!",
    }
    
    user_lower = user_message.lower().strip()
    
    # Check for exact matches first
    if user_lower in responses:
        return responses[user_lower]
    
    # Check for partial matches
    for key, value in responses.items():
        if key in user_lower:
            return value
    
    # Handle questions
    if user_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
        return f"That's an interesting question about '{user_message}'. I'm a simple demo chatbot, so I might not have all the answers, but I'm happy to chat about it!"
    
    # Handle longer statements
    if len(user_message.split()) > 5:
        return f"Thanks for sharing that with me! You mentioned something about '{user_message[:50]}...' - I'm a simple chatbot, but I find our conversation interesting. What else would you like to talk about?"
    
    # Default response
    return f"I understand you said: '{user_message}'. I'm a simple chatbot demo, but I'm here to chat! Try asking me 'hello', 'how are you', 'what can you do', or tell me a joke!"

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Generate simple bot response (NO API calls)
        bot_response = generate_bot_response(user_message)
        
        # Save to database
        save_to_database(user_message, bot_response)
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/history')
def history():
    """Get chat history"""
    try:
        chat_history = get_chat_history()
        return jsonify([{
            'user_message': msg[0],
            'bot_response': msg[1],
            'timestamp': msg[2]
        } for msg in chat_history])
    except Exception as e:
        return jsonify({'error': f'Error retrieving history: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        clear_chat_history()
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Count messages in database
        conn = sqlite3.connect('chat_history.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM messages')
        message_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'environment': 'local',
            'database': 'SQLite',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'messages_stored': message_count
        })
    except Exception as e:
        return jsonify({'error': f'Health check failed: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting ChatGPT Clone (Simple Version - No API integrations)")
    print("💾 Using SQLite database for local storage")
    print("🌐 Access your app at: http://localhost:5000")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)