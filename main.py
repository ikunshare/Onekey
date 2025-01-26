import sys
import os
import traceback
import time
import logging
import subprocess
import asyncio
import aiofiles
import colorlog
import httpx
import winreg
import ujson as json
import vdf
from typing import Any
from pathlib import Path
from colorama import init, Fore, Back, Style

init()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

lock = asyncio.Lock()
client = httpx.AsyncClient(verify=False)


DEFAULT_CONFIG = {
    "Github_Personal_Token": "",
    "Custom_Steam_Path": "",
    "QA1": "温馨提示: Github_Personal_Token可在Github设置的最底下开发者选项找到, 详情看教程",
    "教程": "https://ikunshare.com/Onekey_tutorial"
}

LOG_FORMAT = '%(log_color)s%(message)s'
LOG_COLORS = {
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'purple',
}


def init_log(level=logging.DEBUG) -> logging.Logger:
    """ 初始化日志模块 """
    logger = logging.getLogger('Onekey')
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    fmt = colorlog.ColoredFormatter(LOG_FORMAT, log_colors=LOG_COLORS)
    stream_handler.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(stream_handler)

    return logger


log = init_log()


def init():
    """ 输出初始化信息 """
    banner_lines = [
        "  _____   __   _   _____   _   _    _____  __    __ ",
        " /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /",
        " | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /",
        " | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / ",
        " | |_| | | | \\  | | |___  | | \\ \\  | |___    / /",
        " \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/",
    ]
    for line in banner_lines:
        log.info(line)

    log.info('作者: ikun0014')
    log.warning('本项目采用GNU General Public License v3开源许可证, 请勿用于商业用途')
    log.info('版本: 1.3.6')
    log.info(
        '项目Github仓库: https://github.com/ikunshare/Onekey \n Gitee: https://gitee.com/ikun0014/Onekey'
    )
    log.info('官网: ikunshare.com')
    log.warning(
        '本项目完全开源免费, 如果你在淘宝, QQ群内通过购买方式获得, 赶紧回去骂商家死全家\n   交流群组:\n    https://t.me/ikunshare_qun'
    )
    log.info('App ID可以在SteamDB, SteamUI或Steam商店链接页面查看')


def stack_error(exception: Exception) -> str:
    """ 处理错误堆栈 """
    stack_trace = traceback.format_exception(
        type(exception), exception, exception.__traceback__)
    return ''.join(stack_trace)


async def gen_config_file():
    """ 生成配置文件 """
    try:
        async with aiofiles.open("./config.json", mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False, escape_forward_slashes=False))

        log.info('程序可能为第一次启动或配置重置,请填写配置文件后重新启动程序')
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'配置文件生成失败,{stack_error(e)}')


async def load_config() -> dict:
    """ 加载配置文件 """
    if not os.path.exists('./config.json'):
        await gen_config_file()
        os.system('pause')
        sys.exit()

    try:
        async with aiofiles.open("./config.json", mode="r", encoding="utf-8") as f:
            config = json.loads(await f.read())
            return config
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f"配置文件加载失败，原因: {stack_error(e)},重置配置文件中...")
        os.remove("./config.json")
        await gen_config_file()
        os.system('pause')
        sys.exit()

config = asyncio.run(load_config())


async def check_github_api_rate_limit(headers):
    """ 检查Github请求数 """

    if headers != None:
        log.info(f"您已配置Github Token")

    url = 'https://api.github.com/rate_limit'
    try:
        r = await client.get(url, headers=headers)
        r_json = r.json()
        if r.status_code == 200:
            rate_limit = r_json.get('rate', {})
            remaining_requests = rate_limit.get('remaining', 0)
            reset_time = rate_limit.get('reset', 0)
            reset_time_formatted = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
            log.info(f'剩余请求次数: {remaining_requests}')
            if remaining_requests == 0:
                log.warning(f'GitHub API 请求数已用尽, 将在 {reset_time_formatted} 重置,建议生成一个填在配置文件里')
        else:
            log.error('Github请求数检查失败, 网络错误')
    except KeyboardInterrupt:
        log.info("程序已退出")
    except httpx.ConnectError as e:
        log.error(f'检查Github API 请求数失败, {stack_error(e)}')
    except httpx.ConnectTimeout as e:
        log.error(f'检查Github API 请求数超时: {stack_error(e)}')
    except Exception as e:
        log.error(f'发生错误: {stack_error(e)}')


async def checkcn() -> bool:
    try:
        req = await client.get('https://mips.kugou.com/check/iscn?&format=json')
        body = req.json()
        scn = bool(body['flag'])
        if (not scn):
            log.info(
                f"您在非中国大陆地区({body['country']})上使用了项目, 已自动切换回Github官方下载CDN")
            os.environ['IS_CN'] = 'no'
            return False
        else:
            os.environ['IS_CN'] = 'yes'
            return True
    except KeyboardInterrupt:
        log.info("程序已退出")
    except httpx.ConnectError as e:
        os.environ['IS_CN'] = 'yes'
        log.warning('检查服务器位置失败，已忽略，自动认为你在中国大陆')
        log.warning(stack_error(e))
        return False


async def depotkey_merge(config_path: Path, depots_config: dict) -> bool:
    if not config_path.exists():
        async with lock:
            log.error('Steam默认配置不存在, 可能是没有登录账号')
        return False

    try:
        async with aiofiles.open(config_path, encoding='utf-8') as f:
            content = await f.read()

        config = vdf.loads(content)
        steam = config.get('InstallConfigStore', {}).get('Software', {}).get('Valve') or config.get('InstallConfigStore', {}).get('Software', {}).get('valve')

        if steam is None:
            log.error('找不到Steam配置, 请检查配置文件')
            return False

        depots = steam.setdefault('depots', {})
        depots.update(depots_config.get('depots', {}))

        async with aiofiles.open(config_path, mode='w', encoding='utf-8') as f:
            new_context = vdf.dumps(config, pretty=True)
            await f.write(new_context)

        log.info('成功合并')
        return True
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        async with lock:
            log.error(f'合并失败, 原因: {e}')
        return False


async def get(sha: str, path: str, repo: str):
    if os.environ.get('IS_CN') == 'yes':
        url_list = [
            f'https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}',
            f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
            f'https://raw.gitmirror.com/{repo}/{sha}/{path}',
            f'https://raw.dgithub.xyz/{repo}/{sha}/{path}',
            f'https://gh.akass.cn/{repo}/{sha}/{path}'
        ]
    else:
        url_list = [
            f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
        ]
    retry = 3
    while retry > 0:
        for url in url_list:
            try:
                r = await client.get(url, timeout=30)
                if r.status_code == 200:
                    return r.read()
                else:
                    log.error(f'获取失败: {path} - 状态码: {r.status_code}')
            except KeyboardInterrupt:
                log.info("程序已退出")
            except httpx.ConnectError as e:
                log.error(f'获取失败: {path} - 连接错误: {str(e)}')
            except httpx.ConnectTimeout as e:
                log.error(f'连接超时: {url} - 错误: {str(e)}')

        retry -= 1
        log.warning(f'重试剩余次数: {retry} - {path}')

    log.error(f'超过最大重试次数: {path}')
    raise Exception(f'无法下载: {path}')


async def get_manifest(sha: str, path: str, steam_path: Path, repo: str) -> list:
    collected_depots = []
    depot_cache_path = steam_path / 'depotcache'
    try:
        depot_cache_path.mkdir(exist_ok=True)
        if path.endswith('.manifest'):
            save_path = depot_cache_path / path
            if save_path.exists():
                log.warning(f'已存在清单: {save_path}')
                return collected_depots
            content = await get(sha, path, repo)
            log.info(f'清单下载成功: {path}')
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(content)
        elif path == 'Key.vdf':
            content = await get(sha, path, repo)
            log.info(f'密钥下载成功: {path}')
            depots_config = vdf.loads(content.decode('utf-8'))
            depots = dict(depots_config.get('depots'))
            collected_depots = [
                (depot_id, depot_info['DecryptionKey'])
                for depot_id, depot_info in depots.items()
            ]
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'处理失败: {path} - {stack_error(e)}')
        raise
    return collected_depots


def get_steam_path() -> Path:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
        steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])

        custom_steam_path = config.get("Custom_Steam_Path", "").strip()
        return Path(custom_steam_path) if custom_steam_path else steam_path
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'Steam路径获取失败, {stack_error(e)}, 请检查是否正确安装Steam')
        os.system('pause')
        return Path()


SP = get_steam_path()
GL = any((SP / dll).exists() for dll in ['GreenLuma_2024_x86.dll', 'GreenLuma_2024_x64.dll', 'User32.dll'])
ST = (SP / 'config' / 'stUI').is_dir()
ST_PT = Path(SP) / "config" / "stplug-in"
TP = Path('./temp')
ST_STP_URL = 'https://steamtools.net/res/SteamtoolsSetup.exe'
STP_FILE = TP / 'SteamtoolsSetup.exe'


async def download_setup_file() -> None:
    log.info('开始下载 SteamTools 安装程序...')
    try:
        r = await client.get(ST_STP_URL, timeout=30)
        if r.status_code == 200:
            async with aiofiles.open(STP_FILE, mode='wb') as f:
                await f.write(r.read())
            log.info('安装程序下载完成')
        else:
            log.error(f'网络错误，无法下载安装程序，状态码: {r.status_code}')
    except KeyboardInterrupt:
        log.info("程序已退出")
    except httpx.ConnectTimeout:
        log.error('下载时超时')
    except Exception as e:
        log.error(f'下载失败: {e}')


async def migrate() -> None:
    try:
        log.info('检测到你正在使用 SteamTools,尝试迁移旧文件')
        if SP.exists():
            for file in SP.iterdir():
                if file.is_file() and file.name.startswith("Onekey_unlock_"):
                    new_filename = file.name[len("Onekey_unlock_"):]
                    try:
                        file.rename(SP / new_filename)
                        log.info(f'Renamed: {file.name} -> {new_filename}')
                    except Exception as e:
                        log.error(
                            f'重命名失败 {file.name} -> {new_filename}: {e}')
        else:
            log.error('故障,正在重新安装 SteamTools')
            TP.mkdir(parents=True, exist_ok=True)
            await download_setup_file(client)
            subprocess.run(str(STP_FILE), check=True)
            for file in TP.iterdir():
                file.unlink()
            TP.rmdir()
    except KeyboardInterrupt:
        log.info("程序已退出")


async def stool_add(depot_data: list, app_id: str) -> bool:
    lua_filename = f"{app_id}.lua"
    lua_filepath = SP / "config" / "stplug-in" / lua_filename
    async with lock:
        log.info(f'SteamTools 解锁文件生成: {lua_filepath}')
        try:
            async with aiofiles.open(lua_filepath, mode="w", encoding="utf-8") as lua_file:
                await lua_file.write(f'addappid({app_id}, 1, "None")\n')
                for depot_id, depot_key in depot_data:
                    await lua_file.write(f'addappid({depot_id}, 1, "{depot_key}")\n')
            luapacka_path = SP / "config" / "stplug-in" / "luapacka.exe"
            log.info(f'正在处理文件: {lua_filepath}')
            result = subprocess.run(
                [str(luapacka_path), str(lua_filepath)],
                capture_output=True
            )
            if result.returncode != 0:
                log.error(f'调用失败: {result.stderr.decode()}')
                return False
            log.info('处理完成')
        except KeyboardInterrupt:
            log.info("程序已退出")
        except Exception as e:
            log.error(f'处理过程出现错误: {e}')
            return False
        finally:
            if lua_filepath.exists():
                os.remove(lua_filepath)
                log.info(f'删除临时文件: {lua_filepath}')
    return True


async def greenluma_add(depot_id_list: list) -> bool:
    app_list_path = SP / 'AppList'
    try:
        app_list_path.mkdir(parents=True, exist_ok=True)
        for file in app_list_path.glob('*.txt'):
            file.unlink(missing_ok=True)
        depot_dict = {
            int(i.stem): int(i.read_text(encoding='utf-8').strip())
            for i in app_list_path.iterdir() if i.is_file() and i.stem.isdecimal() and i.suffix == '.txt'
        }
        for depot_id in map(int, depot_id_list):
            if depot_id not in depot_dict.values():
                index = max(depot_dict.keys(), default=-1) + 1
                while index in depot_dict:
                    index += 1
                (app_list_path /
                 f'{index}.txt').write_text(str(depot_id), encoding='utf-8')
                depot_dict[index] = depot_id
        return True
    except Exception as e:
        print(f'处理时出错: {e}')
        return False


async def fetch_branch_info(url, headers) -> str | None:
    try:
        r = await client.get(url, headers=headers)
        return r.json()
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'获取信息失败: {stack_error(e)}')
        return None
    except httpx.ConnectTimeout as e:
        log.error(f'获取信息时超时: {stack_error(e)}')
        return None


async def get_latest_repo_info(repos: list, app_id: str, headers) -> Any | None:
    latest_date = None
    selected_repo = None
    for repo in repos:
        url = f'https://api.github.com/repos/{repo}/branches/{app_id}'
        r_json = await fetch_branch_info(url, headers)
        if r_json and 'commit' in r_json:
            date = r_json['commit']['commit']['author']['date']
            if (latest_date is None) or (date > latest_date):
                latest_date = date
                selected_repo = repo

    return selected_repo, latest_date


async def main(app_id: str, repos: list) -> bool:
    app_id_list = list(filter(str.isdecimal, app_id.strip().split('-')))
    if not app_id_list:
        log.error(f'App ID无效')
        return False
    app_id = app_id_list[0]
    github_token = config.get("Github_Personal_Token", "")
    headers = {'Authorization': f'Bearer {github_token}'} if github_token else None
    await checkcn()
    await check_github_api_rate_limit(headers)
    selected_repo, latest_date = await get_latest_repo_info(repos, app_id, headers)
    if (selected_repo):
        log.info(f'选择清单仓库: {selected_repo}')
        url = f'https://api.github.com/repos/{selected_repo}/branches/{app_id}'
        r_json = await fetch_branch_info(url, headers)
        if (r_json) and ('commit' in r_json):
            sha = r_json['commit']['sha']
            url = r_json['commit']['commit']['tree']['url']
            r2_json = await fetch_branch_info(url, headers)
            if (r2_json) and ('tree' in r2_json):
                collected_depots = []
                for item in r2_json['tree']:
                    result = await get_manifest(sha, item['path'], SP, selected_repo)
                    collected_depots.extend(result)
                if collected_depots:
                    if ST:
                        await migrate()
                        await stool_add(collected_depots, app_id)
                        log.info('找到SteamTools, 已添加解锁文件')
                    elif GL:
                        await greenluma_add([app_id])
                        depot_config = {'depots': {depot_id: {'DecryptionKey': depot_key} for depot_id, depot_key in collected_depots}}
                        await depotkey_merge(SP / 'config' / 'config.vdf', depot_config)
                        if await greenluma_add([int(i) for i in depot_config['depots'] if i.isdecimal()]):
                            log.info('找到GreenLuma, 已添加解锁文件')
                    log.info(f'清单最后更新时间: {latest_date}')
                    log.info(f'入库成功: {app_id}')
                    await client.aclose()
                    os.system('pause')
                    return True
    log.error(f'清单下载或生成失败: {app_id}')
    await client.aclose()
    os.system('pause')
    return False


if __name__ == '__main__':
    init()
    try:
        repos = [
            'ikun0014/ManifestHub',
            'Auiowu/ManifestAutoUpdate',
        ]
        app_id = input(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}请输入游戏AppID: {Style.RESET_ALL}").strip()
        asyncio.run(main(app_id, repos))
    except KeyboardInterrupt:
        log.info("程序已退出")
    except SystemExit:
        sys.exit()
