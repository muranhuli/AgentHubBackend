import os
import urllib.parse
from pymilvus import connections
import redis
import pika
import contextvars
from dotenv import load_dotenv
from minio import Minio

# Global ContextVar for storing the current execution context
_current_ctx = contextvars.ContextVar("current_execution_context")


class Context:
    """
    Manages Redis and RabbitMQ connections.
    Establishes connections when entering the context and closes RabbitMQ connection on exit,
    resetting the global ContextVar.
    """

    def __init__(self, task_id=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, 'middleware', '.env')
        load_dotenv(dotenv_path=env_path)
        header_address = os.getenv("HEADER_ADDRESS")
        redis_port = os.getenv("REDIS_PORT")
        redis_pass = urllib.parse.quote(os.getenv("REDIS_PASSWORD"), safe='')
        rabbitmq_port = os.getenv("RABBITMQ_PORT")
        rabbitmq_user = os.getenv("RABBITMQ_USER")
        rabbitmq_pass = os.getenv("RABBITMQ_PASSWORD")
        minio_port = os.getenv("MINIO_API_PORT")
        minio_user = os.getenv("MINIO_ROOT_USER")
        minio_pass = os.getenv("MINIO_ROOT_PASSWORD")
        # Connect to Milvus VectorDB
        connections.connect(
            alias="agent_vectorDB",
            host=os.getenv("HEADER_ADDRESS"),
            port=os.getenv("MILVUS_PORT")
        )
        self.redis_url = f"redis://:{redis_pass}@{header_address}:{redis_port}/1"
        credentials = pika.PlainCredentials(
            username=rabbitmq_user,
            password=rabbitmq_pass,
        )
        self.amqp_para = pika.ConnectionParameters(
            host=header_address,
            port=int(rabbitmq_port),
            virtual_host="/",
            credentials=credentials,
        )
        self.queue = "runner_task_queue"
        self._redis = None
        self._connection = None
        self._channel = None
        self._minio = None
        self._token = None
        self.task_id = task_id
        self.init_task = None

        self.minio_endpoint = f"{header_address}:{minio_port}"
        self.minio_user = minio_user
        self.minio_pass = minio_pass

        init_task_lua_path = os.path.join(os.path.dirname(__file__), "init_task.lua")
        with open(init_task_lua_path, 'r', encoding="utf8") as _f:
            self._init_task_lua = _f.read()

    def __enter__(self):
        # Establish Redis connection
        self._redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
        self.init_task = self.redis.register_script(self._init_task_lua)
        # Establish RabbitMQ connection and channel
        self._connection = pika.BlockingConnection(self.amqp_para)
        self._channel = self._connection.channel()
        # Ensure the queue exists and is durable
        self._channel.queue_declare(queue=self.queue, durable=True)
        # Establish Minio client
        self._minio = Minio(
            self.minio_endpoint,
            access_key=self.minio_user,
            secret_key=self.minio_pass,
            secure=False,
        )

        # Set this context as the current one
        self._token = _current_ctx.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset ContextVar
        _current_ctx.reset(self._token)
        # Close RabbitMQ connection
        if self._connection and not self._connection.is_closed:
            self._connection.close()
        # Redis client manages connection pool automatically
        self._minio = None

    @property
    def redis(self) -> redis.Redis:
        if not self._redis:
            raise RuntimeError("Redis is not initialized. Use within an ExecutionContext.")
        return self._redis

    @property
    def channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        if not self._channel:
            raise RuntimeError("RabbitMQ channel is not initialized. Use within an ExecutionContext.")
        return self._channel

    @property
    def connection(self) -> pika.BlockingConnection:
        if not self._connection:
            raise RuntimeError("RabbitMQ connection is not initialized. Use within an ExecutionContext.")
        return self._connection

    @property
    def minio(self) -> Minio:
        if not self._minio:
            raise RuntimeError("Minio client is not initialized. Use within an ExecutionContext.")
        return self._minio

    @property
    def task(self):
        if self.task_id is None:
            raise RuntimeError("Task ID is not set. Use the `set_task` method to set a task ID.")
        return self.task_id

    def set_task(self, task_id):
        self.task_id = task_id


def get_context() -> Context:
    """
    Retrieve the current execution context. Raises an error if called outside an ExecutionContext.
    """
    ctx = _current_ctx.get(None)
    if ctx is None:
        raise RuntimeError("No active ExecutionContext. Use `with ExecutionContext(...) as ctx:`.")
    return ctx
