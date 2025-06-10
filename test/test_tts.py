from core.Context import Context
import uuid
from coper.TTS import TTS
import time
from pydantic import BaseModel, Field

if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        start = time.time()
        # 使用 TTS 类
        tts = TTS()

        # 测试文本转语音
        prompt = "我看 codex 已经可以调用 gdb 调试大型项目了，这个就是给了大模型与shell交互的能力。"
        minio_path = {
            'bucket': 'test-bucket',
            'object_name': 'test_tts.mp3'
        }
        response1 = tts(prompt, minio_path=minio_path).result()
        print(response1)
        end = time.time()
        print(f"Total time taken: {end - start:.2f} seconds")

