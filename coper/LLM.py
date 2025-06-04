from core.Computable import Computable
from dotenv import load_dotenv
import os
import litellm


class LLM(Computable):
    """Call large language models via the LiteLLM library."""

    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env-llm')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)

    def compute(self, model: str, prompt: str):
        response = litellm.completion(model=model, messages=[{"role": "user", "content": prompt}], stream=False)
        return response["choices"][0]["message"]["content"]
