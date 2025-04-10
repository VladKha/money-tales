import os

import gradio as gr
import logging
from datetime import datetime

from dotenv import load_dotenv

from src.generate_rss import generate_rss_feed
from src.generate_story import generate_story
from src.generate_audio_elevenlabs import text_to_speech
from src.db import AlibabaCloudOSSStorageDB

# Load environment variables from .env file
load_dotenv()

# Configure logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_HERO = "SpongeBob SquarePants"
DEFAULT_CONCEPT = "saving money"
IS_MOCK = os.getenv("IS_MOCK", "True").lower() == "true"
DB = AlibabaCloudOSSStorageDB()

def make_story(hero, concept, timestamp):
    # Generate story
    title, story = generate_story(concept=concept, hero=hero, is_mock=IS_MOCK)

    # Save the story
    filename = f"{hero}_{concept}_{timestamp}/{hero}_{concept}.txt"
    content = f"{title}\n\n{story}"
    url = DB.save_to_file(content, filename)
    logging.info(f"Story saved to OSS: {url}")
    
    # Format the story with title
    formatted_story = f"{title}\n\n{story}"
    return formatted_story

def make_audio(story, hero, concept, timestamp):
    # Generate audio
    audio_file_name = f"{hero}_{concept}.mp3"
    text_to_speech(story, audio_file_name, is_mock=IS_MOCK)
    
    # Save to OSS
    cloud_audio_file_path = f"{hero}_{concept}_{timestamp}/{audio_file_name}"
    with open(audio_file_name, 'rb') as f:
        audio_url = DB.save_to_file(f.read(), cloud_audio_file_path)
    logging.info(f"Audio saved to OSS: {audio_url}")
    
    return audio_file_name

def make_rss_feed():
    output_file = 'rss_feed.xml'
    rss_content = generate_rss_feed(DB, output_file)
    logging.info(f"RSS feed created in {output_file}")
    DB.save_to_file(rss_content, output_file)
    logging.info(f"RSS feed file saved to OSS")


with gr.Blocks(title="MoneyTales", theme=gr.themes.Ocean()) as demo:
    gr.Markdown("""
<h1 style='text-align: center'>MoneyTales</h1>
<p style='text-align: center; font-size: 16px; color: #666; margin: 20px 0;'>
    Financial literacy for kids through personalized, engaging audio stories featuring their favorite characters
</p>""")
    
    with gr.Row():
        with gr.Column():
            hero_input = gr.Dropdown(
                label="Your hero",
                choices=[
                    "SpongeBob SquarePants",
                    "Mickey Mouse",
                    "Sonic the Hedgehog",
                    "Pikachu",
                    "Mario",
                    "Spiderman",
                    "Batman",
                    "Superman",
                    "Wonder Woman",
                    "Thor",
                    "Captain America",
                    "Iron Man"
                ],
                value=DEFAULT_HERO
            )
        with gr.Column():
            concept_input = gr.Dropdown(
                label="Financial concept",
                choices=[
                    "saving money",
                    "what money is and how we use it",
                    "budgeting",
                    "earning money",
                    "needs vs wants",
                    "sharing and giving",
                    "delayed gratification",
                    "financial goal setting",
                    "smart shopping",
                    "impulsive buying and how to avoid it",
                    "compound interest",
                    "investing",
                    "banks",
                    "inflation"
                ],
                value=DEFAULT_CONCEPT
            )
    
    generate_btn = gr.Button("Generate story", variant="primary")

    with gr.Blocks():
        with gr.Row():
            audio_output = gr.Audio(label="Story Audio", show_download_button=True, visible=False)
        with gr.Row():
            story_output = gr.TextArea(visible=False, max_lines=20, autoscroll=False) #Markdown())

    def on_generate_step_1(hero, concept, progress=gr.Progress()):
        # Validate inputs and use placeholder values if empty
        if not hero.strip():
            hero = DEFAULT_HERO
        if not concept.strip():
            concept = DEFAULT_CONCEPT
            
        # First, generate and show the story text with progress
        yield gr.TextArea(label="Story", visible=True, autoscroll=False)
        progress(0, desc="Generating story...")
        story = make_story(hero, concept, timestamp)
        progress(100, desc="Story generation complete!")
        yield gr.TextArea(value=story, visible=True, autoscroll=False)
    
    def on_generate_step_2(story, hero, concept, progress=gr.Progress()):
        yield gr.Audio(label="Story Audio", visible=True)
        
        # Then generate audio in the background
        progress(0, desc="Generating audio...")
        if not hero.strip():
            hero = DEFAULT_HERO
        if not concept.strip():
            concept = DEFAULT_CONCEPT
        audio = make_audio(story, hero, concept, timestamp)

        make_rss_feed()

        progress(100, desc="Generation complete!")
        yield gr.Audio(label="Story Audio", value=audio, show_download_button=True, visible=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generate_btn.click(
        fn=on_generate_step_1,
        inputs=[hero_input, concept_input],
        outputs=[story_output]
    ).then(
        fn=on_generate_step_2,
        inputs=[story_output, hero_input, concept_input],
        outputs=[audio_output]    
    )

if __name__ == "__main__":
    demo.queue().launch(show_error=True, inbrowser=True)
