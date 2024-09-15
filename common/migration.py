import os
import subprocess
import requests

from pathlib import Path
from .log import log
from .get_steam_path import steam_path

directory = Path(steam_path / "config" / "stplug-in")

def migrate(st_use):
    if st_use == True:
        log.info('检测到你正在使用SteamTools，尝试迁移旧文件')
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
            log.error('故障，正在重新安装SteamTools')
            temp_path = './temp'
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
            down_url = 'https://steamtools.net/res/SteamtoolsSetup.exe'
            out_path = './temp/SteamtoolsSetup.exe'
            with requests.get(down_url, stream=True) as r:
                if r.status_code == 200:
                    with open(out_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    log.error('网络错误')
            subprocess.run(str(out_path))
            os.rmdir(temp_path)
    else:
        log.info('未使用SteamTools，停止迁移')