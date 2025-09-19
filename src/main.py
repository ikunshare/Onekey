from typing import List, Dict, Tuple
from .constants import STEAM_API_BASE
from .config import ConfigManager
from .logger import Logger
from .models import DepotInfo, ManifestInfo, SteamAppInfo, SteamAppManifestInfo
from .network.client import HttpClient
from .manifest_handler import ManifestHandler
from . import constants


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

    async def check_ip(self):
        req = await self.client.get(
            "https://mips.kugou.com/check/iscn",
        )
        req.raise_for_status()
        body = req.json()
        constants.IS_CN = bool(body["ip_flag"])

    async def fetch_key(self):
        trans = {
            "week": "周卡",
            "month": "月卡",
            "year": "年卡",
            "permanent": "永久卡",
        }
        try:
            response = await self.client._client.post(
                f"{STEAM_API_BASE}/getKeyInfo",
                json={"key": self.config.app_config.key},
            )
            body = response.json()
            if not body["info"]:
                self.logger.error("卡密不存在")
                return False
            self.logger.info(f"卡密类型: {trans[body['info']['type']]}")
            if trans[body["info"]["type"]] != "永久卡":
                self.logger.info(f"卡密过期时间: {body['info']['expiresAt']}")
            return True
        except Exception as e:
            self.logger.error(f"获取卡密信息失败: {str(e)}")
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
            self.logger.info(f"正在获取游戏 {app_id} 的信息...")

            response = await self.client._client.post(
                f"{STEAM_API_BASE}/getGame",
                json={"appId": int(app_id), "dlc": and_dlc},
                headers={"X-Api-Key": self.config.app_config.key},
            )

            if response.status_code == 401:
                self.logger.error("API密钥无效")
                return []

            if response.status_code != 200:
                self.logger.error(f"API请求失败，状态码: {response.status_code}")
                return []

            data = response.json()

            if not data:
                self.logger.error("未找到此游戏的清单信息")
                return []

            self.logger.info(f"游戏名称: {data.get('name', 'Unknown')}")
            self.logger.info(f"Depot数量: {data.get('depotCount', 'Unknown')}")

            if and_dlc:
                for item in data["gameManifests"]:
                    manifest = ManifestInfo(
                        app_id=item["app_id"],
                        depot_id=item["depot_id"],
                        depot_key=item["depot_key"],
                        manifest_id=item["manifest_id"],
                        url=item["url"],
                    )
                    main_app_manifests.append(manifest)

                for item in data["dlcManifests"]:
                    self.logger.info(f"DLC名称: {item.get('dlcName', 'Unknown')}")
                    self.logger.info(f"DLC AppId: {item.get('dlcId', 'Unknown')}")
                    for manifests in item["manifests"]:
                        manifest = ManifestInfo(
                            app_id=manifests["app_id"],
                            depot_id=manifests["depot_id"],
                            depot_key=manifests["depot_key"],
                            manifest_id=manifests["manifest_id"],
                            url=manifests["url"],
                        )
                        dlc_manifests.append(manifest)
            else:
                for item in data["manifests"]:
                    manifest = ManifestInfo(
                        app_id=item["app_id"],
                        depot_id=item["depot_id"],
                        depot_key=item["depot_key"],
                        manifest_id=item["manifest_id"],
                        url=item["url"],
                    )
                    main_app_manifests.append(manifest)
        except Exception as e:
            self.logger.error(f"获取主游戏信息失败: {str(e)}")
            return SteamAppManifestInfo(mainapp=[], dlcs=[])

        return SteamAppInfo(
            app_id,
            data["name"],
            data.get("totalDLCCount", data.get("dlcCount", 0)),
            data["depotCount"],
            data.get("workshopDecryptionKey", "None"),
        ), SteamAppManifestInfo(mainapp=main_app_manifests, dlcs=dlc_manifests)

    def prepare_depot_data(
        self, manifests: List[ManifestInfo]
    ) -> tuple[List[DepotInfo], Dict[str, List[str]]]:
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

    async def run(self, app_id: str, tool_type: str, dlc: bool):
        """
        为Web版本提供的运行方法。
        """
        try:
            if not self.config.steam_path:
                self.logger.error("Steam路径未配置或无效，无法继续")
                return False

            await self.check_ip()
            await self.fetch_key()

            manifests = []

            app_info, manifests = await self.fetch_app_data(app_id, dlc)

            if not manifests:
                return False

            manifest_handler = ManifestHandler(
                self.client, self.logger, self.config.steam_path
            )
            processed_manifests = await manifest_handler.process_manifests(manifests)
            if not processed_manifests:
                self.logger.error("没有成功处理的清单")
                return False

            depot_data, _ = self.prepare_depot_data(processed_manifests)
            self.logger.info(f"选择的解锁工具: {tool_type}")
            if tool_type == "steamtools":
                from .tools.steamtools import SteamTools

                tool = SteamTools(self.config.steam_path)
                success = await tool.setup(depot_data, app_info)
            elif tool_type == "greenluma":
                from .tools.greenluma import GreenLuma

                tool = GreenLuma(self.config.steam_path)
                success = await tool.setup(depot_data, app_id)
            else:
                self.logger.error("无效的工具选择")
                return False

            if success:
                self.logger.info("游戏解锁配置成功！")
                self.logger.info("重启Steam后生效")
                return True
            else:
                self.logger.error("配置失败")
                return False
        except Exception as e:
            self.logger.error(f"运行错误: {e}")
            return False
        finally:
            await self.client.close()
