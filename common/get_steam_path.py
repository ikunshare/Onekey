import os
import winreg
from pathlib import Path
from .log import log
from .config import config
from .stack_error import stack_error

def get_steam_path() -> Path:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
        steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])
        
        custom_steam_path = config.get("Custom_Steam_Path", "").strip()
        return Path(custom_steam_path) if custom_steam_path else steam_path
    except KeyboardInterrupt:
        log.info("\n 程序已退出")
    except Exception as e:
        log.error(f'Steam路径获取失败, {stack_error(e)}, 请检查是否正确安装Steam')
        os.system('pause')
        return Path()

steam_path = get_steam_path()
