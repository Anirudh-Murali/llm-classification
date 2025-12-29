import os
import glob
from typing import List, Dict

class PromptManager:
    def __init__(self, prompt_folder: str):
        """
        Initialize PromptManager with a prompt folder.
        
        Expected structure:
        prompt_folder/
            system_prompt.txt       # Template with {{CATEGORIES}} placeholder
            categories/
                category1.txt
                category2.txt
                ...
        """
        self.prompt_folder = prompt_folder
        self.categories_dir = os.path.join(prompt_folder, "categories")
        self.system_prompt_path = os.path.join(prompt_folder, "system_prompt.txt")
        
        self.categories = self._load_categories()
        self.category_names = list(self.categories.keys())
        
    def _load_categories(self) -> Dict[str, str]:
        """Load all category definition files."""
        categories = {}
        pattern = os.path.join(self.categories_dir, "*.txt")
        files = glob.glob(pattern)
        
        for file_path in files:
            category_name = os.path.splitext(os.path.basename(file_path))[0]
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            categories[category_name] = content
        return categories

    def _build_categories_section(self) -> str:
        """Build the categories section to inject into the prompt."""
        parts = []
        for name, content in self.categories.items():
            parts.append(f"**{name}**\n{content}\n")
        return "\n".join(parts)

    def get_system_prompt(self) -> str:
        """Load system prompt template and inject categories."""
        # Load template
        with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Build categories section
        categories_section = self._build_categories_section()
        
        # Inject into template
        prompt = template.replace("{{CATEGORIES}}", categories_section)
        
        return prompt
    
    def get_valid_categories(self) -> List[str]:
        """Return list of valid category names for validation."""
        return self.category_names + ["unclassified"]
