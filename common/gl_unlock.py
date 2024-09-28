from .get_steam_path import steam_path
from pathlib import Path

async def greenluma_add(depot_id_list: list) -> bool:
    app_list_path = steam_path / 'AppList'
    
    try:
        app_list_path.mkdir(parents=True, exist_ok=True)
        
        for file in app_list_path.iterdir():
            if file.is_file() and file.suffix == '.txt':
                file.unlink(missing_ok=True)

        depot_dict = {}
        
        for i in app_list_path.iterdir():
            if i.stem.isdecimal() and i.suffix == '.txt':
                with i.open('r', encoding='utf-8') as f:
                    app_id_ = f.read().strip()
                    if app_id_.isdecimal():
                        depot_dict[int(i.stem)] = int(app_id_)

        for depot_id in depot_id_list:
            depot_id = int(depot_id)
            if depot_id not in depot_dict.values():
                index = max(depot_dict.keys(), default=-1) + 1
                while index in depot_dict:
                    index += 1
                
                with (app_list_path / f'{index}.txt').open('w', encoding='utf-8') as f:
                    f.write(str(depot_id))

                depot_dict[index] = depot_id

        return True

    except Exception as e:
        print(f'❗ 处理时出错: {e}')
        return False
