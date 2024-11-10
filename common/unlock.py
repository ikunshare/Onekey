import os
import asyncio
import subprocess
import aiofiles
from .get_steam_path import steam_path
from .log import log

lock = asyncio.Lock()

async def stool_add(depot_data: list, app_id: str) -> bool:
    lua_filename = f"{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename

    async with lock:
        log.info(f'SteamTools 解锁文件生成: {lua_filepath}')
        try:
            async with aiofiles.open(lua_filepath, mode="w", encoding="utf-8") as lua_file:
                await lua_file.write(f'addappid({app_id}, 1, "None")\n')
                for depot_id, depot_key in depot_data:
                    await lua_file.write(f'addappid({depot_id}, 1, "{depot_key}")\n')

            luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
            log.info(f'正在处理文件: {lua_filepath}')

            result = subprocess.run(
                [str(luapacka_path), str(lua_filepath)],
                capture_output=True
            )
            if result.returncode != 0:
                log.error(f'调用失败: {result.stderr.decode()}')
                return False

            log.info('处理完成')
        except KeyboardInterrupt:
            log.info("\n 程序已退出")
        except Exception as e:
            log.error(f'处理过程出现错误: {e}')
            return False
        finally:
            if lua_filepath.exists():
                os.remove(lua_filepath)
                log.info(f'🗑️ 删除临时文件: {lua_filepath}')

    return True


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
