from common import log, getsteampath
import asyncio
import aiofiles
import os
import subprocess

lock = asyncio.Lock()
log = log.log
steam_path = getsteampath.steam_path


# 增加SteamTools解锁相关文件
async def stool_add(depot_data, app_id):
    lua_filename = f"{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename

    async with lock:
        log.info(f' ✅ SteamTools解锁文件生成: {lua_filepath}')
        async with aiofiles.open(lua_filepath, mode="w", encoding="utf-8") as lua_file:
            await lua_file.write(f'addappid({app_id}, 1, "None")\n')
            for depot_id, depot_key in depot_data:
                await lua_file.write(f'addappid({depot_id}, 1, "{depot_key}")\n')

    luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
    subprocess.run([str(luapacka_path), str(lua_filepath)])
    os.remove(lua_filepath)
    return True

stunlock = stool_add