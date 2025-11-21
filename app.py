import os
from openai import OpenAI
from flask import Flask, request, jsonify 
from flask_cors import CORS 
from calendar_service import get_calendar_service, find_open_slots 

# --- 1. GLOBAL INITIALIZATION ---
# 🚨 PASTE YOUR API KEY HERE
client = OpenAI()

# Initialize Flask app
app = Flask(__name__)
CORS(app) 

# Initialize the Google Calendar connection once globally
try:
    calendar_service = get_calendar_service() 
    print("Calendar Service Initialized.")
except Exception as e:
    print(f"Error initializing calendar: {e}")
    
# --- 2. GLOBAL MEMORY STORE (System Prompt and History) ---
SYSTEM_INSTRUCTION = """
You are 'Lexi', an automated intake assistant for 'Miller Family Law'.
Your goal is to qualify potential clients for a consultation.

RULES & BEHAVIOR:
1. DISCLAIMER: In your FIRST response, you must state: "I am an AI assistant. I cannot provide legal advice."
2. CONFLICT CHECK: Before confirming a booking, you MUST ask for the name of the opposing party (the person they are having a dispute with) to check for conflicts.
3. QUALIFICATION: We ONLY handle Family Law (Divorce, Custody). If they ask about traffic tickets or criminal law, politely refer them to the local bar association and end the chat.
4. TONE: Professional, empathetic, but concise. Do not be overly chatty.
5. BOOKING: If they are qualified (Family Law) and provide the opposing party's name, you will state: "Thank you. I have checked attorney Miller's calendar and can offer you the following open slots: [SLOTS HERE]."
"""

SESSION_HISTORY = {} 

def get_session_messages(session_id):
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]
    return SESSION_HISTORY[session_id]
@app.route('/chat', methods=['POST'])
def chat():
    # 1. Get user message and session ID from the web request
    try:
        data = request.get_json()
        user_input = data.get('message')
        session_id = data.get('session_id', 'default_user') 
    except Exception:
        return jsonify({"error": "Invalid request format"}), 400

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # 2. Get history and add new user message
    messages = get_session_messages(session_id)
    messages.append({"role": "user", "content": user_input})

    # 3. Call the OpenAI API
    completion = client.chat.completions.create(
        model="gpt-4o", 
        messages=messages
    )
    
    bot_response = completion.choices[0].message.content

    # 4. TOOL USE LOGIC: Check for the calendar trigger
    if "offer you the following open slots" in bot_response:
        available_slots = find_open_slots(calendar_service)
        slot_text = "\n* " + "\n* ".join(available_slots) 
        bot_response = bot_response.replace("[SLOTS HERE]", slot_text)

    # 5. Save response to history and send back as JSON
    messages.append({"role": "assistant", "content": bot_response})
    
    return jsonify({"response": bot_response})
if __name__ == '__main__':
    # Run the server locally on port 5000 
    app.run(debug=True, port=5000)