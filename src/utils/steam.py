from typing import Optional, Tuple


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
