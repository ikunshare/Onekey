import winreg
from pathlib import Path
from common import config

config = config.config

# 通过注册表获取Steam安装路径
def get_steam_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
    steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])
    custom_steam_path = config["Custom_Steam_Path"]
    if not custom_steam_path == '':
        return Path(custom_steam_path)
    else:
        return steam_path
    
steam_path = get_steam_path()