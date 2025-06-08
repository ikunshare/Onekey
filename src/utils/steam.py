import vdf
from typing import List, Optional, Tuple

from ..models import DepotInfo


def parse_key_file(content: bytes) -> List[DepotInfo]:
    """解析密钥文件"""
    try:
        depots = vdf.loads(content.decode("utf-8"))["depots"]
        return [
            DepotInfo(depot_id=d_id, decryption_key=d_info["DecryptionKey"])
            for d_id, d_info in depots.items()
        ]
    except Exception:
        return []


def parse_manifest_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """解析清单文件名"""
    if not filename.endswith(".manifest"):
        return None, None

    name = filename.replace(".manifest", "")
    if "_" not in name:
        return None, None

    parts = name.split("_", 1)
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return None, None

    return parts[0], parts[1]
