from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import os

app = Flask(__name__)

# Database setup
def init_db():
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
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_message, bot_response)
        VALUES (?, ?)
    ''', (user_message, bot_response))
    conn.commit()
    conn.close()

def get_chat_history():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_message, bot_response, timestamp FROM messages ORDER BY timestamp')
    history = cursor.fetchall()
    conn.close()
    return history

# Enhanced bot response generator with intelligent responses
def generate_bot_response(user_message):
    import re
    
    user_lower = user_message.lower().strip()
    
    # Greetings
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greeting in user_lower for greeting in greetings):
        return "Hello! I'm your AI assistant. I'm here to help answer your questions, provide information, and have meaningful conversations. What would you like to know about?"
    
    # Farewell
    farewells = ['bye', 'goodbye', 'see you', 'farewell', 'talk to you later']
    if any(farewell in user_lower for farewell in farewells):
        return "Goodbye! It was great chatting with you. Feel free to come back anytime if you have more questions. Have a wonderful day!"
    
    # Identity questions
    if any(phrase in user_lower for phrase in ['what is your name', 'who are you', 'what are you']):
        return "I'm an AI assistant designed to help answer questions and have conversations. I can discuss a wide variety of topics including science, history, technology, arts, and much more. How can I assist you today?"
    
    # How are you
    if 'how are you' in user_lower:
        return "I'm doing well, thank you for asking! I'm here and ready to help with any questions or topics you'd like to explore. What's on your mind today?"
    
    # World War 2
    if any(phrase in user_lower for phrase in ['world war 2', 'world war ii', 'ww2', 'wwii', 'second world war']):
        return """World War II (1939-1945) was the largest and deadliest conflict in human history. Here are key points:

**Timeline & Participants:**
- Started September 1, 1939 when Germany invaded Poland
- Main Axis powers: Germany, Italy, Japan
- Main Allied powers: Britain, Soviet Union, United States, China

**Major Events:**
- Holocaust: Systematic genocide of 6 million Jews and millions of others
- Pearl Harbor (Dec 7, 1941): Japan's surprise attack brought US into war
- D-Day (June 6, 1944): Allied invasion of Normandy, France
- Atomic bombs dropped on Hiroshima and Nagasaki (August 1945)

**Impact:**
- 70-85 million deaths worldwide
- Led to creation of United Nations
- Beginning of Cold War between US and Soviet Union
- Massive technological and social changes

Would you like me to elaborate on any specific aspect of WWII?"""
    
    # Science topics
    if any(word in user_lower for word in ['science', 'physics', 'chemistry', 'biology', 'astronomy']):
        return "Science is fascinating! I'd be happy to discuss scientific topics with you. Whether you're interested in physics (like quantum mechanics or relativity), chemistry (molecular structures, reactions), biology (evolution, genetics), astronomy (space, planets, stars), or any other scientific field - just let me know what specifically interests you!"
    
    # Technology
    if any(word in user_lower for word in ['technology', 'computer', 'programming', 'ai', 'artificial intelligence']):
        return "Technology is rapidly evolving and shaping our world! I can discuss topics like programming languages, software development, artificial intelligence, machine learning, computer hardware, emerging technologies, or any specific tech topic you're curious about. What aspect of technology interests you most?"
    
    # Math
    if any(word in user_lower for word in ['math', 'mathematics', 'calculation', 'equation']):
        return "Mathematics is the universal language! I can help with various math topics from basic arithmetic to advanced calculus, statistics, algebra, geometry, and more. I can also solve equations, explain mathematical concepts, or discuss the beauty of mathematical patterns. What math topic would you like to explore?"
    
    # History
    if 'history' in user_lower:
        return "History is full of fascinating stories and lessons! I can discuss ancient civilizations, medieval times, modern history, specific historical events, famous figures, cultural movements, and more. Whether you're interested in a particular time period, region, or type of history, I'm here to help. What historical topic interests you?"
    
    # Help or assistance
    if any(word in user_lower for word in ['help', 'assist', 'support']):
        return "I'm here to help! I can assist you with a wide range of topics including:\n\n• Answering questions on various subjects\n• Explaining complex concepts\n• Providing information and research\n• Creative writing and brainstorming\n• Problem-solving and analysis\n• Educational support\n• General conversation and discussion\n\nWhat specific area would you like help with?"
    
    # Weather (though we don't have real weather data)
    if 'weather' in user_lower:
        return "I don't have access to real-time weather data, but I can discuss weather patterns, climate science, meteorology, or help you understand weather phenomena! For current weather conditions, I'd recommend checking a weather app or website like Weather.com or your local meteorological service."
    
    # Creative topics
    if any(word in user_lower for word in ['story', 'poem', 'creative', 'writing', 'art']):
        return "I love creative topics! I can help with creative writing, storytelling, poetry, discussing art movements, analyzing literature, brainstorming creative projects, or exploring artistic techniques. What type of creative endeavor are you interested in?"
    
    # Default intelligent response
    return f"That's an interesting topic you've brought up! While I try to provide helpful responses on a wide variety of subjects, I'd love to give you a more detailed answer. Could you tell me more specifically what you'd like to know about '{user_message}'? I can discuss topics like science, history, technology, arts, current events, and much more in depth."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Generate bot response
        bot_response = generate_bot_response(user_message)
        
        # Save to database
        save_to_database(user_message, bot_response)
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    try:
        chat_history = get_chat_history()
        return jsonify([{
            'user_message': msg[0],
            'bot_response': msg[1],
            'timestamp': msg[2]
        } for msg in chat_history])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        conn = sqlite3.connect('chat_history.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        conn.commit()
        conn.close()
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)