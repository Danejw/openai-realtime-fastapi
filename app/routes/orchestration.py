from http.client import HTTPException
import json
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase import profiles
from app.supabase.profiles import ProfileRepository
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import asyncio
import logging
from app.auth import verify_token
from agents import Agent, Runner, WebSearchTool, FileSearchTool, function_tool, ToolCallItem


router = APIRouter()


class UserInput(BaseModel):
    message: str


profile_repo = ProfileRepository()


def get_user_name(user_id: str) -> str:
    return profile_repo.get_user_name(user_id)

@function_tool
def update_user_name(user_id: str, name: str) -> str:
    """
    Updates the user's name in the profile repository.

    Parameters:
    - user_id (str): The unique identifier of the user.
    - name (str): The new name to update for the user.

    Returns:
    - str: the names of the user
    """ 
    return profile_repo.update_user_name(user_id, name)

@function_tool
async def find_personalized_info_about_user(user_id: str, query: str) -> str:
    """
    Look for personalized information about the user in the knowledge repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    - query (str): The query to find addtional information about the user to personalize the conversation.

    Returns:
    - str: the addtional information about the user
    """

    knowledge_service = KnowledgeExtractionService(user_id)
    try:
        return await knowledge_service.retrieve_similar_knowledge(query)
    except Exception as e:
        logging.error(f"Error retrieving knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/orchestration")
async def orchestrate(user_input: UserInput, user=Depends(verify_token)):
    """
    Orchestrates sentiment analysis, personality assessments (MBTI, OCEAN),
    knowledge extraction, similarity search, and dynamic AI response generation.
    """
    try:
        user_id = user["id"]
        message = user_input.message
        
        logging.info(f"User ID: {user_id}")

        # Run analyses concurrently
        mbti_service = MBTIAnalysisService(user_id)
        mbti_task = asyncio.create_task(mbti_service.analyze_message(message))
        
        ocean_service = OceanAnalysisService(user_id)
        ocean_task = asyncio.create_task(ocean_service.analyze_message(message))

        knowledge_service = KnowledgeExtractionService(user_id)
        knowledge_task = asyncio.create_task(knowledge_service.extract_knowledge(message))

        # Wait for all tasks to complete
        await mbti_task  # MBTI updates asynchronously
        await ocean_task  # OCEAN updates asynchronously
        await knowledge_task
        
        # Retrieve stored MBTI & OCEAN
        mbti_type = mbti_service.get_mbti_type()
        style_prompt = mbti_service.generate_style_prompt(mbti_type)
        ocean_traits = ocean_service.get_personality_traits()
        
        logging.info(f"MBTI Type: {mbti_type, style_prompt}")
        logging.info(f"OCEAN Traits: {ocean_traits}")

        # Run similarity search on extracted knowledge
        similar_knowledge = await knowledge_service.retrieve_similar_knowledge(message, top_k=3)

        # Construct dynamic system prompt
        system_prompt = (
            f"MBTI Type: {mbti_type, style_prompt}.\n"
            f"OCEAN Traits: {ocean_traits}.\n"
            f"Similar Previous Knowledge: {similar_knowledge}."
        )
        
        logging.info(f"System prompt: {system_prompt}")

        # Generate AI response using system prompt
        conversational_agent = Agent(
            name="Wit",
            handoff_description="A conversational response agent given the context.",
            instructions= system_prompt + "\n\n You are a conversational agent. Respond to the user using the information provided.",
            model="gpt-4o-mini",
            tools=[
                WebSearchTool(),
                FileSearchTool()
            ]
        )

        response = await Runner.run(conversational_agent, message)
              
        logging.info(f"Response Object: {response}")  

        return response.final_output

    except Exception as e:
        logging.error(f"Error processing orchestration: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
@router.post("/convo-lead")
async def convo_lead(user_input: UserInput, user=Depends(verify_token)):
    """
    Leads the conversation with the user. Asking questions to get to know the user better.  
    """
    user_id = user["id"]   
    
    # Get the users name
    user_name = get_user_name(user_id)
    
    # Run analyses concurrently
    mbti_service = MBTIAnalysisService(user_id)
    #mbti_task = asyncio.create_task(mbti_service.analyze_message(message))
    
    ocean_service = OceanAnalysisService(user_id)
    #ocean_task = asyncio.create_task(ocean_service.analyze_message(message))

    knowledge_service = KnowledgeExtractionService(user_id)
    #knowledge_task = asyncio.create_task(knowledge_service.extract_knowledge(message))

    # Wait for all tasks to complete
    # await mbti_task  # MBTI updates asynchronously
    # await ocean_task  # OCEAN updates asynchronously
    # await knowledge_task
    
    # Retrieve stored MBTI & OCEAN
    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    
    instructions = f"""
        You are a conversational agent. 
        
        The user_id is {user_id}.
        You are having a conversation with (this is the user's name) {user_name}. Naturally use their name in your responses. 
        If their name is not available, ask for it first. 
        When the user's name is given, update it using the update_user_name tool.
                
        You will lead the conversation with the user. You will ask questions to get to know the user better.
        Ask your questions in a natural way as the conversation progresses. Ask questions that are relevant to gain accurate MBTI type and OCEAN analysis traits of the user.
        Ask questions that are relevant to the user's message.
        
        DO NOT MENTION MBTI OR OCEAN analysis in your response.
        
        Personality OCEAN Traits of the user are: {ocean_traits}
        Personality MBTI Type of the user is: {mbti_type}
        
        Your conversational style should be: {style_prompt}
    """
    
    logging.info(f"Convo Lead Instructions: {instructions}")
    
    # Generate AI response using system prompt
    convo_lead_agent = Agent(
        name="Lead",
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini",
        tools=[update_user_name, find_personalized_info_about_user]
    )
    
    try:
        response = await Runner.run(convo_lead_agent, user_input.message)
        
        logging.info(f"Convo Lead Response: {response}")
        logging.info(f"new items: {response.new_items}")
        
        # stringify the new items
        #new_items = json.dumps(response.new_items)
    
        return response.final_output
            
    except Exception as e:
        logging.error(f"Error processing convo lead: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


    
    # tools_called = ""
    # for item in response.new_items:
    #     if isinstance(item, ToolCallItem):
    #         tool_name = item.raw_item['name']
    #         tools_called += f"Tool Used: {tool_name}\n"
    
    # Response
    # new_reponse = f"""
    # {tools_called}
    # \n\n
    # {response.final_output}
    # """
    

        
        

        

