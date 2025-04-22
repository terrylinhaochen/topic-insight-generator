import os
import sys

# Add the config directory to the path
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
sys.path.append(config_path)

from prompts.career_single import CAREER_SYSTEM_PROMPT
from prompts.parenting_single import PARENTING_SYSTEM_PROMPT

class PromptHandler:
    def __init__(self):
        self.prompts = {
            'career': CAREER_SYSTEM_PROMPT,
            'parenting': PARENTING_SYSTEM_PROMPT
        }

    def format_prompt(self, domain, user_input):
        """
        Format the prompt for Claude with the appropriate system prompt for the domain.
        
        Args:
            domain (str): The domain to get the prompt for ('career' or 'parenting')
            user_input (str): The user's input content
            
        Returns:
            dict: A dictionary with 'system' and 'user' keys for Claude
            
        Raises:
            ValueError: If the domain is invalid
        """
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