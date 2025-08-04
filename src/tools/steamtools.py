from typing import List
from datetime import datetime

from .base import UnlockTool
from ..models import DepotInfo, SteamAppInfo


class SteamTools(UnlockTool):
    """SteamTools解锁工具实现"""

    async def setup(
        self,
        depot_data: List[DepotInfo],
        app_info: SteamAppInfo,
    ) -> bool:
        """设置SteamTools解锁"""
        st_path = self.steam_path / "config" / "stplug-in"
        st_path.mkdir(parents=True, exist_ok=True)

        lua_content = f"""
-- Generated Lua Manifest by Onekey
-- Steam App {app_info.appId} Manifest
-- Name: {app_info.name}
-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Total Depots: {app_info.depotCount}
-- Total DLCs: {app_info.dlcCount}

-- MAIN APP
addappid({app_info.appId}, "0", "{app_info.workshopDecryptionKey}")

-- ALL Depots
"""

        for depot in depot_data:
            lua_content += (
                f'addappid({depot.depot_id}, "1", "{depot.decryption_key}")\n'
            )

        lua_file = st_path / f"{app_info.appId}.lua"
        lua_file.write_text(lua_content, encoding="utf-8")

        return True
