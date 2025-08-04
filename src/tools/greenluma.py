import vdf
from typing import List

from .base import UnlockTool
from ..models import DepotInfo


class GreenLuma(UnlockTool):
    """GreenLuma解锁工具实现"""

    async def setup(self, depot_data: List[DepotInfo], app_id: str, **kwargs) -> bool:
        """设置GreenLuma解锁"""
        applist_dir = self.steam_path / "AppList"
        applist_dir.mkdir(exist_ok=True)

        for f in applist_dir.glob("*.txt"):
            f.unlink()

        for idx, depot in enumerate(depot_data, 1):
            (applist_dir / f"{idx}.txt").write_text(depot.depot_id)

        config_path = self.steam_path / "config" / "config.vdf"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = vdf.loads(f.read())

            content.setdefault("depots", {}).update(
                {
                    depot.depot_id: {"DecryptionKey": depot.decryption_key}
                    for depot in depot_data
                }
            )

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(vdf.dumps(content))

            return True
        except Exception:
            return False
