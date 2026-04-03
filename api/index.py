from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import json
import re
from datetime import datetime

# Add parent directory to path so we can import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your modules
from knowledge_base import KnowledgeBase
from search_engine import SearchEngine

# Try to import Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini AI not available")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ============================================
# CONFIGURATION
# ============================================

# Get API key from environment variable (set in Vercel dashboard)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("API_KEY", ""))

# Configure Gemini if key is available
model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini AI configured")
    except Exception as e:
        print(f"❌ Gemini config error: {e}")

# ============================================
# KNOWLEDGE BASE SETUP
# ============================================

knowledge_base = None
search_engine = None

def initialize_system():
    """Initialize the knowledge base and search engine"""
    global knowledge_base, search_engine
    
    print("=" * 50)
    print("Initializing AriseWebX Knowledge System")
    print("=" * 50)
    
    try:
        knowledge_base = KnowledgeBase()
        
        # Try different paths for the data file
        data_paths = [
            "arisewebx_scraped_data.json",
            "/var/task/arisewebx_scraped_data.json",
            os.path.join(os.path.dirname(__file__), "../arisewebx_scraped_data.json"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "arisewebx_scraped_data.json")
        ]
        
        data_loaded = False
        for path in data_paths:
            if os.path.exists(path):
                print(f"✅ Found data file at: {path}")
                # Manually load the data
                with open(path, 'r', encoding='utf-8') as f:
                    knowledge_base.raw_data = json.load(f)
                data_loaded = True
                break
        
        if data_loaded:
            # Build knowledge base
            knowledge_base.build_knowledge_graph()
            knowledge_base.create_text_chunks()
            knowledge_base.build_inverted_index()
            search_engine = SearchEngine(knowledge_base)
            print(f"✅ Knowledge loaded: {len(knowledge_base.chunks)} chunks")
            return True
        else:
            print("❌ Could not find arisewebx_scraped_data.json")
            # Create fallback responses
            create_fallback_knowledge()
            return True
            
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        create_fallback_knowledge()
        return True

def create_fallback_knowledge():
    """Create fallback knowledge if JSON file not found"""
    global knowledge_base, search_engine
    
    print("Creating fallback knowledge base...")
    
    # Create a simple knowledge base with known data
    class SimpleKnowledge:
        def __init__(self):
            self.chunks = []
            self.index = {}
        
        def build_knowledge_graph(self):
            pass
        
        def create_text_chunks(self):
            # Add social media chunks
            self.chunks.append({
                "id": "social_1",
                "content": "Instagram: https://instagram.com/arisewebx",
                "metadata": {"type": "social"},
                "keywords": ["instagram", "social"]
            })
            self.chunks.append({
                "id": "social_2", 
                "content": "LinkedIn: https://linkedin.com/company/arisewebx",
                "metadata": {"type": "social"},
                "keywords": ["linkedin", "social"]
            })
            self.chunks.append({
                "id": "social_3",
                "content": "Twitter: https://twitter.com/arisewebx", 
                "metadata": {"type": "social"},
                "keywords": ["twitter", "social"]
            })
            self.chunks.append({
                "id": "contact_1",
                "content": "Email: arisewebx@gmail.com",
                "metadata": {"type": "contact"},
                "keywords": ["email", "contact"]
            })
        
        def build_inverted_index(self):
            pass
    
    class SimpleSearch:
        def __init__(self, kb):
            self.kb = kb
        
        def answer_question(self, query):
            q_lower = query.lower()
            if 'instagram' in q_lower:
                return {"answer": "📸 Instagram: https://instagram.com/arisewebx"}
            elif 'linkedin' in q_lower:
                return {"answer": "🔗 LinkedIn: https://linkedin.com/company/arisewebx"}
            elif 'twitter' in q_lower:
                return {"answer": "🐦 Twitter: https://twitter.com/arisewebx"}
            elif 'email' in q_lower or 'contact' in q_lower:
                return {"answer": "📧 Email: arisewebx@gmail.com"}
            else:
                return {"answer": "I can help with AriseWebX's social media (Instagram, LinkedIn, Twitter) and contact information. What would you like to know?"}
        
        def hybrid_search(self, query, top_k=3):
            return []
    
    knowledge_base = SimpleKnowledge()
    knowledge_base.create_text_chunks()
    search_engine = SimpleSearch(knowledge_base)
    print(f"✅ Fallback knowledge created with {len(knowledge_base.chunks)} chunks")

# ============================================
# CONVERSATION HANDLERS
# ============================================

def is_greeting(message: str) -> bool:
    greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
    msg_lower = message.lower().strip()
    return any(msg_lower == g or msg_lower.startswith(g) for g in greetings)

def is_farewell(message: str) -> bool:
    farewells = ['bye', 'goodbye', 'see you', 'farewell', 'cya', 'take care', 'later']
    msg_lower = message.lower().strip()
    return any(f in msg_lower for f in farewells)

def is_thanks(message: str) -> bool:
    thanks = ['thanks', 'thank you', 'thx', 'appreciate', 'awesome', 'great']
    msg_lower = message.lower().strip()
    return any(t in msg_lower for t in thanks)

def is_how_are_you(message: str) -> bool:
    patterns = ['how are you', 'how are you doing', 'how\'s it going']
    msg_lower = message.lower().strip()
    return any(p in msg_lower for p in patterns)

def get_conversation_response(message: str) -> str:
    if is_greeting(message):
        return "👋 Hello! I'm AriseWebX's AI assistant. How can I help you today?"
    elif is_farewell(message):
        return "👋 Goodbye! Feel free to come back if you have more questions. Have a great day!"
    elif is_thanks(message):
        return "🎉 You're very welcome! I'm glad I could help!"
    elif is_how_are_you(message):
        return "🤖 I'm doing great, thank you for asking! How can I help you today?"
    return None

# ============================================
# AI RESPONSE FUNCTION
# ============================================

def get_ai_response(user_query: str, context: str) -> str:
    """Get response from Gemini AI"""
    if not model:
        return None
    
    try:
        system_prompt = f"""You are AriseWebX's AI assistant. Use this context:
        {context}
        
        User: {user_query}
        Answer concisely and helpfully:"""
        
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "knowledge_loaded": knowledge_base is not None,
        "chunks_count": len(knowledge_base.chunks) if knowledge_base else 0,
        "ai_enabled": model is not None,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON provided"}), 400
        
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Check for conversation patterns
        conversation_response = get_conversation_response(user_message)
        if conversation_response:
            return jsonify({
                "response": conversation_response,
                "type": "conversation",
                "timestamp": datetime.now().isoformat()
            })
        
        # Get response from knowledge base
        response_text = "I'm here to help with AriseWebX. Ask me about our social media (Instagram, LinkedIn, Twitter) or contact info!"
        
        if search_engine:
            try:
                answer = search_engine.answer_question(user_message)
                response_text = answer.get('answer', response_text)
            except Exception as e:
                print(f"Search error: {e}")
        
        # Try AI enhancement if available
        if model and search_engine and knowledge_base and knowledge_base.chunks:
            try:
                context = ""
                for chunk in knowledge_base.chunks[:3]:
                    context += chunk['content'] + "\n"
                
                ai_response = get_ai_response(user_message, context)
                if ai_response:
                    response_text = ai_response
            except Exception as e:
                print(f"AI enhancement error: {e}")
        
        return jsonify({
            "response": response_text,
            "type": "ai_assisted",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "AriseWebX API is running on Vercel",
        "endpoints": {
            "chat": "POST /chat - Send {'message': 'your question'}",
            "health": "GET /health - Check API status"
        },
        "knowledge_loaded": knowledge_base is not None,
        "ai_enabled": model is not None
    })

# ============================================
# INITIALIZE SYSTEM (THIS RUNS ON DEPLOYMENT)
# ============================================
print("Starting AriseWebX API on Vercel...")
initialize_system()
print("API ready!")

# Export for Vercel
app = app