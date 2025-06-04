import uuid
from typing import Any

from coper.LLM import LLM
from coper.Mul import Mul
from coper.Test import Test
from core.Context import Context
from coper.Service import Service

if __name__ == '__main__':
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        add = Test()
        mul = Mul()
        search = Service("local-web-search")
        llm_lite = LLM("volcengine/doubao-1-5-lite-32k-250115")
        llm_pro = LLM("volcengine/doubao-1-5-pro-32k-250115")

        query = "python 如何实现多线程"

        keywords = llm_pro(f"""用户的问题是：{query}
请给出 3-5 组相关的搜索关键词，从而全面准确的回答用户的问题。可以尝试使用不同语言或不同的表达方式来描述同一内容。
多组关键词通过|分割，关键词中不能含有 |，可以含有逗号或空格等其余内容。请不要给出任何其他内容。
输出格式距离：xxx xxx|yy yyyy|zzzzz。
""").result()
        keywords = keywords.strip().split("|")
        print("关键词：", keywords)
        web_res = []
        for i in range(len(keywords)):
            web_res.append(search(keywords[i].strip(), "bing", 5))

        simple = []
        res = []
        for i in range(len(web_res)):
            tr = web_res[i].result()
            for ts in tr:
                res.append(ts)
                simple.append(llm_lite(f"""查询的内容是：{query}
网站的搜索结果为，标题为：{ts['title']}，内容为：{ts['content']}
请提取所有与查询内容相关的资料，使用纯文本，不包含任何图片或链接，使用最精简的形式输出，要尽可能的遵循网页内容的原文。
"""))

        for i in range(len(simple)):
            res[i]["content"] = simple[i].result()

        for i in range(len(res)):
            print(f"第{i + 1}个结果：")
            print("title:", res[i]["title"])
            print("url:", res[i]["url"])
            print("content:", res[i]["content"])
            print()
