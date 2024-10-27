from .get_steam_path import steam_path
from pathlib import Path


async def greenluma_add(depot_id_list: list) -> bool:
    app_list_path = steam_path / 'AppList'

    try:
        app_list_path.mkdir(parents=True, exist_ok=True)

        for file in app_list_path.glob('*.txt'):
            file.unlink(missing_ok=True)

        depot_dict = {
            int(i.stem): int(i.read_text(encoding='utf-8').strip())
            for i in app_list_path.iterdir() if i.is_file() and i.stem.isdecimal() and i.suffix == '.txt'
        }

        for depot_id in map(int, depot_id_list):
            if depot_id not in depot_dict.values():
                index = max(depot_dict.keys(), default=-1) + 1
                while index in depot_dict:
                    index += 1

                (app_list_path /
                 f'{index}.txt').write_text(str(depot_id), encoding='utf-8')

                depot_dict[index] = depot_id

        return True

    except Exception as e:
        print(f'处理时出错: {e}')
        return False
