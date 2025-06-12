import uuid

from coper.Minio import Minio
from coper.Service import Service
from core.Context import Context

if __name__ == "__main__":
    task_id = str(uuid.uuid4())
    print("Task ID: {}".format(task_id))
    with Context(task_id=task_id):

        io = Minio()

        code_sandbox = Service("interactive-sandbox")
        # Create a temporary directory for the sandbox
        state, session_id = code_sandbox("create_session").result()
        print("State: {}, Session ID: {}".format(state, session_id))
        state, (out, err, code) = code_sandbox("exec", session_id, "ls").result()
        print("State: {}, Output: {}, Error: {}, Code: {}".format(state, out, err, code))

        source_code = """import uuid

if __name__ == "__main__":
    from core.Context import Context
    from coper.basic_ops import Mul
    from coper.basic_ops import Add
    with Context(task_id=str(uuid.uuid4())):
        mul = Mul()
        add = Add()
        a = mul(3, 2)
        b = add(3, 2)
        c = add(a, b)
        print(f"{c.result()}")
        with open("result.txt", "w") as f:
            f.write(f"{c.result()}")
"""
        bucket = io("make_bucket", "test-bucket")
        file = io("write", bucket, "agent.py", source_code)
        state, msg = code_sandbox("upload_file", session_id, file).result()
        print("State: {}, Message: {}".format(state, msg))
        state, (out, err, code) = code_sandbox("exec", session_id, "python agent.py").result()
        print("State: {}, Output: {}, Error: {}, Code: {}".format(state, out, err, code))
        download_file = code_sandbox("download_file", session_id, {
            "bucket": bucket,
            "object_name": "result.txt"
        })
        res_data = io("read_s3", download_file).result()
        print("Result Data: {}".format(res_data))
        state, msg = code_sandbox("close_session", session_id).result()
        print("State: {}, Message: {}".format(state, msg))

"""
EXAMPLE OUTPUT:
Task ID: f1d2785b-0256-43a7-9c07-d0ecc844f0cf
State: True, Session ID: 00346d61893c434dbc6677dc43186013
State: True, Output: coper
core
middleware
requirements.txt
, Error: None, Code: 0
State: True, Message: File uploaded successfully
State: True, Output: 11
, Error: None, Code: 0
Result Data: b'11'
State: True, Message: Session closed successfully
"""



