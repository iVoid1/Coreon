import vosk
import pyaudio
import json
import queue
import sys
import sounddevice
import datetime
import time






class Mic:
    "Microphone input module using Vosk for speech recognition and sounddevice for audio input."

    def __init__(self, model, sample_rate: int = 16000, chunk: int = 8000, log_file: str = "mic_log.txt"):
        """
        Initialize the microphone with the specified Vosk model and parameters.
        :param model: Path to the Vosk model directory.
        :param sample_rate: Sample rate for audio input.
        :param chunk: Number of audio frames per buffer.
        :param log_file: File to log microphone input and recognized speech. Default is "mic_log.txt". if you want to disable logging, set it to None.
        """
        print("Initializing microphone...")
        self.model = vosk.Model(model)
        self._model_name = model
        self.is_listening = False
        self._q = queue.Queue()
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk
        print(f"Using Vosk model: {model} with sample rate: {self.SAMPLE_RATE} and chunk size: {self.CHUNK}")
        self.recognizer = vosk.KaldiRecognizer(self.model, self.SAMPLE_RATE)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.LOG_FILE = log_file
        self.message = ""
        
    async def mic_logger(self, duration:int = 5):
        """
        Start the microphone logger.
        This method listens to the microphone and logs recognized speech to a file.
        """
        start = time.time()
        text = ""
        print("Starting microphone logger...")
        with sounddevice.RawInputStream(samplerate=self.SAMPLE_RATE, blocksize=self.CHUNK,dtype='int16', channels=1, callback=self._audio_callback):
            while not self.is_listening and time.time() - start < duration:
                data = self._q.get()

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    
                    if text.strip():
                        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
                        print(f"{timestamp} {text}")
                        
                        if self.LOG_FILE:
                            # Log the recognized text with timestamp
                            with open(self.LOG_FILE, "a", encoding="utf-8") as log:
                                log.write(f"{timestamp} {text}\n")
                            
                        self.message = text.strip()
                        print(f"Recognized: {self.message}")
            return text.strip()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        if status:
            print("⚠️", status, file=sys.stderr)
        self._q.put(bytes(in_data))
        
        
        

if __name__ == "__main__":
    mic = Mic(model="vosk-model-small-en-us-0.15", sample_rate=16000, chunk=8000, log_file="mic_log.txt")
    import asyncio
    async def main():
        recognized_text = await mic.mic_logger(duration=10)
        print(f"Final recognized text: {recognized_text}")

    asyncio.run(main())