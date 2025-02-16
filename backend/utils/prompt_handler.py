from config.prompts import career, parenting

class PromptHandler:
    def __init__(self):
        from config.prompts.career import CAREER_SYSTEM_PROMPT
        from config.prompts.parenting import PARENTING_SYSTEM_PROMPT
        
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