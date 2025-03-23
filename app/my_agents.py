import asyncio
from agents import Agent, Runner, function_tool, trace, ItemHelpers, RunContextWrapper

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

mbti = "INTJ"


@function_tool
def get_irony_definition():
    return "Irony is a literary device that involves a contrast between what is expected and what actually happens. It can be classified into several types, including situational irony, verbal irony, and dramatic irony."


voice_agent = Agent(
    name="voice",
    handoff_description="A voice agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, speak like so.",
    ),    
    model="gpt-4o-mini",
    tools=[get_irony_definition],
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

witty_agent = Agent(
    name="Wit",
    handoff_description="A witty response agent.",
    instructions=
        "You are a witty agent that can make light in the conversation given the context.",
    model="gpt-4o-mini",
)



async def main():
    msg = "so the Situational Irony Is that I am learning how irony works. can you tell me more about it?"

    ocean_result = await Runner.run(ocean_agent, msg)
    mbti_result = await Runner.run(mbti_agent, msg)

    print(f"Ocean: {ocean_result.final_output}")
    print(f"MBTI: {mbti_result.final_output}")
    
    voice_result = await Runner.run(voice_agent, f"User message: {msg}\n Sentiments: \n Zodiac: {western_zodiac} {chinese_zodiac}\n Ocean: {ocean_result.final_output}\n MBTI: The user is an  {mbti} and asks: {mbti_result.final_output}")
    witty_result = await Runner.run(witty_agent, f"User message: {msg}\n Sentiments: \n Zodiac: {western_zodiac} {chinese_zodiac}\n Ocean: {ocean_result.final_output}\n MBTI: The user is an  {mbti} and asks: {mbti_result.final_output}")

    print(f"Voice: {witty_result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())