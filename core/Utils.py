import msgpack
import zlib

def serialize(obj, compress=False) -> tuple[bytes, str]:
    try:
        packed = msgpack.packb(obj, use_bin_type=True)
        data   = zlib.compress(packed) if compress else packed
        return data, data.decode('latin1')
    except Exception as e:
        raise ValueError(f"Serialization failed: {e}")

def deserialize(s: bytes | str, compressed=False):
    try:
        data = s if isinstance(s, bytes) else s.encode('latin1')
        raw  = zlib.decompress(data) if compressed else data
        return msgpack.unpackb(raw, raw=False)
    except Exception as e:
        raise ValueError(f"Deserialization failed: {e}")