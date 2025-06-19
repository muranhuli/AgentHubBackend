# AgentHub 操作符与服务使用说明

本文档面向大语言模型，介绍本项目提供的各类算子（Operator）及服务（Service）的使用方式。所有示例均需在 `core.Context.Context` 管理的环境中执行。

## 目录
- [基础算子 basic_ops](#基础算子-basic_ops)
- [LLM](#llm)
- [Embedding](#embedding)
- [VectorDB](#vectordb)
- [Minio](#minio)
- [TTS](#tts)
- [Service](#service)
- [内置服务](#内置服务)


## 基础算子 basic_ops

### 功能简介
提供常见的数学与逻辑运算，包括加减乘除、比较以及按位运算等。

### 输入参数
所有二元运算使用 `BinaryInput`：
- `x`：第一个操作数，任意类型。
- `y`：第二个操作数，任意类型。

部分单目运算使用 `UnaryInput`：
- `x`：操作数。

### 输出参数
`BasicOutput`：
- `result`：运算结果，类型与输入相关。

### 功能说明
调用方式为实例化对应算子后直接传入参数，例如 `Add()(3, 2)`。算子返回 `ComputableResult`，通过 `.result()` 获取最终值。

### 示例
```python
from core.Context import Context
from coper.basic_ops import Add, LogicalNot
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    add = Add()
    res = add(3, 2).result()   # 5
    flag = LogicalNot()(True).result()  # False
```

## LLM

### 功能简介
封装 LiteLLM 的接口，支持语言模型与视觉模型调用，并可根据提供的 JSON Schema 生成结构化输出。

### 输入参数
`LLMInput`：
- `prompt` (str)：发送给模型的文本提示。
- `image_base64` (str，可选)：如提供则按多模态方式处理，需为 base64 编码的图片数据。
- `structured_output` (dict，可选)：期望的 JSON Schema，若提供则模型返回符合该结构的数据。

### 输出参数
`LLMOutput`：
- `content` (str)：模型生成的文本内容。
- `reasoning_content` (str)：推理过程描述（若有）。
- `structured_output` (dict)：当请求结构化输出时，解析后的结果。

### 功能说明
实例化时需指定 `model`，可选 `custom_provider` 对应不同的 LLM 服务商，环境变量中需配置 `${PROVIDER}_API_KEY` 与 `${PROVIDER}_BASE_URL`。调用后返回 `ComputableResult`，通过 `.result()` 获取 `LLMOutput` 字典。

### 示例
```python
from core.Context import Context
from coper.LLM import LLM
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    llm = LLM(model="doubao-1-5-thinking-pro-250415", custom_provider="ARK")
    resp = llm("讲解相对论的核心思想").result()
    print(resp)
```
示例输出：
```json
{"content": "相对论是..."}
```

## Embedding

### 功能简介
将文本转化为向量表示，便于向量检索或相似度计算。

### 输入参数
- `text` (str 或 List[str])：待转换的文本或文本列表。

### 输出参数
- 返回单个向量 (List[float]) 或向量列表 (List[List[float]])，请求失败时返回 `None`。

### 功能说明
初始化时自动从 `.env` 读取 `EMBEDDING_URL`、`EMBEDDING_API_KEY` 和 `EMBEDDING_MODEL`。调用实例并传入文本即可获得嵌入向量。

### 示例
```python
from core.Context import Context
from coper.Embedding import Embedding
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    emb = Embedding()
    vec = emb("Hello, world!").result()
    print(vec)
```

## VectorDB

### 功能简介
对 Milvus 向量数据库进行增删查改操作。

### 输入参数
根据 `function_name` 不同需要提供相应参数：
- `create_collection`：`collection_name` (str), `dimension` (int)
- `drop_collection`：`collection_name` (str)
- `create_index`：`collection_name` (str), `index_params` (dict，可选)
- `insert_vector`：`collection_name` (str), `vectors` (list), `contents` (list), `labels` (list，可选), `partition_name` (str, 默认 `_default`)
- `search_vector`：`collection_name` (str), `query_vector` (list), `top_k` (int), `partition_name` (str, 默认 `_default`), `expr` (str，可选)
- `delete_vector`：`collection_name` (str), `vector_id` (int)

### 输出参数
各操作返回值不同，如 `insert_vector` 返回插入后的 ID 列表，`search_vector` 返回匹配结果列表。

### 功能说明
实例化 `VectorDB()` 后通过 `vec_ops(function_name, **kwargs)` 调用具体操作。常见流程包括创建集合、写入向量、搜索以及删除等。

### 示例
```python
from core.Context import Context
from coper.VectorDB import VectorDB
import numpy as np
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    vec_ops = VectorDB()
    vec_ops("create_collection", collection_name="demo", dimension=8).result()
    ids = vec_ops(
        "insert_vector",
        collection_name="demo",
        vectors=np.random.random((2,8)).tolist(),
        contents=["doc1","doc2"],
        labels=["a","b"]
    ).result()
    results = vec_ops(
        "search_vector",
        collection_name="demo",
        query_vector=np.random.random(8).tolist(),
        top_k=1
    ).result()
    print(ids, results)
```

## Minio

### 功能简介
封装 MinIO 客户端，用于对象存储的读写及桶管理。

### 输入参数
`compute(function_name, **kwargs)` 根据不同的 `function_name` 需要提供参数：
- `write`：`bucket` (str), `object_name` (str), `data` (bytes 或 str)
- `read`：`bucket` (str), `object_name` (str), `output_format` ("bytes" 或 "base64", 默认 "bytes")
- `delete`：`bucket` (str), `object_name` (str)
- `make_bucket`：`bucket` (str)
- `delete_bucket`：`bucket` (str)

### 输出参数
根据操作返回布尔值、字节数据或路径字典等。

### 功能说明
在 `Context` 环境中自动获得 MinIO 连接。常见用法包括创建桶、写入文件、读取文件或删除对象等。

### 示例
```python
from core.Context import Context
from coper.Minio import Minio
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    io = Minio()
    io("make_bucket", bucket="demo-bucket")
    io("write", bucket="demo-bucket", object_name="hello.txt", data=b"Hello")
    data = io("read", bucket="demo-bucket", object_name="hello.txt").result()
    print(data)
    io("delete", bucket="demo-bucket", object_name="hello.txt")
    io("delete_bucket", bucket="demo-bucket")
```

## TTS

### 功能简介
利用 MiniMax API 将文本转换为语音，并将音频文件写入 MinIO。

### 输入参数
- `text` (str)：待合成的文本。
- `minio_path` (dict)：目标存储路径，格式 `{"bucket": "名称", "object_name": "文件名"}`。
- `model` (str)：语音模型，默认 `speech-02-hd`。
- `voice_id` (str)：发音人 ID，默认 `Boyan_new_platform`。
- `speed` (int)：语速，默认 1。
- 其余参数如 `pitch`、`volume`、`emotion`、`sample_rate` 等同 `TTS.compute` 定义。

### 输出参数
字典结构：
- `success` (bool)：是否合成成功。
- `minio_path` (dict)：实际写入的对象路径。
- `message` (str)：状态说明或错误原因。

### 功能说明
调用成功后会把生成的音频文件写入指定 MinIO 路径，可根据返回信息确认结果。

### 示例
```python
from core.Context import Context
from coper.TTS import TTS
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    tts = TTS()
    res = tts("你好，世界！", minio_path={"bucket": "demo", "object_name": "hello.mp3"}).result()
    print(res)
```

## Service

### 功能简介
`Service` 是统一的调用接口，通过 RabbitMQ 将请求发送给后台服务并等待结果返回。

### 输入参数
实例化时仅需提供服务标识：
- `service_id` (str)：待调用的服务 ID。
调用时根据具体服务的定义传递参数。

### 输出参数
返回数据由服务端决定；若服务出现异常，会将异常信息转发给调用方。

### 功能说明
在 `Context` 环境内创建 `Service(service_id)`，然后像函数一样调用即可。组件会自动完成消息队列通信及结果解析。

### 通用示例
```python
from core.Context import Context
from coper.Service import Service
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    svc = Service("local-web-search")
    res = svc("AgentHub", engine="google", max_results=3).result()
    for item in res:
        print(item["title"], item["url"])
```

### Code Sandbox 服务

#### 功能简介
在隔离的 Docker 环境中编译并执行代码，输入和输出文件均通过 MinIO 存储。

#### 输入参数
- `source_file` (dict)：源码压缩包的 MinIO 路径。
- `data_file` (dict)：可选，输入数据压缩包路径。
- `command_file` (dict)：包含运行指令的压缩包路径。
- `output_file` (dict)：结果输出的目标 MinIO 路径。
- `execution_timeout` (int, 默认 `60`)：运行超时时间，单位秒。
- `execution_memory` (int, 默认 `256`)：允许使用的内存上限（MB）。
- `sandbox_template` (str, 默认 `"advanced"`)：编译/运行所用的模板名称。

#### 输出参数
返回字典，包含 `compilation` 与 `running` 的执行结果；若出现错误会提供 `error` 与 `error_msg` 信息，同时在 `output_file` 指定位置生成归档。

#### 功能说明
需先运行 `service/deploy.py install code-sandbox` 和 `service/deploy.py start code-sandbox sandbox` 以部署服务，之后通过 `Service("code-sandbox")` 调用。

#### 示例
```python
with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    sandbox = Service("code-sandbox")
    result = sandbox(
        source_file={"bucket": "demo", "object_name": "src.zip"},
        data_file={"bucket": "demo", "object_name": "data.zip"},
        command_file={"bucket": "demo", "object_name": "cmd.zip"},
        output_file={"bucket": "demo", "object_name": "out.zip"},
        execution_timeout=60,
        execution_memory=512,
        sandbox_template="python-3.12",
    ).result()
    print(result)
```

### Local Web Search 服务

#### 功能简介
调用本地浏览器进行网页搜索，并将结果页面转换为 Markdown 文本。

#### 输入参数
- `keywords` (str)：搜索关键词。
- `engine` (str, 默认 `"google"`)：要使用的搜索引擎。
- `max_results` (int, 默认 `5`)：返回结果数量。

#### 输出参数
列表，每个元素包含:
- `title` (str) - 结果标题。
- `url` (str) - 网页地址。
- `content` (str) - 页面内容 Markdown。

#### 功能说明
部署并启动服务：
```bash
python service/deploy.py install local-web-search
python service/deploy.py start local-web-search
```
随后即可使用 `Service("local-web-search")` 调用。

#### 示例
```python
with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    search = Service("local-web-search")
    results = search("AgentHub", engine="brave", max_results=3).result()
    for r in results:
        print(r["title"], r["url"])
```

### OCR Service 服务

#### 功能简介
调用OCR服务，识别文字

#### 输入参数
- `bucket` (str)：Minio的桶名称。
- `object_name` (str)：待识别的文件文件名。

#### 输出参数
列表，每个元素包含:
- `text` (str) - 识别出的文本内容

参考网页：https://paddlepaddle.github.io/PaddleOCR/main/version3.x/pipeline_usage/OCR.html#22-python

#### 功能说明
部署并启动服务：
```bash
cd service/ocr-service
python ../deploy.py install ocr-service
python ../deploy.py start ocr-service
```
随后即可使用 `Service("ocr-service")` 调用。

#### 示例
```python
with Context(task_id=str(uuid.uuid4())):
    ocr = Service("ocr-service")
    test_bucket = "test-bucket"
    test_object = "test_ocr.pdf"
    result = ocr(test_bucket, test_object).result()
    print(result)
    test_object = "test_ocr.jpg"
    result = ocr(test_bucket, test_object).result()
    print(result)
```
