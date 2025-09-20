"""常量定义"""

from pathlib import Path
from httpx import Client

LOG_DIR: Path = Path("logs")
CONFIG_FILE: Path = Path("config.json")


def check_ip():
    try:
        with Client(verify=False, timeout=5.0) as client:
            req = client.get(
                "https://mips.kugou.com/check/iscn",
            )
            req.raise_for_status()
            body = req.json()
            print("已获取IP属地")
            return bool(body["flag"])
    except:
        print("获取IP属地失败, 默认您位于中国大陆境内")
        return True


IS_CN: bool = check_ip()


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
