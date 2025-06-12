# AgentHub Backend - LLM and Embedding Usage Guide

This guide explains how to use within the AgentHub Backend. All components must be used within the `Context` manager.

## Environment Configuration

Before using the components, ensure you have a `.env` file in the project root directory with the necessary API keys and base URLs.

**For LLM (Example using ARK - ByteDance Doubao):**

```env
ARK_API_KEY=your-ark-api-key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Add other providers as needed, e.g., SDU, VLLM
# SDU_API_KEY=your-sdu-api-key
# SDU_BASE_URL=http://your-sdu-server/v1
# VLLM_API_KEY=your-vllm-api-key
# VLLM_BASE_URL=http://your-vllm-server:8000/v1
```

**For Embedding:**

```env
EMBEDDING_URL=https://your-embedding-api-endpoint
EMBEDDING_API_KEY=your-embedding-api-key
EMBEDDING_MODEL=your-embedding-model-name
```

## Core Usage Pattern

1. **Import necessary classes:** `Context`, `LLM`, `Embedding`.
2. **Wrap operations in `Context`:** All component calls must be within a `with Context(...) as ctx:` block.
3. **Instantiate components:** Create instances of `LLM` or `Embedding`.
4. **Call components:** Invoke the component instance directly with input parameters.
5. **Get results:** Use `.result()` to retrieve the output.

## 1. LLM - Large Language Model

The `LLM` component allows you to interact with various large language models.

### Initialization

```python
from core.Context import Context
from coper.LLM import LLM
import uuid

# Example: Initialize LLM with Doubao model via ARK provider
with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    llm = LLM(model_name="doubao-1-5-thinking-pro-250415", custom_provider="ARK")
    # Other examples:
    # llm = LLM(model_name="DeepSeek-R1", custom_provider="SDU")
    # llm = LLM(model_name="Qwen3-32B", custom_provider="VLLM")
```

### Basic Invocation

```python
# Continued from above
prompt = "Explain the theory of relativity in simple terms."
response = llm(prompt).result()
print(response)
# The 'response' will be a dictionary, typically with a 'content' key for the main text.
```

### Structured Output

You can request the LLM to return a response that conforms to a specific Pydantic model schema.

```python
from pydantic import BaseModel, Field

class CodeExplanation(BaseModel):
    code: str = Field(description="The generated code snippet.")
    explanation: str = Field(description="An explanation of the code.")

# Continued from above
code_prompt = "Write a Python function to calculate a factorial and explain it."

# Pass the Pydantic model's JSON schema
structured_response = llm(code_prompt, CodeExplanation.model_json_schema()).result()

print(structured_response)
```

The result for structured output will be under the `structured_output` key in the response dictionary.

## 2. Embedding

The `Embedding` component is used to generate vector embeddings for given text(s).

### Embedding Initialization

```python
from core.Context import Context
from coper.Embedding import Embedding
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    embedding_service = Embedding()
```

### Generating Embeddings

**Single Text:**

```python
# Continued from above
text_to_embed = "Hello, world!"
single_vector = embedding_service(text_to_embed).result()
# print(f"Embedding for single text: {single_vector}")
# 'single_vector' will be a list of floats.
```

**Batch of Texts:**

```python
# Continued from above
texts_to_embed = ["This is the first document.", "This is the second document."]
batch_vectors = embedding_service(texts_to_embed).result()
# print(f"Embeddings for batch of texts: {batch_vectors}")
# 'batch_vectors' will be a list of lists of floats.
```

This covers the basic usage for `LLM` and `Embedding` components. Remember to always operate within the `Context` manager.

## 3. VectorDB - Vector Database

The `VectorDB` component provides an interface to interact with a vector database, allowing for creation of collections, insertion of vectors, searching, and deletion.

### VectorDB Initialization and Basic Operations

```python
from coper.VectorDB import VectorDB
import numpy as np
import random
from core.Context import Context
import uuid

if __name__ == "__main__": # This is typically how you'd run a script.
                           # In a real application, you might integrate this into a larger flow.
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        vec_ops = VectorDB()

        collection_name = "my_test_collection"
        dimension = 8  # Example dimension

        # 1. Create a collection (ensure it's dropped first if it might exist)
        vec_ops("drop_collection", collection_name=collection_name).result()
        vec_ops("create_collection", collection_name=collection_name, dimension=dimension).result()
        print(f"Collection '{collection_name}' created.")

        # 2. Create an index (optional, can be done after insertion)
        # Default index: IVF_FLAT, nlist=128, metric: L2
        vec_ops("create_index", collection_name=collection_name).result()
        print("Index created on collection.")

        # 3. Insert vectors
        random.seed(42)
        np.random.seed(42)
        num_vectors = 5
        labels = [f"label_{i % 2}" for i in range(num_vectors)] # Example labels
        contents = [f"Document content {i}" for i in range(num_vectors)]
        vectors_to_insert = np.random.random((num_vectors, dimension)).tolist()
        
        inserted_ids = vec_ops("insert_vector", 
                               collection_name=collection_name, 
                               vectors=vectors_to_insert, 
                               contents=contents, 
                               labels=labels).result()
        print(f"Inserted vectors with IDs: {inserted_ids}")

        # 4. Search vectors
        # Using the third inserted vector as the query vector
        query_vec = vectors_to_insert[2] 
        top_k = 3
        # Example of searching with a filter expression
        search_results = vec_ops("search_vector", 
                                 collection_name=collection_name, 
                                 query_vector=query_vec, 
                                 top_k=top_k,
                                 expr='label == "label_0"').result() 
                                 # expr is optional, searches all if not provided or if filter is not needed
        
        print("\\nSearch results (label == 'label_0'):")
        if search_results:
            for idx, content, label, dist in search_results:
                print(f"  ID: {idx}, Content: '{content}', Label: {label}, Distance: {dist:.4f}")
        else:
            print("  No results found for the given filter.")

        # Search without filter
        search_results_all = vec_ops("search_vector", 
                                     collection_name=collection_name, 
                                     query_vector=query_vec, 
                                     top_k=top_k).result()
        print("\\nSearch results (all):")
        if search_results_all:
            for idx, content, label, dist in search_results_all:
                print(f"  ID: {idx}, Content: '{content}', Label: {label}, Distance: {dist:.4f}")
        else:
            print("  No results found.")

        # 5. Delete a vector
        if inserted_ids:
            delete_id = inserted_ids[0] # Example: delete the first inserted vector
            vec_ops("delete_vector", collection_name=collection_name, vector_id=delete_id).result()
            print(f"\\nDeleted vector with ID: {delete_id}")

            # Verify by searching again
            search_results_after_delete = vec_ops("search_vector", 
                                                 collection_name=collection_name, 
                                                 query_vector=query_vec, 
                                                 top_k=num_vectors).result() # search more to see effect
            print("Search results after deletion:")
            if search_results_after_delete:
                for idx, content, label, dist in search_results_after_delete:
                    print(f"  ID: {idx}, Content: '{content}', Label: {label}, Distance: {dist:.4f}")
            else:
                print("  No results found.")
        
        # 6. Drop the collection
        vec_ops("drop_collection", collection_name=collection_name).result()
        print(f"\\nCollection '{collection_name}' dropped.")

```

## 4. TTS - Text-to-Speech

The `TTS` component converts text to speech using the MiniMax TTS API, allowing you to generate high-quality audio files from text input.

We use MiniMax's services (<https://www.minimaxi.com>).

### Environment Configuration

Add the following to your `.env` file:

```env
MINIMAX_GROUP_ID=your-minimax-group-id
MINIMAX_API_KEY=your-minimax-api-key
```

### Output Format

The TTS component returns a dictionary with the following structure:

```python
{
    'success': bool,      # Whether the operation succeeded
    'minio_path': {
        'bucket': str,
        'object_name': str
    },
    'message': str        # Success message or error description
}
```

This covers the basic usage of the TTS component.

## 5. Minio - Object Storage

The `Minio` operator is a simple wrapper around the MinIO SDK for reading and writing objects.

```python
from core.Context import Context
from coper.Minio import Minio
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    io = Minio()

    # Create a bucket
    io('make_bucket', bucket='demo-bucket')

    # Write data
    io('write', bucket='demo-bucket', object_name='hello.txt', data=b'Hello')

    # Read as bytes
    data = io('read', bucket='demo-bucket', object_name='hello.txt').result()

    # Read an image as base64 (for LLM vision models)
    img = io('read', bucket='demo-bucket', object_name='img.png', output_format='base64').result()

    # Delete file and bucket
    io('delete', bucket='demo-bucket', object_name='hello.txt')
    io('delete_bucket', bucket='demo-bucket')
```

## 6. Service - Invoke Registered Services

`Service` lets you call a background service via RabbitMQ. Provide the service ID when creating the instance.

```python
from core.Context import Context
from coper.Service import Service
import uuid

with Context(task_id=str(uuid.uuid4().hex)) as ctx:
    search = Service('local-web-search')
    results = search('AgentHub', engine='google', max_results=3).result()
    for item in results:
        print(item['title'], item['url'])
```

## 7. Built-in Services

Two services are included under the `service/` directory. Use `service/deploy.py` to install, start or remove them.

### Code Sandbox

Runs code snippets securely inside Docker containers.

```bash
# build images and prepare
python service/deploy.py install code-sandbox

# start the service ("sandbox" or "interactive" mode)
python service/deploy.py start code-sandbox sandbox
```

Inputs and outputs are defined in `service/code-sandbox/config.json`.

### Local Web Search

Performs a local browser search using Playwright and returns markdown archives of the pages.

```bash
python service/deploy.py install local-web-search
python service/deploy.py start local-web-search
```

The input/output schema is described in `service/local-web-search/config.json`.
