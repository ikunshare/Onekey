import os
import sys
import json
import winreg
from pathlib import Path
from typing import Dict, Optional

from .constants import CONFIG_FILE
from .models import AppConfig

DEFAULT_CONFIG = {
    "KEY": "",
    "Debug_Mode": False,
    "Logging_Files": True,
    "Show_Console": False,
    "Custom_Steam_Path": "",
}


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_path = CONFIG_FILE
        self._config_data: Dict = {}
        self.app_config: AppConfig = AppConfig()
        self.steam_path: Optional[Path] = None
        self._load_config()

    def _generate_config(self) -> None:
        """生成默认配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print("配置文件已生成")
            os.system("pause")
            sys.exit(1)
        except IOError as e:
            print(f"配置文件创建失败: {str(e)}")
            os.system("pause")
            sys.exit(1)

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            self._generate_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config_data = json.load(f)

            self.app_config = AppConfig(
                key=self._config_data.get("KEY", ""),
                custom_steam_path=self._config_data.get("Custom_Steam_Path", ""),
                debug_mode=self._config_data.get("Debug_Mode", False),
                logging_files=self._config_data.get("Logging_Files", True),
                show_console=self._config_data.get("Show_Console", True),
            )

            self.steam_path = self._get_steam_path()
        except json.JSONDecodeError:
            print("配置文件损坏，正在重新生成...")
            self._generate_config()
            print("配置文件已重新生成，使用默认配置继续运行")
            self.app_config = AppConfig(
                key=DEFAULT_CONFIG.get("KEY", ""),
                custom_steam_path=DEFAULT_CONFIG.get("Custom_Steam_Path", ""),
                debug_mode=DEFAULT_CONFIG.get("Debug_Mode", False),
                logging_files=DEFAULT_CONFIG.get("Logging_Files", True),
                show_console=DEFAULT_CONFIG.get("Show_Console", True),
            )
            try:
                self.steam_path = self._get_steam_path()
            except:
                self.steam_path = None
        except Exception as e:
            print(f"配置加载失败: {str(e)}")
            print("使用默认配置继续运行")
            self.app_config = AppConfig(
                key=DEFAULT_CONFIG.get("KEY", ""),
                custom_steam_path=DEFAULT_CONFIG.get("Custom_Steam_Path", ""),
                debug_mode=DEFAULT_CONFIG.get("Debug_Mode", False),
                logging_files=DEFAULT_CONFIG.get("Logging_Files", True),
                show_console=DEFAULT_CONFIG.get("Show_Console", True),
            )
            try:
                self.steam_path = self._get_steam_path()
            except:
                self.steam_path = None

    def _get_steam_path(self) -> Optional[Path]:
        """获取Steam安装路径"""
        try:
            if self.app_config.custom_steam_path:
                return Path(self.app_config.custom_steam_path)

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
            ) as key:
                return Path(winreg.QueryValueEx(key, "SteamPath")[0])
        except Exception as e:
            print(f"Steam路径获取失败: {str(e)}")
            print("程序将继续运行，但部分功能可能不可用")
            return None
