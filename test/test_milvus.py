from coper.VectorDB import VectorDB
import numpy as np
import random
from core.Context import Context
import uuid

if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        # 使用 VectorDBComputable 类
        vec_ops = VectorDB()

        # 1. 创建集合
        collection_name = "test_collection"
        dimension = 8
        vec_ops("drop_collection", collection_name=collection_name).result()  # 确保集合不存在
        vec_ops("create_collection", collection_name=collection_name, dimension=dimension).result()

        # 2. 插入之前先创建索引（也可以等数据插入再创建，但为了简洁，放在这里）
        #    - 默认索引类型：IVF_FLAT；nlist=128；度量方式：L2
        vec_ops("create_index", collection_name=collection_name).result()

        # 3. 生成并插入 5 条随机向量
        random.seed(42)
        np.random.seed(42)
        labels = [f"0" for i in range(5)]
        contents = [f"content_{i}" for i in range(5)]
        vectors_to_insert = np.random.random((5, dimension)).tolist()
        inserted_ids = vec_ops("insert_vector", collection_name=collection_name, 
                               vectors=vectors_to_insert, contents=contents, labels=labels).result()

        print(inserted_ids)
    
        # 4. 以第 3 条向量作为查询向量，执行检索
        query_vec = vectors_to_insert[2]
        top_k = 10
        search_results = vec_ops("search_vector", collection_name=collection_name, query_vector=query_vec, 
                                 top_k=top_k, expr='label == "0"').result()
        print("首次检索结果：")
        for idx, content, label, dist in search_results:
            print(f"  id = {idx}，content = {content}，label = {label}，distance = {dist:.4f}")

        # 5. 删除 id = 1
        delete_id = inserted_ids[0]
        vec_ops("delete_vector", collection_name=collection_name, vector_id=delete_id).result()

        # 6. 再次检索，观察结果变化
        search_results_after_delete = vec_ops("search_vector", collection_name=collection_name, query_vector=query_vec, top_k=top_k).result()
        print("删除后再次检索结果：")
        for idx, content, label, dist in search_results_after_delete:
            print(f"  id = {idx}，content = {content}，label = {label}，distance = {dist:.4f}")
        # 7. 删除集合
        vec_ops("drop_collection", collection_name=collection_name).result()