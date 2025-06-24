import asyncio

from io_methods.stt import Mic
from io_methods.tts import TTS
from data.Config import config
from model.BitVoid import BitVoid


#TODO : Add model selection logic if needed
#TODO : Add error handling for model loading
#TODO : Add conversation history management
#TODO : Add streaming support for TTS if needed
#TODO : Add logging for better debugging and monitoring
#TODO : Add configuration validation for required fields
#TODO : Add support for multiple languages in TTS if needed


class Main:
    """
    Main application controller that manages microphone input and text-to-speech output.
    """

    def __init__(self):
        # Initialize microphone and TTS components using config values
        self.mic = Mic(
            model=config.MODEL_PATH,
            sample_rate=config.SAMPLE_RATE,
            chunk=config.CHUNK,
            log_file=config.LOG_FILE
        )
        self.tts = TTS()
        self.model = Model()
        print(f"Using model: {self.model.model_name}")
    async def run(self):
        """
        Starts the microphone listener loop and speaks any recognized text.
        """
        mic_logger_task = asyncio.create_task(self.mic.mic_logger())

        while True:
            await asyncio.sleep(0.1)  # Prevent CPU spin

            if mic_logger_task.done():
                recognized_text = mic_logger_task.result()
                if recognized_text:
                    await self.tts.speak(recognized_text)

                # Restart microphone logger for next input
                mic_logger_task = asyncio.create_task(self.mic.mic_logger())

    #TODO : function to handle user input and model interaction
    #TODO : function to handle TTS output and voice selection
    #TODO : function to handle conversation history


if __name__ == "__main__":
    # Launch the application
    asyncio.run(Main().run())

