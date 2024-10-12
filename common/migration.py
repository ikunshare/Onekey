import subprocess
import aiofiles
from pathlib import Path
from tqdm.asyncio import tqdm
from .log import log
from .get_steam_path import steam_path

directory = Path(steam_path) / "config" / "stplug-in"
temp_path = Path('./temp')
setup_url = 'https://steamtools.net/res/SteamtoolsSetup.exe'
setup_file = temp_path / 'SteamtoolsSetup.exe'

async def download_setup_file(session) -> None:
    log.info('🔄 开始下载 SteamTools 安装程序...')
    try:
        async with session.get(setup_url, stream=True) as r:
            if r.status == 200:
                total_size = int(r.headers.get('Content-Length', 0))
                chunk_size = 8192
                progress = tqdm(total=total_size, unit='B', unit_scale=True, desc='下载安装程序')

                async with aiofiles.open(setup_file, mode='wb') as f:
                    async for chunk in r.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        progress.update(len(chunk))

                progress.close()
                log.info('✅ 安装程序下载完成')
            else:
                log.error('⚠ 网络错误，无法下载安装程序')
    except Exception as e:
        log.error(f'⚠ 下载失败: {e}')

async def migrate(st_use: bool, session) -> None:
    if st_use:
        log.info('🔄 检测到你正在使用 SteamTools，尝试迁移旧文件')

        if directory.exists():
            for file in directory.iterdir():
                if file.is_file() and file.name.startswith("Onekey_unlock_"):
                    new_filename = file.name[len("Onekey_unlock_"):]

                    try:
                        file.rename(directory / new_filename)
                        log.info(f'Renamed: {file.name} -> {new_filename}')
                    except Exception as e:
                        log.error(f'⚠ 重命名失败 {file.name} -> {new_filename}: {e}')
        else:
            log.error('⚠ 故障，正在重新安装 SteamTools')
            temp_path.mkdir(parents=True, exist_ok=True)

            await download_setup_file(session)

            subprocess.run(str(setup_file), check=True)
            for file in temp_path.iterdir():
                file.unlink()
            temp_path.rmdir()
    else:
        log.info('✅ 未使用 SteamTools，停止迁移')
