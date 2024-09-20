import os
import subprocess
import aiofiles
from pathlib import Path
from tqdm.asyncio import tqdm

from .log import log
from .get_steam_path import steam_path

directory = Path(steam_path / "config" / "stplug-in")

async def migrate(st_use, session):
    if st_use == True:
        log.info('🔄 检测到你正在使用SteamTools，尝试迁移旧文件')
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.startswith("Onekey_unlock_"):
                    new_filename = filename[len("Onekey_unlock_"):]

                    old_file = os.path.join(directory, filename)
                    new_file = os.path.join(directory, new_filename)

                    try:
                        os.replace(old_file, new_file)
                        log.info(f'Renamed: {filename} -> {new_filename}')
                    except Exception as e:
                        log.error(f'Failed to rename {filename} -> {new_filename}: {e}')
        else:
            log.error('⚠ 故障，正在重新安装SteamTools')
            temp_path = './temp'
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
            down_url = 'https://steamtools.net/res/SteamtoolsSetup.exe'
            out_path = './temp/SteamtoolsSetup.exe'

            async with session.get(down_url, stream=True) as r:
                if r.status == 200:
                    total_size = int(r.headers.get('Content-Length', 0))
                    chunk_size = 8192
                    progress = tqdm(total=total_size, unit='B', unit_scale=True)

                    async with aiofiles.open(out_path, mode='wb') as f:
                        async for chunk in r.content.iter_chunked(chunk_size=chunk_size):
                            await f.write(chunk)
                            progress.update(len(chunk))

                    progress.close()
                else:
                    log.error('⚠ 网络错误')

            subprocess.run(str(out_path))
            os.rmdir(temp_path)
    else:
        log.info('✅ 未使用SteamTools，停止迁移')
