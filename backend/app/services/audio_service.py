import os
import logging
import whisper
import yt_dlp


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class AudioProcessingService:
    def __init__(self):
        """Initialize the service and configure the local model."""
        self.whisper_model_name = os.getenv("WHISPER_MODEL", "base")
        self._model = None 

    def _load_model(self):
        """Only load the heavy AI model into memory when a request actually comes in."""
        if self._model is None:
            logger.info(f"Loading local Whisper model: {self.whisper_model_name}")
            self._model = whisper.load_model(self.whisper_model_name)
        return self._model

    def _acquire_audio(self, source: str) -> str:
        """Determines if the source is YouTube or local."""
        if source.startswith("http://") or source.startswith("https://"):
            logger.info(f"Downloading YouTube audio: {source}")
            output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_path,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}],
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source, download=True)
                return ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
        else:
            logger.info(f"Processing local file: {source}")
            
            return source

    def transcribe(self, source: str) -> str:
        """The main pipeline: acquires the audio and transcribes it securely on-device."""
        wav_path = self._acquire_audio(source)
        
        logger.info("Audio ready. Starting local Whisper transcription...")
        model = self._load_model()
        
        
        result = model.transcribe(wav_path)
        
        logger.info("Transcription successfully completed.")
        return result["text"]