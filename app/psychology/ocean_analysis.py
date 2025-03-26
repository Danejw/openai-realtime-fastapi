from pydantic import BaseModel
from agents import Agent, Runner
import logging
from app.supabase.supabase_ocean import Ocean, OceanRepository

    
logging.basicConfig(level=logging.INFO)

class OceanResponse(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

instructions = """
You are an expert in personality analysis. You will be given a message and you will need to analyze the message and return an OCEAN personality analysis of the message.
            
The OCEAN personality analysis should have 5 dimensions:
- Openness
- Conscientiousness
- Extraversion
- Agreeableness
- Neuroticism

Each dimension should have a score between 0 and 1, with 1 being the highest score.
"""

ocean_agent = Agent(
    name="OCEAN",
    handoff_description="A Ocean framework sentiment analysis agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=OceanResponse,
)

class OceanAnalysisService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = OceanRepository()
        self.ocean = self.repository.get_ocean(self.user_id) or Ocean()
        self.load_ocean()

    def load_ocean(self):
        stored_ocean = self.repository.get_ocean(self.user_id)
        if stored_ocean:
            self.ocean = stored_ocean
        else:
            logging.info(f"No existing OCEAN data for user {self.user_id}. Using defaults.")

    def save_ocean(self):
        self.repository.upsert_ocean(self.user_id, self.ocean)

    async def analyze_message(self, message: str):
        try:
            ocean_result = await Runner.run(ocean_agent, message)
            logging.info(f"OCEAN result: {ocean_result}")
                    
            # Update rolling average
            self._update_ocean_rolling_average(OceanResponse(**ocean_result.final_output.dict()))
            
            # Save the updated OCEAN data to Supabase
            self.save_ocean()
            
            return ocean_result.final_output
            
        except Exception as e:
            logging.error(f"Error in OCEAN analysis: {e}")
            return None  # Return None to indicate analysis failed

    def _update_ocean_rolling_average(self, new_ocean: OceanResponse):
        old_count = self.ocean.response_count
        new_count = old_count + 1

        self.ocean.openness = (self.ocean.openness * old_count + new_ocean.openness) / new_count
        self.ocean.conscientiousness = (self.ocean.conscientiousness * old_count + new_ocean.conscientiousness) / new_count
        self.ocean.extraversion = (self.ocean.extraversion * old_count + new_ocean.extraversion) / new_count
        self.ocean.agreeableness = (self.ocean.agreeableness * old_count + new_ocean.agreeableness) / new_count
        self.ocean.neuroticism = (self.ocean.neuroticism * old_count + new_ocean.neuroticism) / new_count

        self.ocean.response_count = new_count
        logging.info(f"Updated OCEAN rolling average for user {self.user_id}.")

    def get_personality_traits(self) -> dict:
        """
        Returns the current OCEAN scores as personality traits.
        """
        return {
            "openness": "High" if self.ocean.openness >= 0.5 else "Low",
            "conscientiousness": "High" if self.ocean.conscientiousness >= 0.5 else "Low",
            "extraversion": "High" if self.ocean.extraversion >= 0.5 else "Low",
            "agreeableness": "High" if self.ocean.agreeableness >= 0.5 else "Low",
            "neuroticism": "High" if self.ocean.neuroticism >= 0.5 else "Low"
        }


