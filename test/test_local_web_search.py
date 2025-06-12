import uuid

from coper.LLM import LLM
from coper.basic_ops import Mul
from coper.Test import Test
from core.Context import Context
from coper.Service import Service

if __name__ == '__main__':
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        add = Test()
        mul = Mul()
        search = Service("local-web-search")
        llm_s = LLM("Qwen3-32B", "VLLM")
        # llm_lite = LLM("volcengine/doubao-1-5-lite-32k-250115")
        # llm_pro = LLM("volcengine/doubao-1-5-pro-32k-250115")
        # llm_dsr1 = LLM("volcengine/deepseek-r1-250528")


        query = "Qwen3 最新模型"

        keywords = llm_s(f"""用户的查询是：{query}
请给出 1 - 2 组相关的搜索关键词，从而全面准确的回答用户的问题。可以尝试使用不同语言或不同的角度检索。
多组关键词通过|分割，关键词中不能含有 |，可以含有逗号或空格等其余内容。请不要给出任何其他内容。
输出格式距离：xxx xxx|yy yyyy|zzzzz。
""").result()["content"]
        keywords = keywords.strip().split("|")
        print("关键词：", keywords)
        web_res = []
        for i in range(len(keywords)):
            web_res.append(search(keywords[i].strip(), "google", 2))

        simple = []
        res = []
        for i in range(len(web_res)):
            tr = web_res[i].result()
            for ts in tr:
                res.append(ts)
                simple.append(llm_s(f"""查询的内容是：{query}
网站的搜索结果为，标题为：{ts['title']}，内容为：{ts['content']}
请提取所有与查询内容相关的资料，使用纯文本，不包含任何图片或链接，使用最精简的形式输出，要尽可能的遵循网页内容的原文。
"""))

        for i in range(len(simple)):
            res[i]["content"] = simple[i].result()["content"]

        final_str = ""

        for i in range(len(res)):
            final_str += (f"第{i + 1}个结果：\n"
                          f"title: {res[i]['title']}\n"
                          f"url: {res[i]['url']}\n"
                          f"content: {res[i]['content']}\n\n")
        final = llm_s(f"""用户的查询是：{query}
搜索结果：{final_str}
请根据搜索结果，请尽可能的全面准确的回答用户的问题。
""").result()["content"]
        print(final)




