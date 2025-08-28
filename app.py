from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import os

app = Flask(__name__, template_folder='templates')

# --------------------------
# Database Connection
# --------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")  # set in Vercel env vars

def get_connection():
    """Create a new database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def save_to_database(user_message, bot_response):
    """Insert chat message into Supabase (Postgres)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_message, bot_response) VALUES (%s, %s)",
        (user_message, bot_response)
    )
    conn.commit()
    conn.close()

def get_chat_history():
    """Retrieve all chat history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, bot_response, timestamp FROM messages ORDER BY timestamp")
    history = cursor.fetchall()
    conn.close()
    return history

def clear_chat_history():
    """Delete all messages"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

# --------------------------
# Chatbot Logic
# --------------------------
def generate_bot_response(user_message):
    responses = {
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! What can I do for you?",
        "hey": "Hey! How's it going? What would you like to chat about?",
        "how are you": "I'm doing great! Thanks for asking. How can I assist you?",
        "what is your name": "I'm ChatBot, your AI assistant.",
        "bye": "Goodbye! Have a great day!",
        "thanks": "You're welcome! 😊",
        "help": "I'm here to chat with you. Ask me anything!",
        "about": "I'm a simple ChatGPT-like chatbot demo with persistent history via Supabase!",
    }

    user_lower = user_message.lower().strip()
    if user_lower in responses:
        return responses[user_lower]

    for key, value in responses.items():
        if key in user_lower:
            return value

    if user_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
        return f"That's an interesting question about '{user_message}'. I'm just a demo, but happy to chat!"

    if len(user_message.split()) > 5:
        return f"Thanks for sharing! You mentioned '{user_message[:50]}...' — tell me more!"

    return f"I heard: '{user_message}'. I'm a demo chatbot. Try 'hello', 'help', or 'tell me a joke'!"

# --------------------------
# Routes
# --------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'Empty message'}), 400

        user_message = data['message'].strip()
        bot_response = generate_bot_response(user_message)

        # Save to Supabase
        # save_to_database(user_message, bot_response)

        return jsonify({
            'response': bot_response,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/history')
def history():
    try:
        chat_history = get_chat_history()
        return jsonify(chat_history)
    except Exception as e:
        return jsonify({'error': f'Error retrieving history: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history_route():
    try:
        clear_chat_history()
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500

@app.route('/health')
def health():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()['count']
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'Supabase (Postgres)',
            'messages_stored': count,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': f'Health check failed: {str(e)}'}), 500

# --------------------------
# Run Locally
# --------------------------
if __name__ == '__main__':
    print("🚀 Starting Chatbot with Supabase backend")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
