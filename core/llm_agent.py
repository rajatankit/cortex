import os
import google.generativeai as genai
from core.agent import BaseAgent, AgentResult

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


class LLMAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, role: str, specialty: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.specialty = specialty
        self.enabled = True

        self.system_prompt = f"""Tum {self.name} ho, CORTEX ke ek specialist AI agent, jo Battle Crown esports platform manage karne mein madad karta hai.

Role: {self.role}
Expertise: {self.specialty}

Personality:
- Natural Hinglish mein baat karo, jaise ek smart, calm teammate karta hai
- Boss (admin) ko "Boss" bol sakte ho jab natural lage
- Clear aur direct raho — zyada lamba, robotic ya formal mat bano
- Context data diya gaya hai to usko use karke concrete jawab do, generic mat bolo
- Agar kuch pata nahi ya missing info hai to seedha bata do, guess mat karo
- Kabhi bhi gambling/RNG/luck-based mechanics suggest mat karo — Battle Crown skill-based platform hai"""

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self.system_prompt,
        )

    async def handle(self, task: str, context: dict | None = None) -> AgentResult:
        try:
            prompt = f"Task: {task}\nContext: {context or {}}"
            response = self.model.generate_content(prompt)
            reply = response.text

            return AgentResult(
                success=True,
                agent=self.agent_id,
                message=reply,
                data={"task": task},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=f"{self.name} ko response generate karne mein error aaya: {str(e)}",
                data={"task": task},
            )