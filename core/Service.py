import json

from core.Computable import Computable
from core.Utils import deserialize


class Service(Computable):
    """
    Service类，用于定义一个第三方计算服务的基本框架。
    必须有一个 build.sh 脚本，用于构建服务的基本环境。
    通过环境变量，提供：
    1. WorkSpace: 工作目录，用于存放当前服务实例的运行数据
    2. HeaderAddress: 中心节点的地址（提供给 Service 类）
    3. AuthKey: 用于身份验证的密钥（提供给 Service 类）

    必须有一个 main.py 脚本，用于启动服务的运行。
    脚本中必须实例化一个 Service 的子类，并调用 service.run() 方法。

    Service 有心跳进程，负责注册与心跳。
    只有注册之后才能进行心跳（否则会返回未注册错误），之后会通过独立的进程进行心跳。心跳消失后，会自动清除注册的结果。
    在心跳时，如果发现未注册，会自动执行注册逻辑。

    如果 AuthKey 属于系统用户，则使用 service set 维护，否则使用 user_{user_id}_service set 维护当前的 service_id


    服务类，用于定义一个计算服务，其本质是一个具有状态的 Computable 对象，可以通过 prepare 方法准备计算环境，并在计算时使用。
    服务可以分布式的运行在任意的机器上，通过 RabbitMQ 获取输入数据，在计算完成之后，向指定的队列发送计算结果。
    """

    def __register(self):
        """
        注册服务到中心节点，使用 AuthKey 进行身份验证。
        如果注册成功，则返回 True，否则返回 False。
        """
        pass

    def __heartbeat(self):
        """
        心跳进程，负责定期向中心节点发送心跳信息。
        如果心跳消失，则自动清除注册的结果。
        """
        pass

    def initialize(self):
        raise NotImplementedError("Subclasses must implement the initialize method.")

    def __init__(self, service_id):
        super().__init__()
        self.service_id = service_id

    def _on_message(self, ch, method, properties, body):
        """
        处理接收到的消息。
        子类可以重写此方法以实现自定义的消息处理逻辑。
        """
        task = deserialize(body)
        self.ctx.set_task(task["task_id"])
        return_queue = task["return_queue"]
        args = task["args"]
        kwargs = task["kwargs"]
        rv = {}
        try:
            res = self.compute(*args, **kwargs)
        except Exception as e:
            import traceback
            stack = traceback.format_exc()
            rv["status"] = "error"
            rv["message"] = str(e)
            rv["stack"] = stack
        else:
            rv["status"] = "success"
            rv["result"] = res
        finally:
            self.redis.lpush(return_queue, json.dumps(rv))
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        self.initialize()
        queue_name = f"service.request.{self.service_id}"
        self.ch.queue_declare(queue=queue_name, durable=True)
        self.ch.basic_consume(
            queue=queue_name, on_message_callback=self._on_message
        )
        print("Service is running and waiting for messages...")
        self.ch.start_consuming()
