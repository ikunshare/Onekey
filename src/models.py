from typing import List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DepotInfo:
    """仓库信息"""

    depot_id: str
    decryption_key: str
    manifest_ids: List[str] = None

    def __post_init__(self):
        if self.manifest_ids is None:
            self.manifest_ids = []


@dataclass
class RepoInfo:
    """GitHub仓库信息"""

    name: str
    last_update: datetime
    sha: str


@dataclass
class AppConfig:
    """应用配置"""

    github_token: str = ""
    custom_steam_path: str = ""
    debug_mode: bool = False
    logging_files: bool = True
