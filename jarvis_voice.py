import os
import uuid
import subprocess
# pip install python-dotenv
from dotenv import load_dotenv
# pip install elevenlabs
from elevenlabs.client import ElevenLabs

# Load .env file
load_dotenv()

# Set up ElevenLabs client
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Brian voice ID (official)
BRIAN_VOICE_ID = "N2lVS1w4EtoT3dr4eOWO"

# Play audio using ffplay
def play_audio_ffplay(file_path):
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", file_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# Generate and speak text
def speak(text):
    filename = f"jarvis_{uuid.uuid4().hex}.mp3"

    # Get voice output as generator
    audio_generator = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=BRIAN_VOICE_ID,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128"
    )

    # Combine and save audio
    with open(filename, "wb") as f:
        f.write(b"".join(audio_generator))

    # Play the audio
    play_audio_ffplay(filename)

    # Remove after playing
    os.remove(filename)