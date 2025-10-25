from typing import List
from dataclasses import dataclass


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
class ManifestInfo:
    """清单信息"""

    app_id: int
    depot_id: str
    depot_key: str
    manifest_id: str
    url: str


@dataclass
class SteamAppInfo:
    appId: int
    name: str
    dlcCount: int
    depotCount: int
    workshopDecryptionKey: str


@dataclass
class SteamAppManifestInfo:
    mainapp: List[ManifestInfo]
    dlcs: List[ManifestInfo]


@dataclass
class AppConfig:
    """应用配置"""

    key: str = ""
    port: int = 5000
    custom_steam_path: str = ""
    debug_mode: bool = False
    logging_files: bool = True
    show_console: bool = True
    language: str = "zh"
