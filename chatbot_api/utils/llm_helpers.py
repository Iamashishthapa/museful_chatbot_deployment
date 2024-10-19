from pathlib import Path
from string import Template as StringTemplate
import logging

logger = logging.getLogger(__name__)

PROMPTS_PATH = Path(__file__).parent.parent / "prompts"


def load_and_substitute_prompt(skill, **placeholders):
    try:
        # Replace '.' in skill with '/' to form the path
        prompt_subpath = skill.replace(".", "/")
        # Build the complete file path
        prompt_file_path = PROMPTS_PATH / f"{prompt_subpath}.txt"

        # Read the template file
        with open(prompt_file_path, "r") as file:
            template = StringTemplate(file.read()).substitute(**placeholders)
            logger.info(f"Loaded Template: {template}")
        return template

    except FileNotFoundError:
        logger.error(f"Template file {prompt_file_path} not found.")
        return None
    except KeyError as e:
        logger.error(f"Missing placeholder in template: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred while loading the template: {e}")
        return None


def get_prompt(skill, **placeholders):
    return load_and_substitute_prompt(skill, **placeholders)
