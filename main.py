import os
import sys
import traceback
import asyncio
import aiofiles
import httpx
import vdf
import time
from typing import Any, Tuple, List, Dict
from pathlib import Path
from common import log, variable
from common.variable import (
    CLIENT,
    HEADER,
    STEAM_PATH,
    REPO_LIST,
)


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


LOCK = asyncio.Lock()
LOG = log.log("Onekey")
DEFAULT_REPO = REPO_LIST[0]


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
    LOG.info(banner)
    LOG.info("作者: ikun0014 | 版本: 1.4.4 | 官网: ikunshare.com")
    LOG.info("项目仓库: GitHub: https://github.com/ikunshare/Onekey")
    LOG.warning("ikunshare.com | 严禁倒卖")
    LOG.warning("提示: 请确保已安装Windows 10/11并正确配置Steam;SteamTools/GreenLuma")
    LOG.warning("开梯子必须配置Token, 你的IP我不相信能干净到哪")


async def checkcn() -> bool:
    try:
        req = await CLIENT.get("https://mips.kugou.com/check/iscn?&format=json")
        body = req.json()
        scn = bool(body["flag"])
        if not scn:
            LOG.info(
                f"您在非中国大陆地区({body['country']})上使用了项目, 已自动切换回Github官方下载CDN"
            )
            variable.IS_CN = False
            return False
        else:
            variable.IS_CN = True
            return True
    except KeyboardInterrupt:
        LOG.info("程序已退出")
        return True
    except httpx.ConnectError as e:
        variable.IS_CN = True
        LOG.warning("检查服务器位置失败，已忽略，自动认为你在中国大陆")
        return False


def stack_error(exception: Exception) -> str:
    stack_trace = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )
    return "".join(stack_trace)


async def check_github_api_rate_limit(headers):
    url = "https://api.github.com/rate_limit"
    try:
        r = await CLIENT.get(url, headers=headers)
        r_json = r.json()
        if r.status_code == 200:
            rate_limit = r_json.get("rate", {})
            remaining_requests = rate_limit.get("remaining", 0)
            reset_time = rate_limit.get("reset", 0)
            reset_time_formatted = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(reset_time)
            )
            LOG.info(f"剩余请求次数: {remaining_requests}")
            if remaining_requests == 0:
                LOG.warning(
                    f"GitHub API 请求数已用尽, 将在 {reset_time_formatted} 重置,建议生成一个填在配置文件里"
                )
        else:
            LOG.error("Github请求数检查失败, 网络错误")
    except KeyboardInterrupt:
        LOG.info("程序已退出")
    except httpx.ConnectError as e:
        LOG.error(f"检查Github API 请求数失败, {stack_error(e)}")
    except httpx.ConnectTimeout as e:
        LOG.error(f"检查Github API 请求数超时: {stack_error(e)}")
    except Exception as e:
        LOG.error(f"发生错误: {stack_error(e)}")


async def get_latest_repo_info(repos: list, app_id: str, headers) -> Any | str | None:
    latest_date = None
    selected_repo = None
    for repo in repos:
        url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
        r = await CLIENT.get(url, headers=headers)
        r_json = r.json()
        if r_json and "commit" in r_json:
            date = r_json["commit"]["commit"]["author"]["date"]
            if (latest_date is None) or (date > latest_date):
                latest_date = str(date)
                selected_repo = str(repo)
    return selected_repo, latest_date


async def handle_depot_files(
    repos: List, app_id: str, steam_path: Path
) -> List[Tuple[str, str]]:
    collected = []
    depot_map = {}
    try:
        selected_repo, latest_date = await get_latest_repo_info(
            repos, app_id, headers=HEADER
        )  # type: ignore

        if selected_repo:
            branch_url = (
                f"https://api.github.com/repos/{selected_repo}/branches/{app_id}"
            )
            branch_res = await CLIENT.get(branch_url, headers=HEADER)
            branch_res.raise_for_status()

            tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
            tree_res = await CLIENT.get(tree_url)
            tree_res.raise_for_status()

            depot_cache = steam_path / "depotcache"
            depot_cache.mkdir(exist_ok=True)

            LOG.info(f"当前选择清单仓库: https://github.com/{selected_repo}")
            LOG.info(f"此清单分支上次更新时间：{latest_date}")

            for item in tree_res.json()["tree"]:
                file_path = str(item["path"])
                if file_path.endswith(".manifest"):
                    save_path = depot_cache / file_path
                    if save_path.exists():
                        LOG.warning(f"已存在清单: {save_path}")
                        continue
                    content = await fetch_from_cdn(
                        branch_res.json()["commit"]["sha"], file_path, selected_repo
                    )
                    LOG.info(f"清单下载成功: {file_path}")
                    async with aiofiles.open(save_path, "wb") as f:
                        await f.write(content)
                elif "key.vdf" in file_path.lower():
                    key_content = await fetch_from_cdn(
                        branch_res.json()["commit"]["sha"], file_path, selected_repo
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
        LOG.error(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        LOG.error(f"文件处理失败: {str(e)}")
    return collected, depot_map  # type: ignore


async def fetch_from_cdn(sha: str, path: str, repo: str):
    if variable.IS_CN:
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
                r = await CLIENT.get(url, headers=HEADER, timeout=30)
                if r.status_code == 200:
                    return r.read()
                else:
                    LOG.error(f"获取失败: {path} - 状态码: {r.status_code}")
            except KeyboardInterrupt:
                LOG.info("程序已退出")
            except httpx.ConnectError as e:
                LOG.error(f"获取失败: {path} - 连接错误: {str(e)}")
            except httpx.ConnectTimeout as e:
                LOG.error(f"连接超时: {url} - 错误: {str(e)}")

        retry -= 1
        LOG.warning(f"重试剩余次数: {retry} - {path}")

    LOG.error(f"超过最大重试次数: {path}")

    raise Exception(f"无法下载: {path}")


def parse_key_vdf(content: bytes) -> List[Tuple[str, str]]:
    try:
        depots = vdf.loads(content.decode("utf-8"))["depots"]
        return [(d_id, d_info["DecryptionKey"]) for d_id, d_info in depots.items()]
    except Exception as e:
        LOG.error(f"密钥解析失败: {str(e)}")
        return []


async def setup_unlock_tool(
    depot_data: List[Tuple[str, str]],
    app_id: str,
    tool_choice: int,
    depot_map: Dict,
) -> bool:
    isGreenLuma = any(
        (STEAM_PATH / dll).exists()
        for dll in ["GreenLuma_2024_x86.dll", "GreenLuma_2024_x64.dll", "User32.dll"]
    )
    isSteamTools = (STEAM_PATH / "config" / "stUI").is_dir()

    if (tool_choice == 1) and (isSteamTools):
        return await setup_steamtools(depot_data, app_id, depot_map)
    elif (tool_choice == 2) and (isGreenLuma):
        return await setup_greenluma(depot_data)
    else:
        LOG.error("你选的啥？")
        return False


async def setup_steamtools(
    depot_data: List[Tuple[str, str]], app_id: str, depot_map: Dict
) -> bool:
    st_path = STEAM_PATH / "config" / "stplug-in"
    st_path.mkdir(exist_ok=True)

    choice = input(f"是否锁定版本(推荐在选择仓库1时使用)?(y/n): ").lower()

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
        LOG.error(f"Lua编译失败: {await proc.stderr.read()}")  # type: ignore
        return False

    if lua_file.exists():
        os.remove(lua_file)
        LOG.info(f"删除临时文件: {lua_file}")

    return True


async def setup_greenluma(depot_data: List[Tuple[str, str]]) -> bool:
    applist_dir = STEAM_PATH / "AppList"
    applist_dir.mkdir(exist_ok=True)

    for f in applist_dir.glob("*.txt"):
        f.unlink()

    for idx, (d_id, _) in enumerate(depot_data, 1):
        (applist_dir / f"{idx}.txt").write_text(str(d_id))

    config_path = STEAM_PATH / "config" / "config.vdf"
    async with aiofiles.open(config_path, "r+") as f:
        content = vdf.loads(await f.read())
        content.setdefault("depots", {}).update(
            {d_id: {"DecryptionKey": d_key} for d_id, d_key in depot_data}
        )
        await f.seek(0)
        await f.write(vdf.dumps(content))
    return True


async def main_flow(app_id: str):
    app_id_list = list(filter(str.isdecimal, app_id.strip().split("-")))
    if not app_id_list:
        LOG.error(f"App ID无效")
        os.system("pause")
        return False

    app_id = app_id_list[0]

    try:
        await checkcn()
        await check_github_api_rate_limit(HEADER)

        tool_choice = int(input("请选择解锁工具 (1.SteamTools 2.GreenLuma): "))
        depot_data, depot_map = await handle_depot_files(REPO_LIST, app_id, STEAM_PATH)

        if await setup_unlock_tool(depot_data, app_id, tool_choice, depot_map):  # type: ignore
            LOG.info("游戏解锁配置成功！")
            LOG.info("重启Steam后生效")
        else:
            LOG.error("配置失败")

        os.system("pause")
        return True
    except Exception as e:
        LOG.error(f"运行错误: {stack_error(e)}")
        return False
    except KeyboardInterrupt:
        return False
    finally:
        await CLIENT.aclose()
        return True


if __name__ == "__main__":
    try:
        init()
        app_id = input(f"请输入游戏AppID: ").strip()
        asyncio.run(main_flow(app_id))
    except (asyncio.CancelledError, KeyboardInterrupt):
        os.system("pause")
    except Exception as e:
        LOG.error(f"错误：{stack_error(e)}")
        os.system("pause")
