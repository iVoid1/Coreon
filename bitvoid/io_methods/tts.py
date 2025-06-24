import edge_tts
import pydub
from pydub.playback import play # pydub is a simple and easy-to-use Python library for audio processing
from io import BytesIO # BytesIO is used to handle byte streams in memory
#TODO : replace edge-tts with gTTS for better compatibility
from gtts import gTTS # gTTS is a Google Text-to-Speech library




class TTS:

    "Text-to-Speech module using edge-tts and pydub for audio playback."

    def __init__(self, voice: str = "en-US-GuyNeural"):
        self.voice = voice
        self.communicator = edge_tts.Communicate(text="", voice=voice)

    def set_voice(self, voice: str):
        """Set the voice for TTS."""
        self.voice = voice
        self.communicator = edge_tts.Communicate(text="", voice=self.voice)

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
