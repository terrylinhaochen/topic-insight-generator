import os
import sys

# Add the config directory to the path
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
sys.path.append(config_path)

from prompts.career import CAREER_SYSTEM_PROMPT
from prompts.parenting import PARENTING_SYSTEM_PROMPT

class PromptHandler:
    def __init__(self):
        self.prompts = {
            'career': CAREER_SYSTEM_PROMPT,
            'parenting': PARENTING_SYSTEM_PROMPT
        }

    def format_prompt(self, domain, user_input):
        if domain not in self.prompts:
            raise ValueError(f"Invalid domain: {domain}")
            
        system_prompt = self.prompts[domain]
        
        return {
            "system": system_prompt,
            "user": user_input
        }

    def get_system_prompt(self, domain: str) -> str:
        if domain not in self.prompts:
            raise ValueError(f"Unknown domain: {domain}")
        return self.prompts[domain]