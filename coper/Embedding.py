import os
import requests
from core.Computable import Computable
from typing import Union, List
from dotenv import load_dotenv


class Embedding(Computable):
    """
    使用embedding计算文本的嵌入向量。
    """

    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env-llm')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        self.url = os.getenv('EMBEDDING_URL')
        self.api_key = os.getenv('EMBEDDING_API_KEY')
        self.model = os.getenv('EMBEDDING_MODEL')
    
    def compute(self, text: Union[str, List[str]], **kwargs):
        """
        计算文本的嵌入向量
        
        Args:
            text (Union[str, List[str]]): 输入文本，可以是单个字符串或字符串列表
            
        Returns:
            Union[List[float], List[List[float]], None]: 
            - 单个文本: 返回嵌入向量列表
            - 多个文本: 返回嵌入向量列表的列表
            - 失败时返回 None
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 处理输入格式
        is_single = isinstance(text, str)
        input_texts = [text] if is_single else text
        
        data = {
            "model": self.model,
            "input": input_texts
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            response.raise_for_status()  # 抛出HTTP错误异常
            
            result = response.json()
            
            # 提取嵌入向量
            if 'data' in result and len(result['data']) > 0:
                embeddings = [item.get('embedding', None) for item in result['data']]
                
                # 检查是否所有嵌入都成功获取
                if None in embeddings:
                    return None
                
                # 根据输入类型返回相应格式
                return embeddings[0] if is_single else embeddings
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"响应解析失败: {e}")
            return None