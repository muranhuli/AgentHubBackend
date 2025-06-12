import requests
import os
from core.Computable import Computable
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from coper.Minio import Minio

class TTSInput(BaseModel):
    """Input model for :class:`TTS`."""

    text: str = Field(..., description="Text to convert to speech")
    minio_path: str = Field(
        default='{"bucket": "default-bucket", "object_name": "default-object"}',
        description="Minio path to save the audio file in JSON format"
    )
    model: str = Field(default="speech-02-hd", description="Model to use for TTS")
    voice_id: str = Field(
        default="Boyan_new_platform", 
        description="Voice ID for speech synthesis"
    )
    speed: int = Field(default=1, description="Speech speed")
    pitch: int = Field(default=0, description="Voice pitch")
    volume: int = Field(default=1, description="Audio volume")
    emotion: str = Field(default="happy", description="Voice emotion")
    sample_rate: int = Field(default=32000, description="Audio sample rate")
    bitrate: int = Field(default=128000, description="Audio bitrate")
    language_boost: str = Field(default="auto", description="Language boost setting")
    audio_format: str = Field(default="mp3", description="Audio format")


class TTSOutput(BaseModel):
    """Output model for :class:`TTS`."""
    filename: str = Field(..., description="Filename where audio was saved")
    success: bool = Field(..., description="Whether TTS generation was successful")
    message: str = Field(default="", description="Status message or error description")


class TTS(Computable):
    """Text-to-Speech conversion using MiniMax API."""

    def __init__(self):
        super().__init__()
        self._load_env()  # Load environment variables from .env file
        self.group_id = os.getenv("MINIMAX_GROUP_ID")
        self.api_key = os.getenv("MINIMAX_API_KEY")


    def _load_env(self):
        """加载项目根目录下的.env文件"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)

    def compute(
        self, 
        text: str,
        minio_path: dict[str, str]={'bucket': 'default-bucket', 'object_name': 'default-object'},
        model: str = "speech-02-hd",
        voice_id: str = "Boyan_new_platform",
        speed: int = 1,
        pitch: int = 0,
        volume: int = 1,
        emotion: str = "happy",
        sample_rate: int = 32000,
        bitrate: int = 128000,
        language_boost: str = "auto",
        audio_format: str = "mp3"
    ) -> dict:
        """Convert text to speech using MiniMax API.

        Args:
            text: Text to convert to speech
            filename: Output filename for the audio file
            voice_id: Voice ID for speech synthesis
            speed: Speech speed (0.5-2.0)
            pitch: Voice pitch (-20 to 20)
            volume: Audio volume (0.1-3.0)
            emotion: Voice emotion
            sample_rate: Audio sample rate
            bitrate: Audio bitrate
            audio_format: Audio format
        Returns:
            Dictionary containing audio data, filename, success status, and message
        """
        try:
            url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "text": text,
                "timber_weights": [
                    {
                        "voice_id": voice_id,
                        "weight": 1
                    }
                ],
                "voice_setting": {
                    "voice_id": "",
                    "speed": speed,
                    "pitch": pitch,
                    "vol": volume,
                    "emotion": emotion,
                    "latex_read": False
                },
                "audio_setting": {
                    "sample_rate": sample_rate,
                    "bitrate": bitrate,
                    "format": audio_format
                },
                "language_boost": language_boost
            }

            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                if "data" in response_data and "audio" in response_data["data"]:
                    hex_audio = response_data["data"]["audio"]
                    audio_bytes = bytes.fromhex(hex_audio)
                    # 获取写入minio路径的元数据信息
                    bucket = minio_path.get("bucket", "default-bucket")
                    object_name = minio_path.get("object_name", "default-object")
                    if not object_name.endswith(f".{audio_format}"):
                        full_filename = f"{object_name}.{audio_format}"
                    else:
                        full_filename = object_name
                    # 写入音频数据到Minio
                    Minio()(
                        function_name="write",
                        bucket=bucket,
                        object_name=full_filename,
                        data=audio_bytes
                    )
                    
                    return {
                        'success': True,
                        'minio_path': {
                            'bucket': bucket,
                            'object_name': full_filename
                        },
                        'message': "Audio generated successfully"
                    }
                else:
                    return {
                        'success': False,
                        'minio_path': {
                            'bucket': "",
                            'object_name': ""
                        },
                        'message': "No audio data found in response"
                    }
            else:
                return {
                    'success': False,
                    'minio_path': {
                        'bucket': "",
                        'object_name': ""
                    },
                    'message': f"Request failed with status code {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'minio_path': {
                    'bucket': "",
                    'object_name': ""
                },
                'message': str(e)
            }
