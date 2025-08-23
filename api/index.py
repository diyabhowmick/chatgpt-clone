from flask import Flask, render_template, request, jsonify
import datetime
import os

# Create Flask app with template folder pointing to the templates directory
app = Flask(__name__, template_folder='../templates')

# Global variable for in-memory chat storage
chat_history = []

def save_to_memory(user_message, bot_response):
    """Save chat message to in-memory storage (no database)"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat_history.append({
        'user_message': user_message,
        'bot_response': bot_response,
        'timestamp': timestamp
    })

def get_chat_history():
    """Get all chat history from memory (no database)"""
    return chat_history

def clear_chat_history():
    """Clear all chat history from memory (no database)"""
    global chat_history
    chat_history = []

def generate_bot_response(user_message):
    """Generate bot response without any external APIs"""
    
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
        "date": f"Today's date when you sent this message: {datetime.datetime.now().strftime('%Y-%m-%d')}",
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
    """Handle chat messages - NO DATABASE, only memory storage"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Generate bot response (no external API calls)
        bot_response = generate_bot_response(user_message)
        
        # Save to memory only (NO DATABASE)
        save_to_memory(user_message, bot_response)
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/history')
def history():
    """Get chat history from memory (NO DATABASE)"""
    try:
        history_data = get_chat_history()
        return jsonify(history_data)
    except Exception as e:
        return jsonify({'error': f'Error retrieving history: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear chat history from memory (NO DATABASE)"""
    try:
        clear_chat_history()
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel-serverless',
        'storage': 'in-memory-only',
        'database': 'none',
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'messages_stored': len(chat_history)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500