import os
import winreg
from pathlib import Path
from .log import log
from .config import config
from .stack_error import stack_error

def get_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
        steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])
        custom_steam_path = config["Custom_Steam_Path"]
        
        if custom_steam_path:
            return Path(custom_steam_path)
        
        return steam_path
    except Exception as e:
        log.error(f'Steam路径获取失败, {stack_error(e)}')
        os.system('pause')
        return None

steam_path = get_steam_path()