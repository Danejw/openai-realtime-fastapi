# conversation_history.py
import asyncio
import os
import json
import logging
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from supabase import create_client, Client
from dotenv import load_dotenv
from agents import Agent, Runner


# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize the Supabase client (synchronous)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

def get_or_create_conversation_history(user_id: str) -> list:
    """
    Retrieves the conversation history for the given user_id.
    
    Returns a list of messages (each message is a string).
    If no record exists, creates a new record with an empty history and returns an empty list.
    """
    try:
        response = supabase.table("conversation_history").select("history").eq("user_id", user_id).execute()
        data = response.data
        
        if data and len(data) > 0:
            logging.info(f"Retrieved history for user {user_id}: {data[0]['history']}")
            return data[0]["history"]
        else:
            logging.info(f"No conversation history found for user {user_id}. Creating new record.")
            # Insert a new record with an empty history for the user
            insert_response = supabase.table("conversation_history").insert({
                "user_id": user_id,
                "history": []
            }).execute()
            logging.info(f"New conversation history record created for user {user_id}.")
            return []
    except Exception as e:
        logging.error(f"Error retrieving conversation history for user {user_id}: {e}")
        return []

def update_conversation_history(user_id: str, history: list):
    """
    Updates the conversation history for the given user_id.
    """
    try:
        response = supabase.table("conversation_history").update({"history": history}).eq("user_id", user_id).execute()
        logging.info(f"Updated conversation history for user {user_id}.")
    except Exception as e:
        logging.error(f"Error updating conversation history for user {user_id}: {e}")

def append_message_to_history(user_id: str, role: str, message: str) -> list:
    """
    Appends a new message to the conversation history and updates the record.
    Returns the updated history.
    """
    # Retrieve the current history.
    history = get_or_create_conversation_history(user_id)
    new_message = f"{role}: {message}"
    history.append(new_message)
    update_conversation_history(user_id, history)
    return history

def clear_conversation_history(user_id: str):
    """
    Clears the conversation history for the given user_id.
    """
    try:
        response = supabase.table("conversation_history").update({"history": []}).eq("user_id", user_id).execute()
        logging.info(f"Cleared conversation history for user {user_id}.")
    except Exception as e:
        logging.error(f"Error clearing conversation history for user {user_id}: {e}")

async def replace_conversation_history_with_summary(user_id: str):
    """
    Extracts knowledge from the conversation history, runs MBTI and OCEAN analyses
    Replaces the conversation history with a summary.
    The summary is stored as a single message in the history.
    """
    try:
        history = get_or_create_conversation_history(user_id)
        history_string = "\n".join(history)
        
        # Extract knowledge from the history.
        extraction = KnowledgeExtractionService(user_id)
        extract_task = asyncio.create_task(extraction.extract_knowledge(history_string))
        await extract_task

        # Run MBTI analysis
        mbti_service = MBTIAnalysisService(user_id)
        mbti_task = asyncio.create_task(mbti_service.analyze_message(history_string))
        await mbti_task

        # Run OCEAN analysi
        ocean_service = OceanAnalysisService(user_id)
        ocean_task = asyncio.create_task(ocean_service.analyze_message(history_string))
        await ocean_task
    
        # Define instructions for the summarization agent.
        instructions = (
            "You are an AI that summarizes a conversation. "
            "Read the conversation below and provide a concise summary that captures the key points. "
            "Keep it brief and to the point."
        )

        # Create the summarization agent.
        summarization_agent = Agent(
            name="Summarizer",
            handoff_description="An agent that summarizes conversation context.",
            instructions=instructions,
            model="gpt-4o-mini",
        )

        # Construct the prompt with the conversation history.
        prompt = f"Conversation:\n{history}\n\n"
        
        # Run the agent.
        summary_result = await Runner.run(summarization_agent, prompt)
        summary = summary_result.final_output.strip()
        
        # wrap summary in a list.
        summary = [f"Summary: {summary}"]

        # Clear the existing conversation and store only the summary.
        update_conversation_history(user_id, summary)

        logging.info(f"Replaced conversation history with summary for user {user_id}.")
        return summary
    except Exception as e:
        logging.error(f"Error replacing conversation history for user {user_id}: {e}")
