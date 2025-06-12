from pymilvus import (
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)
from typing import Optional
from core.Computable import Computable



class VectorDBOperations:
    def __init__(self):
        pass

    def create_collection(self, collection_name: str, dimension: int):
        if utility.has_collection(collection_name, using="agent_vectorDB"):
            print(f"[WARNING] Collection '{collection_name}' 已存在，跳过创建")
            return
        id_field = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
        vec_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
        content_field = FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10240)
        label_field = FieldSchema(name="label", dtype=DataType.VARCHAR, max_length=1024)

        schema = CollectionSchema(fields=[id_field, vec_field, content_field, label_field])
        Collection(name=collection_name, schema=schema, using="agent_vectorDB")
        print(f"[INFO] Collection '{collection_name}' 创建成功，向量维度 = {dimension}")

    def drop_collection(self, collection_name: str):
        if utility.has_collection(collection_name, using="agent_vectorDB"):
            utility.drop_collection(collection_name, using="agent_vectorDB")
            print(f"[INFO] Collection '{collection_name}' 已删除")
        else:
            print(f"[WARNING] Collection '{collection_name}' 不存在，无法删除")

    def create_index(self, collection_name: str, index_params: Optional[dict] = None):
        if index_params is None:
            index_params = {
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
                "metric_type": "L2"
            }
        collection = Collection(name=collection_name, using="agent_vectorDB")
        collection.create_index(field_name="embedding", index_params=index_params)
        print(f"[INFO] Collection '{collection_name}' 向量字段 'embedding' 已创建索引：{index_params}")

    def insert_vector(self, collection_name: str, vectors: list, contents: list, labels: Optional[list] = None, partition_name: str = "_default"):
        collection = Collection(name=collection_name, using="agent_vectorDB")
        if partition_name != "_default":
            if partition_name not in [p.name for p in collection.partitions]:
                collection.create_partition(partition_name)

        if labels is None:
            labels = [""] * len(vectors)
        assert len(vectors) == len(labels), "向量和标签数量必须一致"
        assert len(vectors) == len(contents), "向量和内容数量必须一致"
        insert_result = collection.insert([vectors, contents, labels], partition_name=partition_name)
        collection.flush()
        ids = insert_result.primary_keys
        print(f"[INFO] 插入 {len(vectors)} 条记录，ID 范围：{ids[0]} ~ {ids[-1]}，分区：{partition_name}")
        return list(ids)

    def search_vector(self, collection_name: str, query_vector: list, top_k: int = 3, partition_name: str = "_default", expr: Optional[str] = None):
        collection = Collection(name=collection_name, using="agent_vectorDB")
        collection.load(partition_names=[partition_name])
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "content", "label"],
            partition_names=[partition_name],
            expr=expr  # 条件表达式
        )
        print(f"[INFO] 检索 Collection '{collection_name}'（分区 '{partition_name}'），top_k = {top_k}, 过滤条件：{expr}")
        return [(hit.entity.get("id"), hit.entity.get("content"), hit.entity.get("label"), hit.distance) for hit in results[0]] # type: ignore


    def delete_vector(self, collection_name: str, vector_id: int):
        collection = Collection(name=collection_name, using="agent_vectorDB")
        collection.delete(f"id in [{vector_id}]")
        collection.flush()
        print(f"[INFO] 已请求删除 ID = {vector_id} 的向量记录")
        

class VectorDB(Computable):
    """Perform operations on Milvus vector database."""

    def __init__(self):
        super().__init__()
        self.vector_db = VectorDBOperations()

    def compute(self, function_name: str, **kwargs) -> object:
        """Dispatch to the underlying vector database operations.

        Args:
            function_name: Name of the operation.
            **kwargs: Parameters for that operation.

        Returns:
            The result returned by the operation.
        """
        # 操作路由字典
        operation_map = {
            "create_collection": self.vector_db.create_collection,
            "drop_collection": self.vector_db.drop_collection,
            "create_index": self.vector_db.create_index,
            "insert_vector": self.vector_db.insert_vector,
            "search_vector": self.vector_db.search_vector,
            "delete_vector": self.vector_db.delete_vector
        }
        
        if not function_name:
            raise ValueError("必须提供操作类型作为第一个参数")

        if function_name not in operation_map:
            supported_ops = list(operation_map.keys())
            raise ValueError(f"不支持的操作 '{function_name}'。支持的操作: {supported_ops}")

        try:
            # 调用对应的方法
            return operation_map[function_name](**kwargs)
        except Exception as e:
            print(f"[ERROR] 操作 '{function_name}' 执行失败: {str(e)}")
            raise
