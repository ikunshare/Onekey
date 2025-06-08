import traceback
from typing import List, Dict, Tuple

from . import __version__, __author__, __website__
from .constants import BANNER, REPO_LIST
from .config import ConfigManager
from .logger import Logger
from .models import DepotInfo
from .network.client import HttpClient
from .network.github import GitHubAPI
from .utils.region import RegionDetector
from .utils.steam import parse_key_file, parse_manifest_filename
from .tools.steamtools import SteamTools
from .tools.greenluma import GreenLuma


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
        self.github = GitHubAPI(self.client, self.config.github_headers, self.logger)

    def show_banner(self):
        """显示横幅"""
        self.logger.info(BANNER)
        self.logger.info(
            f"本程序源代码基于GPL 2.0许可证开放于Github"
        )
        self.logger.info(
            f"作者: {__author__} | 版本: {__version__} | 官网: {__website__}"
        )
        self.logger.info("项目仓库: GitHub: https://github.com/ikunshare/Onekey")
        self.logger.warning("ikunshare.top | 严禁倒卖")
        self.logger.warning(
            "提示: 请确保已安装Windows 10/11并正确配置Steam;SteamTools/GreenLuma"
        )
        if not self.config.app_config.github_token:
            self.logger.warning("开梯子必须配置Token, 你的IP我不相信能干净到哪")

    async def handle_depot_files(
        self, app_id: str
    ) -> Tuple[List[DepotInfo], Dict[str, List[str]]]:
        """处理仓库文件"""
        depot_list = []
        depot_map = {}

        repo_info = await self.github.get_latest_repo_info(REPO_LIST, app_id)
        if not repo_info:
            return depot_list, depot_map

        self.logger.info(f"当前选择清单仓库: https://github.com/{repo_info.name}")
        self.logger.info(f"此清单分支上次更新时间：{repo_info.last_update}")

        branch_url = f"https://api.github.com/repos/{repo_info.name}/branches/{app_id}"
        branch_res = await self.client.get(
            branch_url, headers=self.config.github_headers
        )
        branch_res.raise_for_status()

        tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
        tree_res = await self.client.get(tree_url)
        tree_res.raise_for_status()

        depot_cache = self.config.steam_path / "depotcache"
        depot_cache.mkdir(exist_ok=True)

        for item in tree_res.json()["tree"]:
            file_path = item["path"]

            if file_path.endswith(".manifest"):
                save_path = depot_cache / file_path
                if save_path.exists():
                    self.logger.warning(f"已存在清单: {save_path}")
                    continue

                content = await self.github.fetch_file(
                    repo_info.name, repo_info.sha, file_path
                )
                save_path.write_bytes(content)
                self.logger.info(f"清单下载成功: {file_path}")

                depot_id, manifest_id = parse_manifest_filename(file_path)
                if depot_id and manifest_id:
                    depot_map.setdefault(depot_id, []).append(manifest_id)

            elif "key.vdf" in file_path.lower():
                key_content = await self.github.fetch_file(
                    repo_info.name, repo_info.sha, file_path
                )
                depot_list.extend(parse_key_file(key_content))

        for depot_id in depot_map:
            depot_map[depot_id].sort(key=lambda x: int(x), reverse=True)

        return depot_list, depot_map

    async def run(self, app_id: str):
        """运行主程序"""
        try:
            detector = RegionDetector(self.client, self.logger)
            is_cn, country = await detector.check_cn()
            self.github.is_cn = is_cn

            await self.github.check_rate_limit()

            self.logger.info(f"正在处理游戏 {app_id}...")
            depot_data, depot_map = await self.handle_depot_files(app_id)

            if not depot_data:
                self.logger.error("未找到此游戏的清单")
                return

            print("\n请选择解锁工具:")
            print("1. SteamTools")
            print("2. GreenLuma")

            choice = input("请输入选择 (1/2): ").strip()

            if choice == "1":
                tool = SteamTools(self.config.steam_path)

                version_lock = False
                lock_choice = input(
                    "是否锁定版本(推荐在选择仓库SteamAutoCracks/ManifestHub时使用)?(y/n): "
                ).lower()
                if lock_choice == "y":
                    version_lock = True

                success = await tool.setup(
                    depot_data, app_id, depot_map=depot_map, version_lock=version_lock
                )
            elif choice == "2":
                tool = GreenLuma(self.config.steam_path)
                success = await tool.setup(depot_data, app_id)
            else:
                self.logger.error("无效的选择")
                return

            if success:
                self.logger.info("游戏解锁配置成功！")
                self.logger.info("重启Steam后生效")
            else:
                self.logger.error("配置失败")

        except Exception as e:
            self.logger.error(f"运行错误: {traceback.format_exc()}")
        finally:
            await self.client.close()


async def main():
    """程序入口"""
    app = OnekeyApp()
    app.show_banner()

    app_id = input("\n请输入游戏AppID: ").strip()

    app_id_list = [id for id in app_id.split("-") if id.isdigit()]
    if not app_id_list:
        app.logger.error("App ID无效")
        return

    await app.run(app_id_list[0])
