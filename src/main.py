from typing import List, Dict, Tuple
from .constants import STEAM_API_BASE
from .config import ConfigManager
from .logger import Logger
from .models import DepotInfo, ManifestInfo, SteamAppInfo, SteamAppManifestInfo
from .network.client import HttpClient
from .manifest_handler import ManifestHandler
from .utils.i18n import t


class OnekeyApp:
    """Onekey主应用"""

    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger(
            "Onekey",
            debug_mode=self.config.app_config.debug_mode,
            log_file=self.config.app_config.logging_files,
        )
        self.client = HttpClient()

    async def fetch_key(self) -> bool:
        """获取并验证卡密信息"""
        try:
            response = await self.client._client.post(
                f"{STEAM_API_BASE}/getKeyInfo",
                json={"key": self.config.app_config.key},
            )
            body = response.json()

            if not body["info"]:
                self.logger.error(t("api.key_not_exist"))
                return False

            key_type = body["info"]["type"]
            self.logger.info(t("api.key_type", type=t(f"key_type.{key_type}")))

            if key_type != "permanent":
                self.logger.info(t("api.key_expires", time=body["info"]["expiresAt"]))
            return True
        except Exception as e:
            self.logger.error(t("api.key_info_failed", error=str(e)))
            return True

    async def fetch_app_data(
        self, app_id: str, and_dlc: bool = True
    ) -> Tuple[SteamAppInfo, SteamAppManifestInfo]:
        """
        从API获取应用数据
        """
        main_app_manifests = []
        dlc_manifests = []

        try:
            self.logger.info(t("api.fetching_game", app_id=app_id))

            response = await self.client._client.post(
                f"{STEAM_API_BASE}/getGame",
                json={"appId": int(app_id), "dlc": and_dlc},
                headers={"X-Api-Key": self.config.app_config.key},
            )

            if response.status_code == 401:
                self.logger.error(t("api.invalid_key"))
                return SteamAppInfo(), SteamAppManifestInfo(mainapp=[], dlcs=[])

            if response.status_code != 200:
                self.logger.error(t("api.request_failed", code=response.status_code))
                return SteamAppInfo(), SteamAppManifestInfo(mainapp=[], dlcs=[])

            data = response.json()

            if not data:
                self.logger.error(t("api.no_manifest"))
                return SteamAppInfo(), SteamAppManifestInfo(mainapp=[], dlcs=[])

            self.logger.info(t("api.game_name", name=data.get("name", "Unknown")))
            self.logger.info(
                t("api.depot_count", count=data.get("depotCount", "Unknown"))
            )

            if and_dlc:
                for item in data.get("gameManifests", []):
                    manifest = ManifestInfo(
                        app_id=item["app_id"],
                        depot_id=item["depot_id"],
                        depot_key=item["depot_key"],
                        manifest_id=item["manifest_id"],
                        url=item["url"],
                    )
                    main_app_manifests.append(manifest)

                for item in data.get("dlcManifests", []):
                    self.logger.info(
                        t("api.dlc_name", name=item.get("dlcName", "Unknown"))
                    )
                    self.logger.info(
                        t("api.dlc_appid", id=item.get("dlcId", "Unknown"))
                    )
                    for manifests in item.get("manifests", []):
                        manifest = ManifestInfo(
                            app_id=manifests["app_id"],
                            depot_id=manifests["depot_id"],
                            depot_key=manifests["depot_key"],
                            manifest_id=manifests["manifest_id"],
                            url=manifests["url"],
                        )
                        dlc_manifests.append(manifest)
            else:
                for item in data.get("manifests", []):
                    manifest = ManifestInfo(
                        app_id=item["app_id"],
                        depot_id=item["depot_id"],
                        depot_key=item["depot_key"],
                        manifest_id=item["manifest_id"],
                        url=item["url"],
                    )
                    main_app_manifests.append(manifest)

        except Exception as e:
            self.logger.error(t("api.fetch_failed", error=str(e)))
            return SteamAppInfo(), SteamAppManifestInfo(mainapp=[], dlcs=[])

        return SteamAppInfo(
            app_id,
            data.get("name", ""),
            data.get("totalDLCCount", data.get("dlcCount", 0)),
            data.get("depotCount", 0),
            data.get("workshopDecryptionKey", "None"),
        ), SteamAppManifestInfo(mainapp=main_app_manifests, dlcs=dlc_manifests)

    def prepare_depot_data(
        self, manifests: List[ManifestInfo]
    ) -> Tuple[List[DepotInfo], Dict[str, List[str]]]:
        """准备仓库数据"""
        depot_data = []
        depot_dict = {}

        for manifest in manifests:
            if manifest.depot_id not in depot_dict:
                depot_dict[manifest.depot_id] = {
                    "key": manifest.depot_key,
                    "manifests": [],
                }
            depot_dict[manifest.depot_id]["manifests"].append(manifest.manifest_id)

        for depot_id, info in depot_dict.items():
            depot_info = DepotInfo(
                depot_id=depot_id,
                decryption_key=info["key"],
                manifest_ids=info["manifests"],
            )
            depot_data.append(depot_info)

        return depot_data, depot_dict

    async def run(self, app_id: str, tool_type: str, dlc: bool) -> bool:
        """
        为Web版本提供的运行方法。

        Args:
            app_id: Steam应用ID
            tool_type: 解锁工具类型 (steamtools/greenluma)
            dlc: 是否包含DLC

        Returns:
            是否成功执行
        """
        try:
            if not self.config.steam_path:
                self.logger.error(t("task.no_steam_path"))
                return False

            await self.fetch_key()

            app_info, manifests = await self.fetch_app_data(app_id, dlc)

            if not manifests.mainapp and not manifests.dlcs:
                return False

            manifest_handler = ManifestHandler(
                self.client, self.logger, self.config.steam_path
            )

            processed_manifests = await manifest_handler.process_manifests(manifests)

            if not processed_manifests:
                self.logger.error(t("task.no_manifest_processed"))
                return False

            depot_data, _ = self.prepare_depot_data(processed_manifests)
            self.logger.info(t("tool.selected", tool=tool_type))

            if tool_type == "steamtools":
                from .tools.steamtools import SteamTools

                tool = SteamTools(self.config.steam_path)
                success = await tool.setup(depot_data, app_info)
            elif tool_type == "greenluma":
                from .tools.greenluma import GreenLuma

                tool = GreenLuma(self.config.steam_path)
                success = await tool.setup(depot_data, app_id)
            else:
                self.logger.error(t("tool.invalid_selection"))
                return False

            if success:
                self.logger.info(t("tool.config_success"))
                self.logger.info(t("tool.restart_steam"))
                return True
            else:
                self.logger.error(t("tool.config_failed"))
                return False

        except Exception as e:
            self.logger.error(t("task.run_error", error=str(e)))
            return False
        finally:
            await self.client.close()
