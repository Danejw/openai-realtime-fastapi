import json
import os
from supabase import create_client, AsyncClient
from dotenv import load_dotenv
from openai import OpenAI
import logging
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


async def generate_embedding(text):
    """
    Converts text into an embedding vector using OpenAI's latest embedding model.
    """
    try:
        response =  await client.embeddings.create(
            model="text-embedding-ada-002",  # Use the latest embedding model
            input=text
        )
        embedding = response.data[0].embedding
        logging.info(f"Embedding generated: {embedding}")
        return embedding
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None


async def store_user_knowledge(user_id: str, knowledge_text: str, metadata: dict):
    """
    Stores extracted knowledge in the vector database with safety checks.
    """
    embedding = await generate_embedding(knowledge_text)
    
    logging.info(f"Embedding generated: {embedding}")   

    # Check if knowledge already exists to prevent duplicates
    existing = supabase.table("user_knowledge").select("*").eq("user_id", user_id).eq("knowledge_text", knowledge_text).execute()

    if existing.data:
        # Increase mention count and update timestamp
        new_count = existing.data[0]["mention_count"] + 1
        supabase.table("user_knowledge").update({
            "metadata": json.dumps(metadata),
            "last_updated": "now()",
            "mention_count": new_count
        }).eq("id", existing.data[0]["id"]).execute()
        print("Updated existing knowledge entry.")
    else:
        # Insert new knowledge
        supabase.table("user_knowledge").insert({
            "user_id": user_id,
            "knowledge_text": knowledge_text,
            "embedding": embedding,
            "metadata": json.dumps(metadata),
            "mention_count": 1
        }).execute()

async def find_similar_knowledge(user_id: str, query: str, top_k=5):
    """
    Finds the most relevant knowledge for a user based on a query.
    """
    query_embedding = await generate_embedding(query)

    # Ensure the user has stored knowledge before searching
    existing = supabase.table("user_knowledge").select("*").eq("user_id", user_id).execute()

    if not existing.data:
        return {"message": "No knowledge stored for this user."}

    response = supabase.rpc("find_similar_knowledge", {
        "user_id": user_id,
        "embedding": query_embedding,
        "top_k": top_k
    }).execute()

    return response.data if response.data else {"message": "No similar knowledge found."}


