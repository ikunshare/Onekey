import vdf
from typing import List

from .base import UnlockTool
from ..models import DepotInfo

class GreenLuma(UnlockTool):
    """GreenLuma解锁工具实现"""
    async def setup(self, depot_data: List[DepotInfo], app_id: str, **kwargs) -> bool:
        applist_dir = self.steam_path / "AppList"
        
        if applist_dir.is_file():
            applist_dir.unlink(missing_ok=True)
        if not applist_dir.is_dir():
            applist_dir.mkdir(parents=True, exist_ok=True)
            
        depot_dict = {}
        for i in applist_dir.iterdir():
            if i.stem.isdecimal() and i.suffix == '.txt':
                with i.open('r', encoding='utf-8') as f:
                    app_id_ = f.read().strip()
                    depot_dict[int(i.stem)] = int(app_id_) if app_id_.isdecimal() else None
        
        def find_next_index():
            if not depot_dict:
                return 0
            for i in range(max(depot_dict.keys())):
                if i not in depot_dict:
                    return i
            return max(depot_dict.keys()) + 1
        
        if app_id and app_id.isdecimal():
            app_id_int = int(app_id)
            if app_id_int not in depot_dict.values():
                index = find_next_index()
                with (applist_dir / f'{index}.txt').open('w', encoding='utf-8') as f:
                    f.write(str(app_id))
                depot_dict[index] = app_id_int
        
        for depot in depot_data:
            depot_id = int(depot.depot_id)
            if depot_id not in depot_dict.values():
                index = find_next_index()
                with (applist_dir / f'{index}.txt').open('w', encoding='utf-8') as f:
                    f.write(str(depot_id))
                depot_dict[index] = depot_id
        
        config_path = self.steam_path / "config" / "config.vdf"
        try:
            if config_path.is_file():
                with open(config_path, "r", encoding="utf-8") as f:
                    content = vdf.loads(f.read())
            else:
                content = {}
                config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if "depots" not in content:
                content["depots"] = {}
            
            for depot in depot_data:
                content["depots"][depot.depot_id] = {"DecryptionKey": depot.decryption_key}
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(vdf.dumps(content))
            return True
        except Exception as e:
            print(f"GreenLuma配置失败: {e}")
            return False