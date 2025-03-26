from http.client import HTTPException
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase.conversation_history import append_message_to_history, get_or_create_conversation_history, replace_conversation_history_with_summary
from app.supabase.profiles import ProfileRepository
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import asyncio
import logging
from app.auth import verify_token
from agents import Agent, Runner, WebSearchTool, FileSearchTool, function_tool


router = APIRouter()


class UserInput(BaseModel):
    message: str


profile_repo = ProfileRepository()


def get_user_name(user_id: str) -> str:
    return profile_repo.get_user_name(user_id)

@function_tool
def get_users_name(user_id: str) -> str:
    """
    Retrieves the name of the user from the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    Returns:
    - str: the name of the user
    """ 
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
async def retrieve_personalized_info_about_user(user_id: str, query: str) -> str:
    """
    Retireve personalized information about the user for more personalized, deeper, and meaningful conversation.
    
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

        # Wait for all tasks to complete
        await mbti_task  # MBTI updates asynchronously
        await ocean_task  # OCEAN updates asynchronously
        
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
    
    # Append the new user message to the conversation history
    if user_name is None:
        append_message_to_history(user_id, "user", user_input.message)
    else:
        append_message_to_history(user_id, user_name, user_input.message)
    
    # Initialize the services
    mbti_service = MBTIAnalysisService(user_id)    
    ocean_service = OceanAnalysisService(user_id)

    # Retrieve stored MBTI & OCEAN
    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    
    
    # Retrieve or create the conversation context for the user
    history = get_or_create_conversation_history(user_id)
    
    instructions = f"""
        You are a conversational agent. 
        
        The user_id is {user_id}.
        You are having a conversation with (this is the user's name) {user_name}. 
        If their name is not available, ask for it first. 
        When the user's name is given, update it using the update_user_name tool.
                
        You will lead the conversation with the user. You will ask questions to get to know the user better.
        Ask your questions in a natural way as the conversation progresses. Ask questions that are relevant to gain accurate MBTI type and OCEAN analysis traits of the user.
        Ask questions that are relevant to the user's message.
        
        Keep your language simple, natural, and conversational. Keep it at a 5th grade level.
        
        DO NOT MENTION MBTI OR OCEAN analysis in your response.
        
        Personality OCEAN Traits of the {user_id} are: {ocean_traits}
        Personality MBTI Type of the {user_id} is: {mbti_type}
        
        Your conversational style should be: {style_prompt}
        
        Conversation History: {history}
    """
    
    logging.info(f"Convo Lead Instructions: {instructions}")
    
    # Generate AI response using system prompt
    convo_lead_agent = Agent(
        name="Astra",
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini",
        tools=[get_users_name, update_user_name, retrieve_personalized_info_about_user]
    )
    
    try:
        response = await Runner.run(convo_lead_agent, user_input.message)
    
        logging.info(f"Convo Lead Response: {response}")
        logging.info(f"new items: {response.new_items}")
        
        # result = Runner.run_streamed(agent, "Calculate something!")
        # async for event in result.stream_events():
        #     if event.type == "run_item_stream_event":
        #         if event.item.type == "tool_call_item":
        #             print("-- Tool was called")
        #         elif event.item.type == "tool_call_output_item":
        #             print(f"-- Tool output: {event.item.output}")
        #         elif event.item.type == "message_output_item":
        #             print(f"-- Message: {event.item.text}")
        #     elif event.type == "agent_updated_stream_event":
        #         print(f"Agent switched to: {event.new_agent.name}")
            
        new_input = response.to_input_list()
        
        logging.info(f"New Input: {new_input}")
            
        # Append the agent's response back to the conversation history
        append_message_to_history(user_id, "Lead Convo Agent", response.final_output)
        
        if len(history) >= 10:
            await replace_conversation_history_with_summary(user_id)
                    
        return response.final_output
            
    except Exception as e:
        logging.error(f"Error processing convo lead: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


    


        
        

        

