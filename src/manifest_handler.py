import vdf
from pathlib import Path
from typing import List, Optional
from steam.client.cdn import DepotManifest
from .constants import STEAM_CACHE_CDN_LIST
from .models import ManifestInfo, SteamAppManifestInfo
from .logger import Logger
from .network.client import HttpClient


class ManifestHandler:
    """清单处理器"""

    def __init__(self, client: HttpClient, logger: Logger, steam_path: Path):
        self.client = client
        self.logger = logger
        self.steam_path = steam_path
        self.depot_cache = steam_path / "depotcache"
        self.depot_cache.mkdir(exist_ok=True)

    async def download_manifest(self, manifest_info: ManifestInfo) -> Optional[bytes]:
        """下载清单文件"""
        for _ in range(3):
            for cdn in STEAM_CACHE_CDN_LIST:
                url = cdn + manifest_info.url
                try:
                    r = await self.client.get(url)
                    if r.status_code == 200:
                        return r.content
                except Exception as e:
                    self.logger.debug(f"从 {url} 下载失败: {str(e)}")

    def process_manifest(
        self, manifest_data: bytes, manifest_info: ManifestInfo, remove_old: bool = True
    ) -> bool:
        """处理清单文件"""
        try:
            depot_id = manifest_info.depot_id
            manifest_id = manifest_info.manifest_id
            depot_key = bytes.fromhex(manifest_info.depot_key)

            manifest = DepotManifest(manifest_data)
            manifest_path = self.depot_cache / f"{depot_id}_{manifest_id}.manifest"

            config_path = self.depot_cache / "config.vdf"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    d = vdf.load(f)
            else:
                d = {"depots": {}}

            d["depots"][depot_id] = {"DecryptionKey": depot_key.hex()}
            d = {"depots": dict(sorted(d["depots"].items()))}

            if remove_old:
                for file in self.depot_cache.iterdir():
                    if file.suffix == ".manifest":
                        parts = file.stem.split("_")
                        if (
                            len(parts) == 2
                            and parts[0] == str(depot_id)
                            and parts[1] != str(manifest_id)
                        ):
                            file.unlink(missing_ok=True)
                            self.logger.info(f"删除旧清单: {file.name}")

            with open(manifest_path, "wb") as f:
                f.write(manifest.serialize(compress=False))

            with open(config_path, "w", encoding="utf-8") as f:
                vdf.dump(d, f, pretty=True)

            self.logger.info(f"清单处理成功: {depot_id}_{manifest_id}.manifest")
            return True

        except Exception as e:
            self.logger.error(f"处理清单时出错: {str(e)}")
            return False

    async def process_manifests(
        self, manifests: SteamAppManifestInfo
    ) -> List[ManifestInfo]:
        """批量处理清单"""
        processed = []

        app_manifest = manifests.mainapp
        dlc_manifest = manifests.dlcs

        for manifest_info in app_manifest + dlc_manifest:
            manifest_path = (
                self.depot_cache
                / f"{manifest_info.depot_id}_{manifest_info.manifest_id}.manifest"
            )

            if manifest_path.exists():
                self.logger.warning(f"清单已存在: {manifest_path.name}")
                processed.append(manifest_info)
                continue

            self.logger.info(
                f"正在下载清单: {manifest_info.depot_id}_{manifest_info.manifest_id}"
            )
            manifest_data = await self.download_manifest(manifest_info)

            if manifest_data:
                if self.process_manifest(manifest_data, manifest_info):
                    processed.append(manifest_info)
                else:
                    self.logger.error(
                        f"处理清单失败: {manifest_info.depot_id}_{manifest_info.manifest_id}"
                    )
            else:
                self.logger.error(
                    f"下载清单失败: {manifest_info.depot_id}_{manifest_info.manifest_id}"
                )

        return processed
