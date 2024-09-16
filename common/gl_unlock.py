from .get_steam_path import steam_path

async def greenluma_add(depot_id_list):
    app_list_path = steam_path / 'AppList'
    if app_list_path.exists() and app_list_path.is_file():
        app_list_path.unlink(missing_ok=True)
    
    if not app_list_path.is_dir():
        app_list_path.mkdir(parents=True, exist_ok=True)
    
    depot_dict = {int(i.stem): None for i in app_list_path.iterdir() if i.stem.isdecimal() and i.suffix == '.txt'}
    
    for i in app_list_path.iterdir():
        if i.stem.isdecimal() and i.suffix == '.txt':
            with i.open('r', encoding='utf-8') as f:
                app_id_ = f.read().strip()
                if app_id_.isdecimal():
                    depot_dict[int(i.stem)] = int(app_id_)
                    
    for depot_id in depot_id_list:
        if int(depot_id) not in depot_dict.values():
            index = max(depot_dict.keys(), default=-1) + 1
            for i in range(max(depot_dict.keys(), default=-1) + 1):
                if i not in depot_dict:
                    index = i
                    break
            
            with (app_list_path / f'{index}.txt').open('w', encoding='utf-8') as f:
                f.write(str(depot_id))
            depot_dict[index] = int(depot_id)
    
    return True