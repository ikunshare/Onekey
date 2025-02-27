DEFAULT_CONFIG = {
    "Github_Personal_Token": "",
    "Custom_Steam_Path": "",
    "QA1": "Github Personal Token可在GitHub设置的Developer settings中生成",
    "教程": "https://ikunshare.com/Onekey_tutorial",
}

import platform
import sys
import os
import traceback
import logzero
import asyncio
import aiofiles
import httpx
import winreg
import ujson as json
import vdf
from typing import Any, Tuple, List, Dict
from pathlib import Path
from enum import Enum


class RepoChoice(Enum):
    IKUN = ("ikun0014/ManifestHub", "已断更的旧仓库")
    AUIOWU = ("Auiowu/ManifestAutoUpdate", "未知维护状态的仓库")
    STEAM_AUTO = ("SteamAutoCracks/ManifestHub", "官方推荐仓库")


DEFAULT_CONFIG = {
    "Github_Personal_Token": "",
    "Custom_Steam_Path": "",
    "QA1": "Github Personal Token可在GitHub设置的Developer settings中生成",
    "教程": "https://ikunshare.com/Onekey_tutorial",
}

DEFAULT_REPO = RepoChoice.STEAM_AUTO
WINDOWS_VERSIONS = ["10", "11"]
STEAM_REG_PATH = r"Software\Valve\Steam"
CONFIG_PATH = Path("./config.json")
LOCK = asyncio.Lock()
CLIENT = httpx.AsyncClient(verify=False, timeout=30)

log = logzero.setup_logger("Onekey")


def init() -> None:
    """初始化控制台输出"""
    banner = r"""
    _____   __   _   _____   _   _    _____  __    __ 
   /  _  \ |  \ | | | ____| | | / /  | ____| \ \  / /
   | | | | |   \| | | |__   | |/ /   | |__    \ \/ / 
   | | | | | |\   | |  __|  | |\ \   |  __|    \  /  
   | |_| | | | \  | | |___  | | \ \  | |___    / /   
   \_____/ |_|  \_| |_____| |_|  \_\ |_____|  /_/    
    """
    print(banner)
    print("作者: ikun0014 | 版本: 1.3.7 | 官网: ikunshare.com")
    print("项目仓库: GitHub: https://github.com/ikunshare/Onekey")
    print("提示: 请确保已安装最新版Windows 10/11并正确配置Steam")


def validate_windows_version() -> None:
    """验证Windows版本"""
    if platform.system() != "Windows":
        log.error("仅支持Windows操作系统")
        sys.exit(1)

    release = platform.uname().release
    if release not in WINDOWS_VERSIONS:
        log.error(f"需要Windows 10/11，当前版本: Windows {release}")
        sys.exit(1)


async def load_config() -> Dict[str, Any]:
    """异步加载配置文件"""
    if not CONFIG_PATH.exists():
        await generate_config()
        log.info("请填写配置文件后重新运行程序")
        sys.exit(0)

    try:
        async with aiofiles.open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.loads(await f.read())
    except json.JSONDecodeError:
        log.error("配置文件损坏，正在重新生成...")
        await generate_config()
        sys.exit(1)
    except Exception as e:
        log.error(f"配置加载失败: {str(e)}")
        sys.exit(1)


async def generate_config() -> None:
    """生成默认配置文件"""
    try:
        async with aiofiles.open(CONFIG_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False))
        log.info("配置文件已生成")
    except IOError as e:
        log.error(f"配置文件创建失败: {str(e)}")
        sys.exit(1)


def get_steam_path(config: Dict) -> Path:
    """获取Steam安装路径"""
    try:
        if custom_path := config.get("Custom_Steam_Path"):
            return Path(custom_path)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STEAM_REG_PATH) as key:
            return Path(winreg.QueryValueEx(key, "SteamPath")[0])
    except Exception as e:
        log.error(f"Steam路径获取失败: {str(e)}")
        sys.exit(1)


async def download_key(file_path: str, repo: str, sha: str) -> bytes:
    """下载密钥文件"""
    try:
        return await fetch_from_cdn(file_path, repo, sha)
    except Exception as e:
        log.error(f"密钥下载失败: {str(e)}")
        raise


async def handle_depot_files(
    repo: str, app_id: str, steam_path: Path
) -> List[Tuple[str, str]]:
    """处理清单文件和密钥"""
    collected = []
    try:
        async with httpx.AsyncClient() as client:
            branch_url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
            branch_res = await client.get(branch_url)
            branch_res.raise_for_status()

            tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
            tree_res = await client.get(tree_url)
            tree_res.raise_for_status()

            depot_cache = steam_path / "depotcache"
            depot_cache.mkdir(exist_ok=True)

            for item in tree_res.json()["tree"]:
                file_path = item["path"]
                if file_path.endswith(".manifest"):
                    await download_manifest(
                        file_path, depot_cache, repo, branch_res.json()["commit"]["sha"]
                    )
                elif "key.vdf" in file_path.lower():
                    key_content = await download_key(
                        file_path, repo, branch_res.json()["commit"]["sha"]
                    )
                    collected.extend(parse_key_vdf(key_content))
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        log.error(f"文件处理失败: {str(e)}")
    return collected


async def download_manifest(path: str, save_dir: Path, repo: str, sha: str) -> None:
    """下载清单文件"""
    save_path = save_dir / path
    if save_path.exists():
        log.warning(f"清单已存在: {path}")
        return

    content = await fetch_from_cdn(path, repo, sha)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)
    log.info(f"清单下载成功: {path}")


async def fetch_from_cdn(path: str, repo: str, sha: str) -> bytes:
    """从CDN获取资源"""
    mirrors = (
        [
            f"https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}",
            f"https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}",
            f"https://raw.gitmirror.com/{repo}/{sha}/{path}",
        ]
        if os.environ.get("IS_CN") == "yes"
        else [f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"]
    )

    for url in mirrors:
        try:
            res = await CLIENT.get(url)
            res.raise_for_status()
            return res.content
        except httpx.HTTPError:
            continue
    raise Exception("所有镜像源均不可用")


def parse_key_vdf(content: bytes) -> List[Tuple[str, str]]:
    """解析密钥文件"""
    try:
        depots = vdf.loads(content.decode("utf-8"))["depots"]
        return [(d_id, d_info["DecryptionKey"]) for d_id, d_info in depots.items()]
    except Exception as e:
        log.error(f"密钥解析失败: {str(e)}")
        return []


async def setup_unlock_tool(
    config: Dict, depot_data: List[Tuple[str, str]], app_id: str, tool_choice: int
) -> bool:
    """配置解锁工具"""
    if tool_choice == 1:
        return await setup_steamtools(config, depot_data, app_id)
    elif tool_choice == 2:
        return await setup_greenluma(config, depot_data)
    else:
        log.error("无效的工具选择")
        return False


async def setup_steamtools(
    config: Dict, depot_data: List[Tuple[str, str]], app_id: str
) -> bool:
    """配置SteamTools"""
    steam_path = (
        Path(config["Custom_Steam_Path"])
        if config.get("Custom_Steam_Path")
        else get_steam_path(config)
    )
    st_path = steam_path / "config" / "stplug-in"
    st_path.mkdir(exist_ok=True)

    lua_content = f'addappid({app_id}, 1, "None")\n'
    for d_id, d_key in depot_data:
        lua_content += f'addappid({d_id}, 1, "{d_key}")\n'

    lua_file = st_path / f"{app_id}.lua"
    async with aiofiles.open(lua_file, "w") as f:
        await f.write(lua_content)

    proc = await asyncio.create_subprocess_exec(
        str(st_path / "luapacka.exe"),
        str(lua_file),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.wait()

    if proc.returncode != 0:
        log.error(f"Lua编译失败: {await proc.stderr.read()}")
        return False
    return True


async def setup_greenluma(config: Dict, depot_data: List[Tuple[str, str]]) -> bool:
    """配置GreenLuma"""
    steam_path = (
        Path(config["Custom_Steam_Path"])
        if config.get("Custom_Steam_Path")
        else get_steam_path(config)
    )
    applist_dir = steam_path / "AppList"
    applist_dir.mkdir(exist_ok=True)

    for f in applist_dir.glob("*.txt"):
        f.unlink()

    for idx, (d_id, _) in enumerate(depot_data, 1):
        (applist_dir / f"{idx}.txt").write_text(str(d_id))

    config_path = steam_path / "config" / "config.vdf"
    async with aiofiles.open(config_path, "r+") as f:
        content = vdf.loads(await f.read())
        content.setdefault("depots", {}).update(
            {d_id: {"DecryptionKey": d_key} for d_id, d_key in depot_data}
        )
        await f.seek(0)
        await f.write(vdf.dumps(content))
    return True


async def main_flow():
    """主流程控制"""
    validate_windows_version()
    init()

    try:
        app_id = input("请输入游戏AppID: ").strip()
        if not app_id.isdigit():
            raise ValueError("无效的AppID")

        print(
            "\n".join(
                [f"{idx+1}. {item.value[1]}" for idx, item in enumerate(RepoChoice)]
            )
        )
        repo_choice = int(input("请选择清单仓库 (默认3): ") or 3)
        selected_repo = list(RepoChoice)[repo_choice - 1].value[0]

        tool_choice = int(input("请选择解锁工具 (1.SteamTools 2.GreenLuma): "))

        config = await load_config()
        steam_path = get_steam_path(config)
        depot_data = await handle_depot_files(selected_repo, app_id, steam_path)

        if await setup_unlock_tool(config, depot_data, app_id, tool_choice):
            log.info("游戏解锁配置成功！")
            if tool_choice == 1:
                log.info("请重启SteamTools生效")
            elif tool_choice == 2:
                log.info("请重启GreenLuma生效")
        else:
            log.error("配置失败，请检查日志")
    except Exception as e:
        log.error(f"运行错误: {str(e)}")
        log.debug(traceback.format_exc())
    finally:
        await CLIENT.aclose()


if __name__ == "__main__":
    asyncio.run(main_flow())
    os.system("pause")
