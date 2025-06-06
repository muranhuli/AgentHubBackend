import asyncio
import json
import subprocess
import time
import zipfile
from pathlib import Path

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.Service import Service
from core.Context import Context
from coper.MinioRead import MinioRead

class CodeSandbox(Service):

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = json.loads(open(config_path).read())
        super().__init__(config["service_id"])
        self.fread = None

    def initialize(self):
        self.fread = MinioRead()
        pass

    def get_file(self, f):
        return self.fread(f["bucket"], f["key"])


    def compute(
            self,
            source_file,
            data_file,
            command_file,
            execution_timeout=60,
            execution_memory=256, # in MB
            sandbox_template="advanced",
    ):
        pass

