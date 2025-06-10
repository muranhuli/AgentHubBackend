import io
import os
import zipfile
from pathlib import Path

import msgpack
import zlib

# pack 时的钩子
def cr_default(obj):
    from core.ComputableResult import ComputableResult
    if isinstance(obj, ComputableResult):
        return {
            "__type__": "ComputableResult",
            "exec_id": obj.exec_id
        }
    # 其他类型交给 msgpack 处理
    return obj

# unpack 时的钩子
def cr_object_hook(obj):
    from core.ComputableResult import ComputableResult
    if obj.get("__type__") == "ComputableResult":
        exec_id = obj["exec_id"]
        return ComputableResult(exec_id)
    return obj

def serialize(obj, compress=False) -> tuple[bytes, str]:
    try:
        packed = msgpack.packb(obj, use_bin_type=True, default=cr_default)
        data   = zlib.compress(packed) if compress else packed
        return data, data.decode('latin1')
    except Exception as e:
        raise ValueError(f"Serialization failed: {e}")

def deserialize(s: bytes | str, compressed=False):
    try:
        data = s if isinstance(s, bytes) else s.encode('latin1')
        raw  = zlib.decompress(data) if compressed else data
        return msgpack.unpackb(raw, raw=False, object_hook=cr_object_hook)
    except Exception as e:
        raise ValueError(f"Deserialization failed: {e}")


def zip_directory_to_bytes(directory_path):
    """
    将目录中的所有文件（包括子目录）打包成 ZIP，并返回 ZIP 的字节流

    Args:
        directory_path (str): 要打包的目录路径

    Returns:
        bytes: ZIP 文件的字节流

    Raises:
        FileNotFoundError: 如果目录不存在
    """
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"目录不存在: {directory_path}")

    # 创建一个内存中的字节流缓冲区
    zip_buffer = io.BytesIO()

    # 使用 zipfile 创建 ZIP 文件
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 遍历目录中的所有文件和子目录
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算 ZIP 中的相对路径（去掉目录路径前缀）
                arcname = os.path.relpath(file_path, start=directory_path)
                # 将文件添加到 ZIP
                zipf.write(file_path, arcname)

    # 获取 ZIP 字节流
    zip_bytes = zip_buffer.getvalue()
    zip_buffer.close()

    return zip_bytes


def unzip_bytes_to_directory(zip_bytes, target_dir, flatten=False, overwrite=False):
    """
    将 ZIP 字节流解压到目标目录

    Args:
        zip_bytes (bytes): ZIP 文件的字节流
        target_dir (str): 解压目标目录路径
        flatten (bool): 是否平铺所有文件到目标目录（忽略 ZIP 中的目录结构）
        overwrite (bool): 是否覆盖已存在的文件

    Returns:
        list: 解压后的文件路径列表

    Raises:
        ValueError: 如果 ZIP 数据无效
        FileExistsError: 如果文件已存在且 overwrite=False
    """
    # 验证目标目录
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # 安全校验：确保目标目录不是根目录或系统关键目录
    if Path(target_dir).parent == Path(target_dir):
        raise ValueError("Dangerous target directory: cannot extract to root or system critical directory")

    # 读取 ZIP 字节流
    zip_buffer = None
    try:
        zip_buffer = io.BytesIO(zip_bytes)
        extracted_files = []

        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # 校验 ZIP 中所有文件路径的安全性
            for file_info in zip_ref.infolist():
                # 防止 ZIP 路径穿越攻击（如包含 ../ 的恶意路径）
                dest_path = os.path.join(target_dir, file_info.filename)
                dest_path = os.path.normpath(dest_path)

                if not dest_path.startswith(os.path.abspath(target_dir) + os.sep):
                    raise ValueError(f"Dangerous file path in ZIP: {file_info.filename}")

                # 处理平铺模式
                if flatten:
                    dest_path = os.path.join(target_dir, os.path.basename(file_info.filename))

                # 检查文件是否已存在
                if os.path.exists(dest_path) and not overwrite:
                    raise FileExistsError(f"File already exists: {dest_path}")

                # 创建目录结构（非平铺模式时）
                if not flatten:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # 如果是文件则解压
                if not file_info.is_dir():
                    with open(dest_path, 'wb') as f:
                        f.write(zip_ref.read(file_info.filename))
                    extracted_files.append(dest_path)

        return extracted_files

    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP data provided")
    finally:
        if zip_buffer:
            zip_buffer.close()