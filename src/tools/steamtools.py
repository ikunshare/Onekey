from typing import List, Dict

from .base import UnlockTool
from ..models import DepotInfo


class SteamTools(UnlockTool):
    """SteamTools解锁工具实现"""

    async def setup(
        self,
        depot_data: List[DepotInfo],
        app_id: str,
        depot_map: Dict[str, List[str]] = None,
        version_lock: bool = False,
    ) -> bool:
        """设置SteamTools解锁"""
        st_path = self.steam_path / "config" / "stplug-in"
        st_path.mkdir(parents=True, exist_ok=True)

        lua_content = f'addappid({app_id}, 1, "None")\n'

        for depot in depot_data:
            if version_lock and depot_map and depot.depot_id in depot_map:
                for manifest_id in depot_map[depot.depot_id]:
                    lua_content += (
                        f'addappid({depot.depot_id}, 1, "{depot.decryption_key}")\n'
                        f'setManifestid({depot.depot_id},"{manifest_id}")\n'
                    )
            else:
                lua_content += (
                    f'addappid({depot.depot_id}, 1, "{depot.decryption_key}")\n'
                )

        lua_file = st_path / f"{app_id}.lua"
        lua_file.write_text(lua_content, encoding="utf-8")

        return True
