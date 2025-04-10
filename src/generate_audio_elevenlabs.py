import os
import time
import shutil

from elevenlabs import ElevenLabs
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


# from https://github.com/elevenlabs/elevenlabs-examples/blob/main/examples/text-to-speech/python/text_to_speech_file.py
def text_to_speech(text: str, save_file_path: str, is_mock: bool = False) -> str:
    """
    Converts text to speech and saves the output as an MP3 file.

    This function uses a specific client for text-to-speech conversion. It configures
    various parameters for the voice output and saves the resulting audio stream to an
    MP3 file with a unique name.

    Args:
        text (str): The text content to convert to speech.
        save_file_path (str): The path where the audio file will be saved.
        is_mock (bool): If True, uses a pre-recorded audio file from mock_data folder.

    Returns:
        str: The file path where the audio file has been saved.
    """
    if is_mock:
        mock_file_path = 'mock_data/SpongeBob SquarePants_saving money.mp3'
        
        # Copy the mock file to the desired location
        shutil.copy2(mock_file_path, save_file_path)

        time.sleep(2)

        print(f"Mock audio file was copied from '{mock_file_path}' to '{save_file_path}'")
        return save_file_path

    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # Adam pre-made voice
        optimize_streaming_latency="0",
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_turbo_v2",  # use the turbo model for low latency, for other languages use the `eleven_multilingual_v2`
        # voice_settings=VoiceSettings(
        #     stability=0.0,
        #     similarity_boost=1.0,
        #     style=0.0,
        #     use_speaker_boost=True,
        # ),
    )

    # Writing the audio stream to the file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"A new audio file was saved successfully at '{save_file_path}'")

    # Return the path of the saved audio file
    return save_file_path


if __name__ == '__main__':
    hero = 'SpongeBob SquarePants'
    financial_concept = 'saving money'
    with open(f'mock_data/{hero}_{financial_concept}.txt', 'r') as f:
        text = f.read()
        title = text.split('\n\n')[0]
        story = '\n\n'.join(text.split('\n\n')[1:])

    # Generating a unique file name for the output MP3 file
    save_file_path = f"{title}.mp3"
    text_to_speech(text, save_file_path)
