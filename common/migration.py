import os
from common import log, getsteampath
from pathlib import Path

# 设置文件目录
log = log.log
steam_path = getsteampath.steam_path
directory = Path(steam_path / "config" / "stplug-in")

# 遍历目录中的所有文件
def migrate():
    for filename in os.listdir(directory):
        if filename.startswith("Onekey_unlock_"):
            new_filename = filename[len("Onekey_unlock_"):]
    
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_filename)
        
            os.rename(old_file, new_file)
            log.info(f'Renamed: {filename} -> {new_filename}')

migrate = migrate
