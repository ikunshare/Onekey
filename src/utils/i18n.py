from typing import Dict


class I18n:
    """国际化管理类"""

    def __init__(self, default_lang: str = "zh"):
        self.current_lang = default_lang
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """加载所有语言的翻译"""
        # 中文翻译
        self.translations["zh"] = {
            # 系统托盘
            "tray.open_browser": "打开浏览器",
            "tray.show_console": "显示控制台",
            "tray.exit": "退出程序",
            # 主程序
            "main.starting": "正在启动Onekey...",
            "main.tray_created": "系统托盘已创建",
            "main.browser_opened": "浏览器已自动打开",
            "main.browser_open_failed": "无法自动打开浏览器，请手动访问: http://localhost:{port}",
            "main.exit": "程序已退出",
            "main.start_error": "启动错误: {error}",
            "main.press_enter": "按回车键退出...",
            "main.startup_failed": "启动失败: {error}",
            "main.checkip_success": "已获取IP属地",
            "main.checkip_failed": "获取IP属地失败: {error}, 默认您在中国大陆境内",
            # 配置
            "config.generated": "配置文件已生成",
            "config.create_failed": "配置文件创建失败: {error}",
            "config.corrupted": "配置文件损坏，正在重新生成...",
            "config.regenerated": "配置文件已重新生成，使用默认配置继续运行",
            "config.load_failed": "配置加载失败: {error}",
            "config.use_default": "使用默认配置继续运行",
            "config.steam_path_failed": "Steam路径获取失败: {error}",
            "config.continue_partial": "程序将继续运行，但部分功能可能不可用",
            # API相关
            "api.key_not_exist": "卡密不存在",
            "api.key_type": "卡密类型: {type}",
            "api.key_expires": "卡密过期时间: {time}",
            "api.key_info_failed": "获取卡密信息失败: {error}",
            "api.fetching_game": "正在获取游戏 {app_id} 的信息...",
            "api.invalid_key": "API密钥无效",
            "api.request_failed": "API请求失败，状态码: {code}",
            "api.no_manifest": "未找到此游戏的清单信息",
            "api.game_name": "游戏名称: {name}",
            "api.depot_count": "Depot数量: {count}",
            "api.dlc_name": "DLC名称: {name}",
            "api.dlc_appid": "DLC AppId: {id}",
            "api.fetch_failed": "获取主游戏信息失败: {error}",
            # 工具相关
            "tool.selected": "选择的解锁工具: {tool}",
            "tool.invalid_selection": "无效的工具选择",
            "tool.config_success": "游戏解锁配置成功！",
            "tool.restart_steam": "重启Steam后生效",
            "tool.config_failed": "配置失败",
            # 任务相关
            "task.no_steam_path": "Steam路径未配置或无效，无法继续",
            "task.no_manifest_processed": "没有成功处理的清单",
            "task.run_error": "运行错误: {error}",
            # 卡密类型
            "key_type.week": "周卡",
            "key_type.month": "月卡",
            "key_type.year": "年卡",
            "key_type.permanent": "永久卡",
            # 错误消息
            "error.load_icon": "加载图标失败: {error}",
            "error.import": "导入错误: {error}",
            "error.ensure_root": "请确保在项目根目录中运行此程序",
            # Web相关
            "web.starting": "启动Onekey Web GUI...",
            "web.visit": "请在浏览器中访问: http://localhost:{port}",
            "web.task_running": "已有任务正在运行",
            "web.invalid_appid": "请输入有效的App ID",
            "web.invalid_format": "App ID格式无效",
            "web.task_started": "任务已开始",
            "web.task_failed": "任务执行失败: {error}",
            "web.config_saved": "配置已保存",
            "web.config_save_failed": "保存配置失败: {error}",
            "web.config_reset": "配置已重置为默认值",
            "web.config_reset_failed": "重置配置失败: {error}",
            "web.key_empty": "卡密不能为空",
            "web.key_service_unavailable": "卡密验证服务不可用",
            "web.verify_timeout": "验证超时，请检查网络连接",
            "web.verify_failed": "验证失败: {error}",
            "web.connected": "已连接到服务器",
            "web.client_disconnected": "客户端断开连接",
            "web.websocket_error": "WebSocket 错误: {error}",
            "web.invalid_config_data": "无效的配置数据",
            # 清单处理
            "manifest.download.failed": "从 {url} 下载失败: {error}",
            "manifest.delete_old": "删除旧清单: {name}",
            "manifest.process.success": "清单处理成功: {depot_id}_{manifest_id}.manifest",
            "manifest.process.failed": "处理清单时出错: {error}",
            "manifest.process.failed2": "处理清单失败: {depot_id}_{manifest_id}",
            "manifest.exists": "清单已存在: {name}",
            "manifest.downloading": "正在下载清单: {depot_id}_{manifest_id}",
            "manifest.downloading.failed": "下载清单失败: {depot_id}_{manifest_id}",
        }

        # 英文翻译
        self.translations["en"] = {
            # System tray
            "tray.open_browser": "Open Browser",
            "tray.show_console": "Show Console",
            "tray.exit": "Exit",
            # Main program
            "main.starting": "Starting Onekey...",
            "main.tray_created": "System tray created",
            "main.browser_opened": "Browser opened automatically",
            "main.browser_open_failed": "Failed to open browser automatically, please visit: http://localhost:{port}",
            "main.exit": "Program exited",
            "main.start_error": "Startup error: {error}",
            "main.press_enter": "Press Enter to exit...",
            "main.startup_failed": "Startup failed: {error}",
            "main.checkip_success": "Obtained IP territory",
            "main.checkip_failed": "Failed to obtain IP territory: {error}, by default you are in mainland China",
            # Configuration
            "config.generated": "Configuration file generated",
            "config.create_failed": "Failed to create configuration file: {error}",
            "config.corrupted": "Configuration file corrupted, regenerating...",
            "config.regenerated": "Configuration file regenerated, continuing with default config",
            "config.load_failed": "Failed to load configuration: {error}",
            "config.use_default": "Continuing with default configuration",
            "config.steam_path_failed": "Failed to get Steam path: {error}",
            "config.continue_partial": "Program will continue but some features may be unavailable",
            # API related
            "api.key_not_exist": "Key does not exist",
            "api.key_type": "Key type: {type}",
            "api.key_expires": "Key expires at: {time}",
            "api.key_info_failed": "Failed to get key info: {error}",
            "api.fetching_game": "Fetching game {app_id} information...",
            "api.invalid_key": "Invalid API key",
            "api.request_failed": "API request failed with status code: {code}",
            "api.no_manifest": "No manifest found for this game",
            "api.game_name": "Game name: {name}",
            "api.depot_count": "Depot count: {count}",
            "api.dlc_name": "DLC name: {name}",
            "api.dlc_appid": "DLC AppId: {id}",
            "api.fetch_failed": "Failed to fetch main game info: {error}",
            # Tool related
            "tool.selected": "Selected unlock tool: {tool}",
            "tool.invalid_selection": "Invalid tool selection",
            "tool.config_success": "Game unlock configuration successful!",
            "tool.restart_steam": "Restart Steam to take effect",
            "tool.config_failed": "Configuration failed",
            # Task related
            "task.no_steam_path": "Steam path not configured or invalid, cannot continue",
            "task.no_manifest_processed": "No manifests successfully processed",
            "task.run_error": "Run error: {error}",
            # Key types
            "key_type.week": "Weekly",
            "key_type.month": "Monthly",
            "key_type.year": "Yearly",
            "key_type.permanent": "Permanent",
            # Error messages
            "error.load_icon": "Failed to load icon: {error}",
            "error.import": "Import error: {error}",
            "error.ensure_root": "Please ensure running this program from project root",
            # Web related
            "web.starting": "Starting Onekey Web GUI...",
            "web.visit": "Please visit: http://localhost:{port}",
            "web.task_running": "A task is already running",
            "web.invalid_appid": "Please enter a valid App ID",
            "web.invalid_format": "Invalid App ID format",
            "web.task_started": "Task started",
            "web.task_failed": "Task execution failed: {error}",
            "web.config_saved": "Configuration saved",
            "web.config_save_failed": "Failed to save configuration: {error}",
            "web.config_reset": "Configuration reset to default",
            "web.config_reset_failed": "Failed to reset configuration: {error}",
            "web.key_empty": "Key cannot be empty",
            "web.key_service_unavailable": "Key verification service unavailable",
            "web.verify_timeout": "Verification timeout, please check network connection",
            "web.verify_failed": "Verification failed: {error}",
            "web.connected": "Connected to server",
            "web.client_disconnected": "Client disconnected",
            "web.websocket_error": "WebSocket error: {error}",
            "web.invalid_config_data": "Invalid configuration data",
            # List processing
            "manifest.download.failed": "Downloading from {url} failed: {error}",
            "manifest.delete_old": "Delete old manifest: {name}",
            "manifest.process.success": "Manifest processing successful: {depot_id}_{manifest_id}.manifest",
            "manifest.process.failed": "Error while processing manifest: {error}",
            "manifest.process.failed2": "Manifest processing failed: {depot_id}_{manifest_id}",
            "manifest.exists": "Manifest already exists: {name}",
            "manifest.downloading": "Downloading manifest: {depot_id}_{manifest_id}",
            "manifest.downloading.failed": "Manifest download failed: {depot_id}_{manifest_id}",
        }

    def set_language(self, lang: str):
        """设置当前语言"""
        if lang in self.translations:
            self.current_lang = lang
        else:
            raise ValueError(f"Unsupported language: {lang}")

    def t(self, key: str, **kwargs) -> str:
        """
        获取翻译文本

        Args:
            key: 翻译键
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        lang_dict = self.translations.get(self.current_lang, {})
        text = lang_dict.get(key, key)

        # 格式化文本
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def get_all_translations(self, lang: str = None) -> Dict[str, str]:
        """获取指定语言的所有翻译"""
        lang = lang or self.current_lang
        return self.translations.get(lang, {})


# 全局i18n实例
_i18n_instance = None


def get_i18n() -> I18n:
    """获取全局i18n实例"""
    global _i18n_instance
    if _i18n_instance is None:
        from ..config import ConfigManager

        config = ConfigManager()
        _i18n_instance = I18n(config.app_config.language)
    return _i18n_instance


def t(key: str, **kwargs) -> str:
    """便捷的翻译函数"""
    return get_i18n().t(key, **kwargs)
