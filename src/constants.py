"""常量定义"""

from pathlib import Path

APP_NAME = "Onekey"
BANNER = r"""
    _____   __   _   _____   _   _    _____  __    __ 
   /  _  \ |  \ | | | ____| | | / /  | ____| \ \  / /
   | | | | |   \| | | |__   | |/ /   | |__    \ \/ / 
   | | | | | |\   | |  __|  | |\ \   |  __|    \  /  
   | |_| | | | \  | | |___  | | \ \  | |___    / /   
   \_____/ |_|  \_| |_____| |_|  \_\ |_____|  /_/    
"""

REPO_LIST = [
    "SteamAutoCracks/ManifestHub",
    "ikun0014/ManifestHub",
    "Auiowu/ManifestAutoUpdate",
    "tymolu233/ManifestAutoUpdate-fix",
]

CN_CDN_LIST = [
    "https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}",
    "https://raw.gitmirror.com/{repo}/{sha}/{path}",
    "https://raw.dgithub.xyz/{repo}/{sha}/{path}",
    "https://gh.akass.cn/{repo}/{sha}/{path}",
]

GLOBAL_CDN_LIST = ["https://raw.githubusercontent.com/{repo}/{sha}/{path}"]

GITHUB_API_BASE = "https://api.github.com"
REGION_CHECK_URL = "https://mips.kugou.com/check/iscn?&format=json"

LOG_DIR = Path("logs")
CONFIG_FILE = Path("config.json")
