try:
    import time
    import httpx
    import sys
    import winreg
    import ujson as json
    from pathlib import Path
except ImportError as e:
    print(e)
    import os

    os.system("pause")


def get_steam_path(config: dict) -> Path:
    """获取Steam安装路径"""
    try:
        if custom_path := config.get("Custom_Steam_Path"):
            return Path(custom_path)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            return Path(winreg.QueryValueEx(key, "SteamPath")[0])
    except Exception as e:
        print(f"Steam路径获取失败: {str(e)}")
        sys.exit(1)


DEFAULT_CONFIG = {
    "Github_Personal_Token": "",
    "Custom_Steam_Path": "",
    "Debug_Mode": False,
    "Logging_Files": True,
    "Help": "Github Personal Token可在GitHub设置的Developer settings中生成",
}


def generate_config() -> None:
    try:
        with open(Path("./config.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False))
        print("配置文件已生成")
    except IOError as e:
        print(f"配置文件创建失败: {str(e)}")
        sys.exit(1)


def load_config() -> dict:
    if not Path("./config.json").exists():
        generate_config()
        print("请填写配置文件后重新运行程序，5秒后退出")
        time.sleep(5)
        sys.exit(1)

    try:
        with open(Path("./config.json"), "r", encoding="utf-8") as f:
            return json.loads(f.read())
    except json.JSONDecodeError:
        print("配置文件损坏，正在重新生成...")
        generate_config()
        sys.exit(1)
    except Exception as e:
        print(f"配置加载失败: {str(e)}")
        sys.exit(1)


CLIENT = httpx.AsyncClient(verify=False)
CONFIG = load_config()
DEBUG_MODE = CONFIG.get("Debug_Mode", False)
LOG_FILE = CONFIG.get("Logging_Files", True)
GITHUB_TOKEN = str(CONFIG.get("Github_Personal_Token", ""))
STEAM_PATH = get_steam_path(CONFIG)
IS_CN = True
HEADER = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else None
REPO_LIST = [
    "SteamAutoCracks/ManifestHub",
    "ikun0014/ManifestHub",
    "Auiowu/ManifestAutoUpdate",
    "tymolu233/ManifestAutoUpdate-fix",
]
