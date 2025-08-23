from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import os
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# In-memory storage for Vercel (since file system is read-only)
chat_storage = []

# Check if we're running on Vercel or locally
def is_vercel_environment():
    return os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None

# Database setup for local development
def init_db():
    if is_vercel_environment():
        # Use in-memory storage for Vercel
        global chat_storage
        chat_storage = []
        print("Using in-memory storage (Vercel environment)")
        return True
    
    try:
        # Use SQLite for local development
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
        conn = sqlite3.connect(db_path)
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
        print("Using SQLite database (local environment)")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def save_to_database(user_message, bot_response):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if is_vercel_environment():
        # Use in-memory storage for Vercel
        try:
            global chat_storage
            chat_storage.append({
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': timestamp
            })
            return True
        except Exception as e:
            print(f"In-memory storage error: {e}")
            return False
    
    try:
        # Use SQLite for local development
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_message, bot_response, timestamp)
            VALUES (?, ?, ?)
        ''', (user_message, bot_response, timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database save error: {e}")
        return False

def get_chat_history():
    if is_vercel_environment():
        # Return in-memory storage for Vercel
        try:
            global chat_storage
            return [(msg['user_message'], msg['bot_response'], msg['timestamp']) for msg in chat_storage]
        except Exception as e:
            print(f"In-memory retrieval error: {e}")
            return []
    
    try:
        # Use SQLite for local development
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_message, bot_response, timestamp FROM messages ORDER BY timestamp')
        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        print(f"Database read error: {e}")
        return []

def clear_chat_history():
    if is_vercel_environment():
        # Clear in-memory storage for Vercel
        try:
            global chat_storage
            chat_storage = []
            return True
        except Exception as e:
            print(f"In-memory clear error: {e}")
            return False
    
    try:
        # Clear SQLite database for local development
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database clear error: {e}")
        return False

# AI-powered bot response generator
def generate_bot_response(user_message):
    # Try Groq API first (since you're using it)
    try:
        return get_groq_response(user_message)
    except Exception as e:
        print(f"Groq API error: {e}")
    
    # Try OpenAI as backup
    try:
        return get_openai_response(user_message)
    except Exception as e:
        print(f"OpenAI API error: {e}")
    
    # Try Hugging Face as backup
    try:
        return get_huggingface_response(user_message)
    except Exception as e:
        print(f"Hugging Face API error: {e}")
    
    # Fallback to local responses
    return get_fallback_response(user_message)

# Groq API Integration (Primary - since you're using this)
def get_groq_response(user_message):
    import requests
    import json
    
    api_key = os.environ.get('GROQ_API_KEY')
    
    if not api_key:
        raise Exception("Groq API key not found in environment variables")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mixtral-8x7b-32768",  # Fast and very capable model
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful, knowledgeable, and friendly AI assistant. Provide accurate, informative, and engaging responses to user questions. Be conversational and helpful."
            },
            {
                "role": "user", 
                "content": user_message
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 1,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            error_details = ""
            try:
                error_info = response.json()
                error_details = f" - {error_info.get('error', {}).get('message', 'Unknown error')}"
            except:
                pass
            raise Exception(f"Groq API returned status {response.status_code}{error_details}")
            
    except requests.exceptions.Timeout:
        raise Exception("Groq API request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON response from Groq API")

# OpenAI Integration (Backup)
def get_openai_response(user_message):
    try:
        import openai
    except ImportError:
        raise Exception("OpenAI library not installed")
    
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        raise Exception("OpenAI API key not configured")
    
    client = openai.OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful, knowledgeable, and friendly AI assistant."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=800,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

# Hugging Face Integration (Free backup)
def get_huggingface_response(user_message):
    import requests
    
    api_key = os.environ.get('HUGGINGFACE_API_KEY')
    
    if not api_key:
        raise Exception("Hugging Face API key not configured")
    
    # Using a different model that's better for general conversation
    url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "inputs": user_message,
        "parameters": {
            "max_length": 200,
            "temperature": 0.8,
            "do_sample": True,
            "pad_token_id": 50256
        }
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            generated = result[0].get('generated_text', '')
            # Clean up the response
            clean_response = generated.replace(user_message, '').strip()
            if clean_response:
                return clean_response
    
    raise Exception(f"Hugging Face API error: {response.status_code}")

# Enhanced fallback responses (if all APIs fail)
def get_fallback_response(user_message):
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
    return f"I appreciate your question about '{user_message}'. While I'm currently running in fallback mode (AI services unavailable), I'd love to help you explore this topic! Could you be more specific about what aspect you'd like to know? I can discuss science, history, technology, arts, current events, and many other subjects in detail."

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
        if clear_chat_history():
            return jsonify({'message': 'Chat history cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear chat history'}), 500
    except Exception as e:
        print(f"Clear history error: {e}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

# Health check endpoint
@app.route('/health')
def health():
    env_type = "Vercel (in-memory)" if is_vercel_environment() else "Local (SQLite)"
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.datetime.now().isoformat(),
        'environment': env_type,
        'storage_type': 'in-memory' if is_vercel_environment() else 'sqlite'
    })

# Initialize database when app starts
if not init_db():
    print("Warning: Database initialization failed")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)