import json
import sys
import os


import docker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.Service import Service
from coper.MinioRead import MinioRead
from coper.MinioWrite import MinioWrite


class CodeSandbox(Service):

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = json.loads(open(config_path).read())
        super().__init__(config["service_id"])
        self.fread = None
        self.fwrite = None

    def initialize(self):
        self.fread = MinioRead()
        self.fwrite = MinioWrite()

    def __get_file(self, f):
        return self.fread(f["bucket"], f["object_name"])

    def compute(
            self,
            source_file,
            data_file,
            command_file,
            execution_timeout=60,
            execution_memory=256,  # in MB
            sandbox_template="advanced",
    ):
        pass










