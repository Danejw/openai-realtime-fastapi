import asyncio
from agents import Agent, Runner, function_tool, trace, ItemHelpers

from chinese_zodiac import get_chinese_zodiac
from pydantic import BaseModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from western_zodiac import get_western_zodiac


class OceanOutput(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    
class MBTIOutput(BaseModel):
    introversion: float
    extroversion: float
    sensing: float
    intuition: float
    thinking: float
    feeling: float
    judging: float
    perceiving: float
    
    
birthMonth = 9
birthDay = 7
birthyear = 1989
western_zodiac = get_western_zodiac(birthMonth, birthDay)
chinese_zodiac = get_chinese_zodiac(birthyear)


voice_agent = Agent(
    name="voice",
    handoff_description="A voice agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, speak like so.",
    ),    
    model="gpt-4o-mini",
)

ocean_agent = Agent(
    name="Sentiment",
    handoff_description="A sentiment analysis agent.",
    instructions=
        "Create a sentiment analysis of the user's message.",
    model="gpt-4o-mini",
    output_type=OceanOutput,
)

mbti_agent = Agent(
    name="MBTI",
    handoff_description="A MBTI analysis agent.",
    instructions=
        "Create a MBTI analysis of the user's message.",
    model="gpt-4o-mini",
    output_type=MBTIOutput,
)


async def main():
    msg = "I like to think about how random the world is."

    ocean_result = await Runner.run(ocean_agent, msg)
    mbti_result = await Runner.run(mbti_agent, msg)

    print(f"Ocean: {ocean_result.final_output}")
    print(f"MBTI: {mbti_result.final_output}")
    
    voice_result = await Runner.run(voice_agent, f"User message: {msg}\n Sentiments: \n Zodiac: {western_zodiac} {chinese_zodiac}\n Ocean: {ocean_result.final_output}\n MBTI: {mbti_result.final_output}")
    
    print(f"Voice: {voice_result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())