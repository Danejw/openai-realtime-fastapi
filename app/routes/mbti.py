from app.psychology.supabase_mbti import MBTI
from fastapi import APIRouter, Request
from app.psychology.mbti_analysis import MBTIAnalysisService
from pydantic import BaseModel

router = APIRouter()


class MBTIRequest(BaseModel):
    user_id: str
    message: str
    
class MBTIUpdateRequest(BaseModel):
    user_id: str
    extraversion_introversion: float
    sensing_intuition: float
    thinking_feeling: float
    judging_perceiving: float
    
class MBTIAnalysisRequest(BaseModel):
    message: str
    
class MBTITypeRequest(BaseModel):
    user_id: str
    

@router.post("/mbti-analyze")
async def mbti_analyze(data: MBTIRequest):
    user_id = data.user_id
    message = data.message

    # Create a new analysis service for this user
    service = MBTIAnalysisService(user_id)
    # Perform the analysis
    await service.analyze_message(message)

    # Get final MBTI type
    final_type = service.get_mbti_type()
    style_prompt = service.generate_style_prompt("INTJ")

    return {
        "mbti_type": final_type,
        "style_prompt": style_prompt
    }


@router.get("/mbti/{user_id}")
async def get_mbti(user_id: str):
    service = MBTIAnalysisService(user_id)
    mbti_data = service.repository.get_mbti(user_id)

    if mbti_data:
        return mbti_data.dict()
    else:
        return {"error": "No MBTI data found for this user"}
    

@router.post("/mbti-update")
async def update_mbti(data: MBTIUpdateRequest):
    """
    Updates the MBTI data for a given user in Supabase,
    applying the rolling average before saving.
    """
    user_id = data.user_id

    # Initialize the MBTI Analysis Service
    service = MBTIAnalysisService(user_id)

    # Construct a new MBTI object with the incoming data
    new_mbti = MBTI(
        extraversion_introversion=data.extraversion_introversion,
        sensing_intuition=data.sensing_intuition,
        thinking_feeling=data.thinking_feeling,
        judging_perceiving=data.judging_perceiving,
        response_count=1  # This will be updated in the rolling average function
    )

    # Apply rolling average update
    service._update_mbti_rolling_average(new_mbti)

    # Save the updated MBTI data to Supabase
    service.save_mbti()

    return {
        "message": "MBTI data updated successfully",
        "mbti": service.mbti.dict()
    }
    

@router.get("/mbti-type/{user_id}")
async def get_mbti_type(user_id: str):
    service = MBTIAnalysisService(user_id)
    mbti_type = service.get_mbti_type()
    return {"mbti_type": mbti_type}


