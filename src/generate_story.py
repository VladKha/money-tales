import logging
import os
import time
from typing import Tuple

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt


# Load environment variables from .env file
load_dotenv()

# Configure logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"), # To obtain an API key, see https://www.alibabacloud.com/help/en/model-studio/developer-reference/get-api-key
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

model = "qwen-max" #"qwen2.5-14b-instruct", #"qwen-max",

@retry(stop=stop_after_attempt(3))
def generate_story(concept: str, hero: str, is_mock: bool = False) -> Tuple[str, str]:
    if is_mock:
        with open(f'mock_data/{hero}_{concept}.txt', 'r') as f:
            text = f.read()
            title = text.split('\n\n')[0]
            story = '\n\n'.join(text.split('\n\n')[1:])

            time.sleep(2)
            return title.strip(), story.strip()

    story_prompt = f"""
Write a fun and engaging short story for children (ages 6-10) that teaches the concept of {concept} using {hero} as the main character.
The story should be easy to understand, age-appropriate, and should naturally weave in the financial lesson through the character's actions and experiences. Use simple language, clear examples, and end with a positive message or moral that reinforces the concept.
Make the tone playful and imaginative, keeping in mind what kids enjoy about {hero}. Avoid sounding too much like a lecture—let the financial lesson come through the story itself.

Strictly adhere to the format.
Don't use any additional formatting.
Use the format:

Story title
---
Story content
"""

    story_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": story_prompt}
                ],
            }
        ],
    )

    story_raw = story_response.choices[0].message.content
    # print(story_raw)
    title, story = story_raw.split("---")

    # TODO:
    # - add structured output (instructor?)?
    # - error handling

    return title.strip(), story.strip()

def edit_story(story: str) -> str:
    prompt = f"""
You are an experienced children's story editor with perfect command of English.
Fix this story. Make all grammar clear and correct.
Fix any wrong punctuation or excessive line or paragraph breaks.
Make fewer paragraphs by joining coherent ones together.
Remove any odd expressions.
If there are phrases that aren't typically used in English or that are hard to understand, replace them with clearer, more common ones that better suit the story.
Start directly with the story — include nothing else in your response.

Story:

{story}
""".strip()

    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return result.choices[0].message.content


if __name__ == "__main__":
    hero = 'SpongeBob SquarePants'
    concept = 'saving money'

    title, story = generate_story(concept=concept,
                                hero=hero)
    with open(f'mock_data/{hero}_{concept}.txt', 'w') as f:
        f.write(title + '\n\n')
        f.write(story)

    with open(f'mock_data/{hero}_{concept}.txt', 'r') as f:
        text = f.read()
        title = text.split('\n\n')[0]
        story = '\n\n'.join(text.split('\n\n')[1:])

    # # Edit the story
    # edited_story = edit_story(story)

    # # Save the edited story
    # with open(f'mock_data/{hero}_{concept}_edited.txt', 'w') as f:
    #     f.write(title + '\n\n')
    #     f.write(edited_story)

    # # Reload and print the edited story
    # with open(f'mock_data/{hero}_{concept}_edited.txt', 'r') as f:
    #     edited_text = f.read()
    #     edited_title = edited_text.split('\n\n')[0]
    #     edited_story = '\n\n'.join(edited_text.split('\n\n')[1:])

    # print("Original Title:", title)
    # print("Original Story:", story)
    # print("\nEdited Title:", edited_title)
    # print("\nEdited Story:", edited_story)
