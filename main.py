import os
import vdf
import winreg
import argparse
import requests
import traceback
import subprocess
import colorlog
import logging
import json
from pathlib import Path
from multiprocessing.pool import ThreadPool
from multiprocessing.dummy import Pool, Lock


def init_log():
    logger = logging.getLogger('Onekey')
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    fmt_string = '%(log_color)s[%(name)s][%(levelname)s]%(message)s'
    log_colors = {
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'purple'
    }
    fmt = colorlog.ColoredFormatter(fmt_string, log_colors=log_colors)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    return logger


def gen_config_file():
    default_config = {"Github_Persoal_Token": "", "Custom_Steam_Path": ""}
    with open('./config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f)
    log.info('程序可能为第一次启动，请填写配置文件后重新启动程序')


def load_config():
    if not os.path.exists('./config.json'):
        gen_config_file()
    else:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config


log = init_log()
config = load_config()
lock = Lock()

print('\033[1;32;40m  _____   __   _   _____   _   _    _____  __    __ \033[0m')
print('\033[1;32;40m /  _  \ |  \ | | | ____| | | / /  | ____| \ \  / /\033[0m')
print('\033[1;32;40m | | | | |   \| | | |__   | |/ /   | |__    \ \/ /\033[0m')
print('\033[1;32;40m | | | | | |\   | |  __|  | |\ \   |  __|    \  /')
print('\033[1;32;40m | |_| | | | \  | | |___  | | \ \  | |___    / /\033[0m')
print('\033[1;32;40m \_____/ |_|  \_| |_____| |_|  \_\ |_____|  /_/\033[0m')
log.info('作者ikun0014')
log.info('本项目基于wxy1343/ManifestAutoUpdate进行修改，采用GPL V3许可证')
log.info('版本：0.0.5')
log.info('项目仓库：https://github.com/ikunshare/Onekey')
log.warning('注意：据传Steam新版本对部分解锁工具进行了检测，但目前未发现问题，如果你被封号可以issue反馈')
log.warning('本项目完全免费，如果你在淘宝，QQ群内通过购买方式获得，赶紧回去骂商家死全家\n交流群组：\n点击链接加入群聊【ikun分享】：https://qm.qq.com/q/D9Uiva3RVS\nhttps://t.me/ikunshare_group')


def get_steam_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
    steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])
    custom_steam_path = config.get("Custom_Steam_Path", "")
    if not custom_steam_path == '':
        return Path(custom_steam_path)
    return steam_path


steam_path = get_steam_path()
isGreenLuma = any((steam_path / dll).exists() for dll in ['GreenLuma_2024_x86.dll', 'GreenLuma_2024_x64.dll', 'User32.dll'])
isSteamTools = (steam_path / 'config' / 'stplug-in').is_dir()


def get(sha, path):
    url_list = [
        f'https://gcore.jsdelivr.net/gh/{repo}@{sha}/{path}',
        f'https://fastly.jsdelivr.net/gh/{repo}@{sha}/{path}',
        f'https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path}',
        f'https://github.moeyy.xyz/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://ghproxy.org/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
    ]
    retry = 3
    while retry:
        for url in url_list:
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    return r.content
                else:
                    log.error(f'获取失败: {path} - 状态码: {r.status_code}')
            except requests.exceptions.ConnectionError:
                log.error(f'获取失败: {path} - 连接错误')
        retry -= 1
        log.warning(f'重试剩余次数: {retry} - {path}')
    log.error(f'超过最大重试次数: {path}')
    raise Exception(f'Failed to download: {path}')


def get_manifest(sha, path, steam_path: Path):
    collected_depots = []
    try:
        if path.endswith('.manifest'):
            depot_cache_path = steam_path / 'depotcache'
            with lock:
                if not depot_cache_path.exists():
                    depot_cache_path.mkdir(exist_ok=True)
            save_path = depot_cache_path / path
            if save_path.exists():
                with lock:
                    log.warning(f'已存在清单: {path}')
                return collected_depots
            content = get(sha, path)
            with lock:
                log.info(f'清单下载成功: {path}')
            with save_path.open('wb') as f:
                f.write(content)
        elif path == 'Key.vdf':
            content = get(sha, path)
            with lock:
                log.info(f'密钥下载成功: {path}')
            depots_config = vdf.loads(content.decode(encoding='utf-8'))
            for depot_id, depot_info in depots_config['depots'].items():
                collected_depots.append((depot_id, depot_info['DecryptionKey']))
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.error(f'处理失败: {path} - {str(e)}')
        traceback.print_exc()
        raise
    return collected_depots


def depotkey_merge(config_path, depots_config):
    if not config_path.exists():
        with lock:
            log.error('Steam默认配置不存在，可能是没有登录账号')
        return
    with open(config_path, encoding='utf-8') as f:
        config = vdf.load(f)
    software = config['InstallConfigStore']['Software']
    valve = software.get('Valve') or software.get('valve')
    steam = valve.get('Steam') or valve.get('steam')
    if 'depots' not in steam:
        steam['depots'] = {}
    steam['depots'].update(depots_config['depots'])
    with open(config_path, 'w', encoding='utf-8') as f:
        vdf.dump(config, f, pretty=True)
    return True


def stool_add(depot_data, app_id):
    lua_filename = f"Onekey_unlock_{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename

    with lock:
        log.info(f'SteamTools解锁文件生成: {lua_filepath}')
        with open(lua_filepath, "w", encoding="utf-8") as lua_file:
            lua_file.write(f'addappid({app_id}, 1, "None")\n')
            for depot_id, depot_key in depot_data:
                lua_file.write(f'addappid({depot_id}, 1, "{depot_key}")\n')

    luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
    subprocess.run([str(luapacka_path), str(lua_filepath)])
    os.remove(lua_filepath)
    return True


def greenluma_add(depot_id_list):
    app_list_path = steam_path / 'AppList'
    if app_list_path.is_file():
        app_list_path.unlink(missing_ok=True)
    if not app_list_path.is_dir():
        app_list_path.mkdir(parents=True, exist_ok=True)
    depot_dict = {}
    for i in app_list_path.iterdir():
        if i.stem.isdecimal() and i.suffix == '.txt':
            with i.open('r', encoding='utf-8') as f:
                app_id_ = f.read().strip()
                depot_dict[int(i.stem)] = None
                if app_id_.isdecimal():
                    depot_dict[int(i.stem)] = int(app_id_)
    for depot_id in depot_id_list:
        if int(depot_id) not in depot_dict.values():
            index = max(depot_dict.keys()) + 1 if depot_dict.keys() else 0
            if index != 0:
                for i in range(max(depot_dict.keys())):
                    if i not in depot_dict.keys():
                        index = i
                        break
            with (app_list_path / f'{index}.txt').open('w', encoding='utf-8') as f:
                f.write(str(depot_id))
            depot_dict[index] = int(depot_id)
    return True


def check_github_api_limit(headers):
    url = 'https://api.github.com/rate_limit'
    r = requests.get(url, headers=headers)
    remain_limit = r.json()['rate']['remaining']
    use_limit = r.json()['rate']['used']
    log.info(f'已用Github请求数：{use_limit}')
    log.info(f'剩余Github请求数：{remain_limit}')
    return True


def main(app_id):
    app_id_list = list(filter(str.isdecimal, app_id.strip().split('-')))
    app_id = app_id_list[0]
    github_token = config.get("Github_Persoal_Token", "")
    headers = {'Authorization': f'Bearer {github_token}'} if github_token else None

    if headers:
        check_github_api_limit(headers)

    url = f'https://api.github.com/repos/{repo}/branches/{app_id}'
    r = requests.get(url, headers=headers)
    if 'commit' in r.json():
        sha = r.json()['commit']['sha']
        url = r.json()['commit']['commit']['tree']['url']
        r = requests.get(url, headers=headers)
        if 'tree' in r.json():
            result_list = []
            collected_depots = []
            with Pool(32) as pool:
                pool: ThreadPool
                for i in r.json()['tree']:
                    result_list.append(pool.apply_async(get_manifest, (sha, i['path'], steam_path)))
                try:
                    for result in result_list:
                        collected_depots.extend(result.get())
                except KeyboardInterrupt:
                    with lock:
                        pool.terminate()
                    raise
            if collected_depots:
                if isSteamTools:
                    stool_add(collected_depots, app_id)
                    log.info('找到SteamTools，已添加解锁文件')
                if isGreenLuma:
                    greenluma_add([app_id])
                    depot_config = {'depots': {depot_id: {'DecryptionKey': depot_key} for depot_id, depot_key in collected_depots}}
                    depotkey_merge(steam_path / 'config' / 'config.vdf', depot_config)
                    log.info('找到GreenLuma，已添加解锁文件')
                log.info(f'入库成功: {app_id}')
                return True
    log.error(f'清单下载或生成.st失败: {app_id}')
    return False


parser = argparse.ArgumentParser()
parser.add_argument('-a', '--app-id')
args = parser.parse_args()
repo = 'ManifestHub/ManifestHub'
if __name__ == '__main__':
    try:
        log.debug('App ID可以在SteamDB或Steam商店链接页面查看')
        main(args.app_id or input('需要入库的App ID: '))
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        log.error(f'发生错误: {str(e)}')
        traceback.print_exc()
    if not args.app_id:
        os.system('pause')
