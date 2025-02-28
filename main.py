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
import time
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

client = httpx.AsyncClient(verify=False)
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


CONFIG = asyncio.run(load_config())
GITHUB_TOKEN = str(CONFIG.get("Github_Personal_Token", ""))
if GITHUB_TOKEN:
    masked_token = f"{GITHUB_TOKEN[:3]}***" if len(GITHUB_TOKEN) > 3 else "***"
    log.info(f"你的Github Token: {masked_token}")
else:
    log.info("未配置Github Token")
HEADER = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else None


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


async def checkcn() -> bool:
    try:
        req = await client.get("https://mips.kugou.com/check/iscn?&format=json")
        body = req.json()
        scn = bool(body["flag"])
        if not scn:
            log.info(
                f"您在非中国大陆地区({body['country']})上使用了项目, 已自动切换回Github官方下载CDN"
            )
            os.environ["IS_CN"] = "no"
            return False
        else:
            os.environ["IS_CN"] = "yes"
            return True
    except KeyboardInterrupt:
        log.info("程序已退出")
    except httpx.ConnectError as e:
        os.environ["IS_CN"] = "yes"
        log.warning("检查服务器位置失败，已忽略，自动认为你在中国大陆")
        return False


def stack_error(exception: Exception) -> str:
    """处理错误堆栈"""
    stack_trace = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )
    return "".join(stack_trace)


async def check_github_api_rate_limit(headers):
    """检查Github请求数"""

    if headers != None:
        log.info(f"您已配置Github Token")

    url = "https://api.github.com/rate_limit"
    try:
        r = await client.get(url, headers=headers)
        r_json = r.json()
        if r.status_code == 200:
            rate_limit = r_json.get("rate", {})
            remaining_requests = rate_limit.get("remaining", 0)
            reset_time = rate_limit.get("reset", 0)
            reset_time_formatted = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(reset_time)
            )
            log.info(f"剩余请求次数: {remaining_requests}")
            if remaining_requests == 0:
                log.warning(
                    f"GitHub API 请求数已用尽, 将在 {reset_time_formatted} 重置,建议生成一个填在配置文件里"
                )
        else:
            log.error("Github请求数检查失败, 网络错误")
    except KeyboardInterrupt:
        log.info("程序已退出")
    except httpx.ConnectError as e:
        log.error(f"检查Github API 请求数失败, {stack_error(e)}")
    except httpx.ConnectTimeout as e:
        log.error(f"检查Github API 请求数超时: {stack_error(e)}")
    except Exception as e:
        log.error(f"发生错误: {stack_error(e)}")


async def handle_depot_files(
    repo: str, app_id: str, steam_path: Path
) -> List[Tuple[str, str]]:
    """处理清单文件和密钥"""
    collected = []
    depot_map = {}
    try:
        branch_url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
        branch_res = await client.get(branch_url, headers=HEADER)
        branch_res.raise_for_status()

        tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
        tree_res = await client.get(tree_url)
        tree_res.raise_for_status()

        depot_cache = steam_path / "depotcache"
        depot_cache.mkdir(exist_ok=True)

        for item in tree_res.json()["tree"]:
            file_path = str(item["path"])
            if file_path.endswith(".manifest"):
                save_path = depot_cache / file_path
                if save_path.exists():
                    log.warning(f"已存在清单: {save_path}")
                    continue
                content = await fetch_from_cdn(
                    branch_res.json()["commit"]["sha"], file_path, repo
                )
                log.info(f"清单下载成功: {file_path}")
                async with aiofiles.open(save_path, "wb") as f:
                    await f.write(content)
            elif "key.vdf" in file_path.lower():
                key_content = await fetch_from_cdn(
                    branch_res.json()["commit"]["sha"], file_path, repo
                )
                collected.extend(parse_key_vdf(key_content))

        for item in tree_res.json()["tree"]:
            if not item["path"].endswith(".manifest"):
                continue

            filename = Path(item["path"]).stem
            if "_" not in filename:
                continue

            depot_id, manifest_id = filename.replace(".manifest", "").split("_", 1)
            if not (depot_id.isdigit() and manifest_id.isdigit()):
                continue

            depot_map.setdefault(depot_id, []).append(manifest_id)

        for depot_id in depot_map:
            depot_map[depot_id].sort(key=lambda x: int(x), reverse=True)

    except httpx.HTTPStatusError as e:
        log.error(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        log.error(f"文件处理失败: {str(e)}")
    return collected, depot_map


async def fetch_from_cdn(sha: str, path: str, repo: str):
    if os.environ.get("IS_CN") == "yes":
        url_list = [
            f"https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}",
            f"https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}",
            f"https://raw.gitmirror.com/{repo}/{sha}/{path}",
            f"https://raw.dgithub.xyz/{repo}/{sha}/{path}",
            f"https://gh.akass.cn/{repo}/{sha}/{path}",
        ]
    else:
        url_list = [f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"]
    retry = 3
    while retry > 0:
        for url in url_list:
            try:
                r = await client.get(url, headers=HEADER, timeout=30)
                if r.status_code == 200:
                    return r.read()
                else:
                    log.error(f"获取失败: {path} - 状态码: {r.status_code}")
            except KeyboardInterrupt:
                log.info("程序已退出")
            except httpx.ConnectError as e:
                log.error(f"获取失败: {path} - 连接错误: {str(e)}")
            except httpx.ConnectTimeout as e:
                log.error(f"连接超时: {url} - 错误: {str(e)}")

        retry -= 1
        log.warning(f"重试剩余次数: {retry} - {path}")

    log.error(f"超过最大重试次数: {path}")
    raise Exception(f"无法下载: {path}")


def parse_key_vdf(content: bytes) -> List[Tuple[str, str]]:
    """解析密钥文件"""
    try:
        depots = vdf.loads(content.decode("utf-8"))["depots"]
        return [(d_id, d_info["DecryptionKey"]) for d_id, d_info in depots.items()]
    except Exception as e:
        log.error(f"密钥解析失败: {str(e)}")
        return []


async def setup_unlock_tool(
    config: Dict,
    depot_data: List[Tuple[str, str]],
    app_id: str,
    tool_choice: int,
    depot_map: Dict,
) -> bool:
    """配置解锁工具"""
    if tool_choice == 1:
        return await setup_steamtools(config, depot_data, app_id, depot_map)
    elif tool_choice == 2:
        return await setup_greenluma(config, depot_data)
    else:
        log.error("无效的工具选择")
        return False


async def setup_steamtools(
    config: Dict, depot_data: List[Tuple[str, str]], app_id: str, depot_map: Dict
) -> bool:
    """配置SteamTools"""
    steam_path = (
        Path(config["Custom_Steam_Path"])
        if config.get("Custom_Steam_Path")
        else get_steam_path(config)
    )
    st_path = steam_path / "config" / "stplug-in"
    st_path.mkdir(exist_ok=True)

    choice = input(f"是否锁定版本（推荐在选择仓库3时使用）？(y/n): ").lower()

    if choice == "y":
        versionlock = True
    else:
        versionlock = False

    lua_content = f'addappid({app_id}, 1, "None")\n'
    for d_id, d_key in depot_data:
        if versionlock:
            for manifest_id in depot_map[d_id]:
                lua_content += f'addappid({d_id}, 1, "{d_key}")\nsetManifestid({d_id},"{manifest_id}")\n'
        else:
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

    if lua_file.exists():
        os.remove(lua_file)
        log.info(f"删除临时文件: {lua_file}")

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
    await checkcn()
    init()

    try:
        app_id = input("请输入游戏AppID: ").strip()
        if not app_id.isdigit():
            raise ValueError("无效的AppID")

        await check_github_api_rate_limit(HEADER)

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
        depot_data, depot_map = await handle_depot_files(
            selected_repo, app_id, steam_path
        )

        if await setup_unlock_tool(config, depot_data, app_id, tool_choice, depot_map):
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
        await client.aclose()
        os.system("pause")


if __name__ == "__main__":
    try:
        asyncio.run(main_flow())
    except asyncio.CancelledError:
        os.system("pause")
    except KeyboardInterrupt:
        os.system("pause")
