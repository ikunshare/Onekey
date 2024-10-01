import os
import asyncio
import subprocess
import aiofiles
from pathlib import Path

from .log import log
from .get_steam_path import steam_path

lock = asyncio.Lock()

async def stool_add(depot_data: list, app_id: str) -> bool:
    lua_filename = f"{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename

    async with lock:
        log.info(f'✅ SteamTools 解锁文件生成: {lua_filepath}')
        try:
            async with aiofiles.open(lua_filepath, mode="w", encoding="utf-8") as lua_file:
                await lua_file.write(f'addappid({app_id}, 1, "None")\n')
                for depot_id, depot_key in depot_data:
                    await lua_file.write(f'addappid({depot_id}, 1, "{depot_key}")\n')

            luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
            log.info(f'🔄 正在处理文件: {lua_filepath}')

            result = subprocess.run(
                [str(luapacka_path), str(lua_filepath)], 
                capture_output=True
            )
            if result.returncode != 0:
                log.error(f'⚠ 调用失败: {result.stderr.decode()}')
                return False

            log.info('✅ 处理完成')
        except Exception as e:
            log.error(f'❗ 处理过程出现错误: {e}')
            return False
        finally:
            if lua_filepath.exists():
                os.remove(lua_filepath)
                log.info(f'🗑️ 删除临时文件: {lua_filepath}')

    return True
