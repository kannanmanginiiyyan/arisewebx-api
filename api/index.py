from flask import Flask, request, jsonify
from flask_cors import CORS
from knowledge_base import KnowledgeBase
from search_engine import SearchEngine
from datetime import datetime
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ============================================
# AI CONFIGURATION (Free Gemini API)
# ============================================

GEMINI_API_KEY = os.getenv("API_KEY")  # Replace with your actual key

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ============================================
# KNOWLEDGE BASE SETUP
# ============================================

knowledge_base = None
search_engine = None

def initialize_system():
    """Initialize the knowledge base and search engine"""
    global knowledge_base, search_engine
    
    print("=" * 60)
    print("Initializing AriseWebX AI Knowledge System")
    print("=" * 60)
    
    knowledge_base = KnowledgeBase()
    
    # Try to load existing knowledge base
    if not knowledge_base.load_knowledge():
        print("No existing knowledge base found. Building from scraped data...")
        if knowledge_base.load_data():
            knowledge_base.build_knowledge_graph()
            knowledge_base.create_text_chunks()
            knowledge_base.build_inverted_index()
            knowledge_base.save_knowledge()
        else:
            print("❌ Cannot initialize: No data available")
            return False
    
    search_engine = SearchEngine(knowledge_base)
    print("✅ System initialized successfully")
    return True

# ============================================
# CONVERSATION HANDLER
# ============================================

def is_greeting(message: str) -> bool:
    """Check if message is a greeting"""
    greetings = [
        'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 
        'good evening', 'hi there', 'hello there', 'sup', 'howdy', 'yo'
    ]
    msg_lower = message.lower().strip()
    return any(msg_lower == g or msg_lower.startswith(g) for g in greetings)

def is_farewell(message: str) -> bool:
    """Check if message is a farewell"""
    farewells = [
        'bye', 'goodbye', 'see you', 'see ya', 'farewell', 'cya', 
        'take care', 'later', 'bye bye', 'talk later'
    ]
    msg_lower = message.lower().strip()
    return any(f in msg_lower for f in farewells)

def is_thanks(message: str) -> bool:
    """Check if message is thanking"""
    thanks = [
        'thanks', 'thank you', 'thx', 'appreciate', 'thank', 'awesome', 
        'great', 'perfect', 'nice', 'cool', 'good to know'
    ]
    msg_lower = message.lower().strip()
    return any(t in msg_lower for t in thanks)

def is_how_are_you(message: str) -> bool:
    """Check if asking 'how are you'"""
    patterns = [
        'how are you', 'how are you doing', 'how\'s it going', 
        'how is it going', 'how are things', 'you alright'
    ]
    msg_lower = message.lower().strip()
    return any(p in msg_lower for p in patterns)

def is_about_agent(message: str) -> bool:
    """Check if asking about the AI assistant itself"""
    patterns = [
        'who are you', 'what are you', 'your name', 'you are', 
        'are you ai', 'are you bot', 'what can you do'
    ]
    msg_lower = message.lower().strip()
    return any(p in msg_lower for p in patterns)

def get_conversation_response(message: str) -> str:
    """Get response for general conversation"""
    if is_greeting(message):
        return "👋 Hello! I'm AriseWebX's AI assistant. How can I help you today? You can ask me about our services, social media, contact information, or anything about AriseWebX!"
    
    elif is_farewell(message):
        return "👋 Goodbye! Feel free to come back if you have more questions about AriseWebX. Have a great day!"
    
    elif is_thanks(message):
        return "🎉 You're very welcome! I'm glad I could help. Is there anything else you'd like to know about AriseWebX?"
    
    elif is_how_are_you(message):
        return "🤖 I'm doing great, thank you for asking! I'm here 24/7 to help you with any questions about AriseWebX. What can I assist you with today?"
    
    elif is_about_agent(message):
        return "✨ I'm AriseWebX's AI-powered virtual assistant! I'm here to help answer questions about:\n\n• 📸 Social media links (Instagram, LinkedIn, Twitter)\n• 📧 Contact information and email\n• 💼 Services we offer\n• 🏢 Company information\n\nI use Google's Gemini AI to provide natural, helpful responses. What would you like to know about AriseWebX?"
    
    return None

# ============================================
# AI CHAT FUNCTION
# ============================================

def get_ai_response(user_query: str, context: str) -> str:
    """
    Get response from Gemini AI with context from knowledge base
    """
    try:
        # Create system prompt with knowledge base context and personality
        system_prompt = f"""You are AriseWebX's friendly, professional AI assistant. Use the following context from their website to answer questions. 
        Be warm, helpful, and conversational. 

        YOUR PERSONALITY:
        - Friendly and professional
        - Enthusiastic about helping
        - Concise but informative
        - Use emojis occasionally to be friendly (👋, 🎉, ✨, 📸, 💼, 📧)
        - If someone says "hi", "hello", or greets you, greet them back warmly
        - If someone thanks you, acknowledge it politely
        - If someone asks "how are you", say you're doing great and ask how you can help

        CONTEXT FROM ARISEWEBX WEBSITE:
        {context}

        IMPORTANT RULES:
        1. For business questions (services, contact, social media), answer based on the context
        2. For general conversation (hi, bye, thanks, how are you), respond naturally and friendly
        3. Always be helpful and represent AriseWebX positively
        4. Keep responses conversational and engaging
        5. If you don't know something, say "I don't have that information yet. Would you like to contact AriseWebX directly at arisewebx@gmail.com?"
        
        User Message: {user_query}
        
        Your response:"""
        
        # Call Gemini API
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
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "ai_enabled": True,
        "model": "gemini-1.5-flash",
        "knowledge_loaded": knowledge_base is not None,
        "chunks_count": len(knowledge_base.chunks) if knowledge_base else 0
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Main chat endpoint with AI integration and conversation handling"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        print(f"\n📝 User: {user_message}")
        
        # Step 1: Check for conversation patterns first
        conversation_response = get_conversation_response(user_message)
        
        if conversation_response:
            # It's a conversation message, no need to search knowledge base
            print(f"🤖 Bot: {conversation_response[:50]}...")
            return jsonify({
                "response": conversation_response,
                "context_used": False,
                "type": "conversation",
                "sources": [],
                "timestamp": datetime.now().isoformat()
            })
        
        # Step 2: Search knowledge base for business-related questions
        search_results = search_engine.hybrid_search(user_message, top_k=3)
        
        # Build context from search results
        context = ""
        if search_results:
            context = "=== RELEVANT INFORMATION FROM ARISEWEBX ===\n"
            for i, result in enumerate(search_results, 1):
                context += f"\n{i}. {result['chunk']['content']}\n"
                context += f"   Type: {result['chunk']['metadata'].get('type', 'general')}\n"
        else:
            # No results found, provide basic context
            context = "No specific information found in the knowledge base. The user is asking about AriseWebX."
        
        # Step 3: Get AI response with context
        ai_response = get_ai_response(user_message, context)
        
        # Step 4: Fallback to knowledge base if AI fails
        if not ai_response:
            answer = search_engine.answer_question(user_message)
            ai_response = answer['answer']
        
        print(f"🤖 AI: {ai_response[:100]}...")
        
        return jsonify({
            "response": ai_response,
            "context_used": len(search_results) > 0,
            "type": "ai_assisted",
            "sources": [r['chunk']['metadata'] for r in search_results[:2]] if search_results else [],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    """Legacy question answering endpoint (without AI)"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.json
        query = data.get('question', '')
        
        if not query:
            return jsonify({"error": "Question is required"}), 400
        
        # First check conversation patterns
        conversation_response = get_conversation_response(query)
        if conversation_response:
            return jsonify({
                "question": query,
                "answer": conversation_response,
                "confidence": 1.0,
                "sources": [],
                "timestamp": datetime.now().isoformat()
            })
        
        # Otherwise use search engine
        answer = search_engine.answer_question(query)
        
        return jsonify({
            "question": query,
            "answer": answer['answer'],
            "confidence": answer['confidence'],
            "sources": answer['sources'],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST', 'OPTIONS'])
def search():
    """Search endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        query = data.get('query', '')
        search_type = data.get('type', 'hybrid')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        print(f"Searching for: {query}")
        
        if search_type == 'keyword':
            results = search_engine.keyword_search(query, top_k)
        elif search_type == 'semantic':
            results = search_engine.semantic_search(query, top_k)
        else:
            results = search_engine.hybrid_search(query, top_k)
        
        formatted_results = []
        for r in results:
            try:
                chunk = r.get('chunk', {})
                content = chunk.get('content', 'No content')
                metadata = chunk.get('metadata', {})
                score = r.get('score', r.get('final_score', 0))
                
                formatted_results.append({
                    "content": str(content)[:500],
                    "type": str(metadata.get('type', 'unknown')),
                    "score": float(score) if isinstance(score, (int, float)) else 0.0,
                    "url": str(metadata.get('url', 'unknown'))
                })
            except Exception as e:
                print(f"Error formatting result: {e}")
                continue
        
        return jsonify({
            "query": query,
            "search_type": search_type,
            "results": formatted_results,
            "total_results": len(formatted_results)
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get search statistics"""
    if not search_engine:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        return jsonify(search_engine.get_search_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/knowledge/summary', methods=['GET'])
def knowledge_summary():
    """Get knowledge base summary"""
    if not knowledge_base:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        summary = {
            "total_chunks": len(knowledge_base.chunks),
            "total_entities": sum(len(kg['entities']) for kg in knowledge_base.knowledge_graph.values()),
            "chunk_types": {},
            "urls": list(knowledge_base.raw_data.keys()) if knowledge_base.raw_data else []
        }
        
        for chunk in knowledge_base.chunks:
            chunk_type = chunk['metadata'].get('type', 'unknown')
            summary['chunk_types'][chunk_type] = summary['chunk_types'].get(chunk_type, 0) + 1
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "AriseWebX AI Knowledge API is running",
        "ai_model": "Google Gemini 1.5 Flash (Free)",
        "conversation_support": "✅ Yes - Handles greetings, farewells, thanks, and how are you",
        "endpoints": {
            "chat": "POST /chat - AI-powered chat with conversation support",
            "ask": "POST /ask - Question answering (no AI)",
            "search": "POST /search - Search knowledge base",
            "health": "GET /health - Health check",
            "stats": "GET /stats - Statistics",
            "summary": "GET /knowledge/summary - Knowledge summary"
        },
        "example_messages": [
            "Hi",
            "How are you?",
            "Thanks!",
            "Bye",
            "Who are you?",
            "What is your Instagram?",
            "How can I contact you?"
        ],
        "free_ai_limits": "20-250 requests/day with Gemini free tier",
        "port": 5001
    })

if __name__ == '__main__':
    if initialize_system():
        print("\n" + "=" * 60)
        print("🚀 AriseWebX AI System Ready!")
        print("=" * 60)
        print("\n📊 System Info:")
        print(f"   - Knowledge chunks: {len(knowledge_base.chunks)}")
        print(f"   - AI Model: Gemini 1.5 Flash (FREE)")
        print(f"   - Conversation Support: ✅ Yes")
        print(f"   - Daily limit: 20-250 requests (free tier)")
        print("\n💬 Conversation Examples:")
        print("   - 'Hi' → Warm greeting")
        print("   - 'How are you?' → Friendly response")
        print("   - 'Thanks!' → Acknowledgment")
        print("   - 'Bye' → Farewell")
        print("   - 'Who are you?' → Introduction")
        print("\n📍 Available Endpoints:")
        print("   POST /chat  - AI-powered chat (recommended)")
        print("   POST /ask   - Basic Q&A (no AI)")
        print("   POST /search - Search knowledge base")
        print("   GET  /health - Health check")
        print("\n🌐 Server running on http://localhost:5001")
        print("💡 Try saying: 'Hi', 'How are you?', or 'Thanks!'")
        print("=" * 60 + "\n")
        app.run(debug=False, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to initialize system. Please run scraper first.")