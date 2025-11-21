import os
from openai import OpenAI
# Import the calendar functions from the file we created
from calendar_service import get_calendar_service, find_open_slots 

# 1. SETUP: Connect to the "Brain"
# 🚨 PASTE YOUR API KEY HERE, inside the quotes.
client = OpenAI()

# NEW: Initialize the Google Calendar connection once at the start
try:
    calendar_service = get_calendar_service() 
    print("Calendar Service Initialized.")
except Exception as e:
    # If the token is missing or expired, this will prompt a re-login
    print(f"Error initializing calendar: {e}")
    # If initialization fails, the find_open_slots function will be unusable

# 2. THE "AGENT INSTRUCTIONS" (System Prompt)
system_instruction = """
You are 'Lexi', an automated intake assistant for 'Miller Family Law'.
Your goal is to qualify potential clients for a consultation.

RULES & BEHAVIOR:
1. DISCLAIMER: In your FIRST response, you must state: "I am an AI assistant. I cannot provide legal advice."
2. CONFLICT CHECK: Before confirming a booking, you MUST ask for the name of the opposing party (the person they are having a dispute with) to check for conflicts.
3. QUALIFICATION: We ONLY handle Family Law (Divorce, Custody). If they ask about traffic tickets or criminal law, politely refer them to the local bar association and end the chat.
4. TONE: Professional, empathetic, but concise. Do not be overly chatty.
5. BOOKING: If they are qualified (Family Law) and provide the opposing party's name, you will state: "Thank you. I have checked attorney Miller's calendar and can offer you the following open slots: [SLOTS HERE]."
"""

# 3. MEMORY INITIALIZATION
messages = [
    {"role": "system", "content": system_instruction}
]

print("--- Legal Agent 'Lexi' Started (Type 'quit' to stop) ---")

# 4. THE ACTION LOOP
while True:
    user_input = input("\nClient: ")
    
    if user_input.lower() in ["quit", "exit"]:
        break

    messages.append({"role": "user", "content": user_input})

    # REASON & DECIDE: Send history to AI to generate a response
    completion = client.chat.completions.create(
        model="gpt-4o", 
        messages=messages
    )
    
    bot_response = completion.choices[0].message.content

    # NEW LOGIC: Check if Lexi is ready to book an appointment (looking for the trigger phrase)
    if "offer you the following open slots" in bot_response:
        
        # Call the real calendar tool to fetch availability
        available_slots = find_open_slots(calendar_service)
        
        # Format the slots for insertion
        slot_text = "\n* " + "\n* ".join(available_slots) 
        
        # Replace the placeholder in the AI's response with the real times
        bot_response = bot_response.replace("[SLOTS HERE]", slot_text)

    # ACT: Display the final response
    print(f"Lexi: {bot_response}")

    # Add agent response to memory
    messages.append({"role": "assistant", "content": bot_response})