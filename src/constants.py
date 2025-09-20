"""常量定义"""

from pathlib import Path

LOG_DIR: Path = Path("logs")
IS_CN: bool = True
CONFIG_FILE: Path = Path("config.json")


STEAM_API_BASE: str = "https://steam.ikunshare.com/api"
STEAM_CACHE_CDN_LIST: list = (
    [
        "http://alibaba.cdn.steampipe.steamcontent.com",
        "http://steampipe.steamcontent.tnkjmec.com",
    ]
    if IS_CN
    else [
        "http://fastly.cdn.steampipe.steamcontent.com",
        "http://akamai.cdn.steampipe.steamcontent.com",
        "http://telus.cdn.steampipe.steamcontent.com",
        "https://cache1-hkg1.steamcontent.com",
        "https://cache2-hkg1.steamcontent.com",
        "https://cache3-hkg1.steamcontent.com",
        "https://cache4-hkg1.steamcontent.com",
        "https://cache5-hkg1.steamcontent.com",
        "https://cache6-hkg1.steamcontent.com",
        "https://cache7-hkg1.steamcontent.com",
        "https://cache8-hkg1.steamcontent.com",
        "https://cache9-hkg1.steamcontent.com",
        "https://cache10-hkg1.steamcontent.com",
    ]
)
