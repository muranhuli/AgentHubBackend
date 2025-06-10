
sandbox_templates = {
    "gcc-13.3-cpp-std_17-O2":{
        "compilation":{
            "exe_path": "/opt/gcc/13.3.0/bin/g++",
            "exe_args": [
                "-Wl,-rpath",
                "-Wl,/opt/gcc/13.3.0/lib64",
                "--define-macro=ONLINE_JUDGE",
                "--optimize=2",
                "--no-warnings",
                "-fmax-errors=3",
                "--std=c++17",
                "-static",
                "--output=/workspace/run/main",
                "/workspace/source/main.cc"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "c_cpp",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },
    },
    "gcc-13.3-cpp-std_11-O2":{
        "compilation":{
            "exe_path": "/opt/gcc/13.3.0/bin/g++",
            "exe_args": [
                "-Wl,-rpath",
                "-Wl,/opt/gcc/13.3.0/lib64",
                "--define-macro=ONLINE_JUDGE",
                "--optimize=2",
                "--no-warnings",
                "-fmax-errors=3",
                "--std=c++11",
                "-static",
                "--output=/workspace/run/main",
                "/workspace/source/main.cc"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "c_cpp",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },
    },
    "gcc-13.3-c-std_11-O2":{
        "compilation":{
            "exe_path": "/opt/gcc/13.3.0/bin/gcc",
            "exe_args": [
                "-Wl,-rpath",
                "-Wl,/opt/gcc/13.3.0/lib64",
                "--define-macro=ONLINE_JUDGE",
                "--optimize=2",
                "--no-warnings",
                "-fmax-errors=3",
                "--std=c11",
                "-static",
                "--output=/workspace/run/main",
                "/workspace/source/main.c"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "c_cpp",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },

    },
    "gcc-13.3-c-std_17-O2":{
        "compilation":{
            "exe_path": "/opt/gcc/13.3.0/bin/gcc",
            "exe_args": [
                "-Wl,-rpath",
                "-Wl,/opt/gcc/13.3.0/lib64",
                "--define-macro=ONLINE_JUDGE",
                "--optimize=2",
                "--no-warnings",
                "-fmax-errors=3",
                "--std=c17",
                "-static",
                "--output=/workspace/run/main",
                "/workspace/source/main.c"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "c_cpp",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },

    },
    "rust-1.78":{
        "compilation":{
            "exe_path": "/opt/rust/1.78.0/bin/rustc",
            "exe_args": [
                "-C",
                "opt-level=2",
                "--cfg",
                "ONLINE_JUDGE",
                "-o",
                "/workspace/run/main",
                "/workspace/source/main.rs"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },
    },
    "rust-1.84":{
        "compilation":{
            "exe_path": "/opt/rust/1.84.0/bin/rustc",
            "exe_args": [
                "-C",
                "opt-level=2",
                "--cfg",
                "ONLINE_JUDGE",
                "-o",
                "/workspace/run/main",
                "/workspace/source/main.rs"
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 512 * 1024 * 1024,  # 512 MiB
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/workspace/run/main",
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        },
    },
    "pypy-3.10":{
        "run": {
            "exe_path": "/opt/pypy/3.10/bin/pypy3",
            "exe_args": [
                "/workspace/source/main.py"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }

    },
    "pypy-3.11":{
        "run": {
            "exe_path": "/opt/pypy/3.11/bin/pypy3",
            "exe_args": [
                "/workspace/source/main.py"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }
    },
    "python-3.12":{
        "run": {
            "exe_path": "/opt/python/3.12/bin/python3",
            "exe_args": [
                "/workspace/source/main.py"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }

    },
    "python-3.13":{
        "run": {
            "exe_path": "/opt/python/3.13/bin/python3",
            "exe_args": [
                "/workspace/source/main.py"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "seccomp_rules": "general",
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }

    },
    "java-8":{
        "compilation":{
            "exe_path": "/opt/java/openjdk8/bin/javac",
            "exe_args": [
                "-J-Xmx1g",
                "-J-XX:ParallelGCThreads=1",
                "-J-XX:CICompilerCount=2",
                "/workspace/source/Main.java",
                "-encoding",
                "UTF-8",
                "-d",
                "/workspace/run",
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 0,
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/opt/java/openjdk8/bin/java",
            "exe_args": [
                "-Dfile.encoding=UTF-8",
                "-Xmx{}m",
                "-XX:ParallelGCThreads=1",
                "-Djava.security.manager",
                "-Djava.awt.headless=true",
                "Main"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }
    },
    "java-17":{
        "compilation":{
            "exe_path": "/opt/java/openjdk17/bin/javac",
            "exe_args": [
                "-J-Xmx1g",
                "-J-XX:ParallelGCThreads=1",
                "-J-XX:CICompilerCount=2",
                "/workspace/source/Main.java",
                "-encoding",
                "UTF-8",
                "-d",
                "/workspace/run",
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 0,
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/opt/java/openjdk17/bin/java",
            "exe_args": [
                "-Dfile.encoding=UTF-8",
                "-Xmx{}m",
                "-XX:ParallelGCThreads=1",
                "-Djava.awt.headless=true",
                "Main"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }

    },
    "java-21":{
        "compilation":{
            "exe_path": "/opt/java/openjdk21/bin/javac",
            "exe_args": [
                "-J-Xmx1g",
                "-J-XX:ParallelGCThreads=1",
                "-J-XX:CICompilerCount=2",
                "/workspace/source/Main.java",
                "-encoding",
                "UTF-8",
                "-d",
                "/workspace/run",
            ],
            "max_cpu_time": 8000,
            "max_real_time": 10000,
            "max_memory": 0,
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/compilation-sandbox-log.txt",
            "output_path": "/workspace/run/compilation-output.txt",
        },
        "run":{
            "exe_path": "/opt/java/openjdk21/bin/java",
            "exe_args": [
                "-Dfile.encoding=UTF-8",
                "-Xmx{}m",
                "-XX:ParallelGCThreads=1",
                "-Djava.awt.headless=true",
                "Main"
            ],
            "input_path": "/workspace/data/input",
            "output_path": "/workspace/output/output",
            "max_output_size": 32 * 1024 * 1024,  # 32 MiB
            "log_path": "/workspace/run/run-sandbox-log.txt",
        }
    },
}
