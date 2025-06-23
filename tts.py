from io import BytesIO
import pydub
from pydub.playback import play
import edge_tts

class TTS:

    "Text-to-Speech module using edge-tts and pydub for audio playback."

    def __init__(self):
        self.voice = "en-US-GuyNeural"
        self.loading_message = "Loading TTS engine..."

    def set_voice(self, voice: str):
        """Set the voice for TTS."""
        self.voice = voice
    
    def clean_text(self, text: str) -> str:
        """
        Clean the input text by removing unwanted characters.
        This is a placeholder for any specific cleaning logic you might want to implement.
        """
        # Example cleaning logic: remove extra spaces and newlines
        text = text.replace("#", " ").replace("**", " ").replace("`", " ")
        return text

    async def speak(self, text: str, voice: str = "en-US-GuyNeural"):
        # create buffer to hold mp3 data
        buffer = BytesIO()

        # initialize edge-tts communicator
        communicator = edge_tts.Communicate(text, voice=voice)

        # stream audio into memory
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                buffer.write(chunk["data"])

        # rewind and decode mp3
        buffer.seek(0)
        sound = pydub.AudioSegment.from_file(buffer, format="mp3")

        # play audio from memory
        play(sound)
