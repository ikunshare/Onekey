import os
import vdf
import aiofiles
import traceback
import time
import asyncio
from common import log, config, getsteampath, stunlock, glunlock, stack_error
from aiohttp import ClientSession, ClientError
from pathlib import Path

log = log.log
config = config.config
lock = asyncio.Lock()
steam_path = getsteampath.steam_path
isGreenLuma = any((steam_path / dll).exists() for dll in ['GreenLuma_2024_x86.dll', 'GreenLuma_2024_x64.dll', 'User32.dll'])
isSteamTools = (steam_path / 'config' / 'stplug-in').is_dir()
stunlock = stunlock.stunlock
glunlock = glunlock.glunlock
stack_error = stack_error.stack_error

print('\033[1;32;40m  _____   __   _   _____   _   _    _____  __    __ ' + '\033[0m')
print('\033[1;32;40m /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /' + '\033[0m')
print('\033[1;32;40m | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /' + '\033[0m')
print('\033[1;32;40m | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / ' + '\033[0m')
print('\033[1;32;40m | |_| | | | \\  | | |___  | | \\ \\  | |___    / /' + '\033[0m')
print('\033[1;32;40m \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/' + '\033[0m')
log.info('作者ikun0014')
log.info('本项目基于wxy1343/ManifestAutoUpdate进行修改，采用ACSL许可证')
log.info('版本：1.1.6')
log.info('项目仓库：https://github.com/ikunshare/Onekey')
log.info('官网：ikunshare.com')
log.warning('本项目完全开源免费，如果你在淘宝，QQ群内通过购买方式获得，赶紧回去骂商家死全家\n交流群组：\n点击链接加入群聊【𝗶𝗸𝘂𝗻分享】：https://qm.qq.com/q/d7sWovfAGI\nhttps://t.me/ikunshare_group')

# 下载清单
async def get(sha, path, repo, session):
    url_list = [
        # f'https://gh.api.99988866.xyz/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
        f'https://jsd.onmicrosoft.cn/gh/{repo}@{sha}/{path}',
        f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://gh.jiasu.in/https://raw.githubusercontent.com/{repo}/{sha}/{path}'
    ]
    retry = 3
    while retry:
        for url in url_list:
            try:
                async with session.get(url, ssl=False) as r:
                    if r.status == 200:
                        return await r.read()
                    else:
                        log.error(f' 🔄 获取失败: {path} - 状态码: {r.status}')
            except ClientError:
                log.error(f' 🔄 获取失败: {path} - 连接错误')
        retry -= 1
        log.warning(f'  🔄  重试剩余次数: {retry} - {path}')
    log.error(f'  🔄 超过最大重试次数: {path}')
    raise Exception(f'  🔄 无法下载: {path}')

# 获取清单信息
async def get_manifest(sha, path, steam_path: Path, repo, session):
    collected_depots = []
    try:
        if path.endswith('.manifest'):
            depot_cache_path = steam_path / 'depotcache'
            if not depot_cache_path.exists():
                depot_cache_path.mkdir(exist_ok=True)
            save_path = depot_cache_path / path
            if save_path.exists():
                log.warning(f'👋已存在清单: {path}')
                return collected_depots
            content = await get(sha, path, repo, session)
            log.info(f' 🔄 清单下载成功: {path}')
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(content)
        elif path == 'Key.vdf':
            content = await get(sha, path, repo, session)
            log.info(f' 🔄 密钥下载成功: {path}')
            depots_config = vdf.loads(content.decode(encoding='utf-8'))
            for depot_id, depot_info in depots_config['depots'].items():
                collected_depots.append((depot_id, depot_info['DecryptionKey']))
    except Exception as e:
        log.error(f'处理失败: {path} - {stack_error(e)}')
        traceback.print_exc()
        raise
    return collected_depots

# 合并DecryptionKey
async def depotkey_merge(config_path, depots_config):
    if not config_path.exists():
        async with lock:
            log.error(' 👋 Steam默认配置不存在，可能是没有登录账号')
        return
    async with aiofiles.open(config_path, encoding='utf-8') as f:
        config = vdf.load(f)
    software = config['InstallConfigStore']['Software']
    valve = software.get('Valve') or software.get('valve')
    steam = valve.get('Steam') or valve.get('steam')
    if 'depots' not in steam:
        steam['depots'] = {}
    steam['depots'].update(depots_config['depots'])
    async with aiofiles.open(config_path, mode='w', encoding='utf-8') as f:
        vdf.dump(config, f, pretty=True)
    return True

async def check_github_api_rate_limit(headers, session):
    url = 'https://api.github.com/rate_limit'

    async with session.get(url, headers=headers, ssl=False) as r:
        if not r == None:
            r_json = await r.json()
        else:
            log.error('孩子，你怎么做到的？')
            os.system('pause')

    if r.status == 200:
        rate_limit = r_json['rate']
        remaining_requests = rate_limit['remaining']
        reset_time = rate_limit['reset']
        reset_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
        log.info(f' 🔄 剩余请求次数: {remaining_requests}')
    else:
        log.error('Github请求数检查失败')

    if remaining_requests == 0:
        log.warning(f' ⚠ GitHub API 请求数已用尽，将在 {reset_time_formatted} 重置, 不想等生成一个填配置文件里')

# 主函数
async def main(app_id):
    app_id_list = list(filter(str.isdecimal, app_id.strip().split('-')))
    app_id = app_id_list[0]
    
    async with ClientSession() as session:
        github_token = config["Github_Personal_Token"]
        headers = {'Authorization': f'Bearer {github_token}'} if github_token else None
        latest_date = None
        selected_repo = None

        # 检查Github API限额
        await check_github_api_rate_limit(headers, session)

        for repo in repos:
            url = f'https://api.github.com/repos/{repo}/branches/{app_id}'
            try:
                async with session.get(url, headers=headers, ssl=False) as r:
                    r_json = await r.json()
                    if 'commit' in r_json:
                        date = r_json['commit']['commit']['author']['date']
                        if latest_date is None or date > latest_date:
                            latest_date = date
                            selected_repo = repo
            except Exception as e:
                log.error(f' ⚠ 获取分支信息失败: {stack_error(e)}')
                traceback.print_exc()
        if selected_repo:
            log.info(f' 🔄 选择清单仓库：{selected_repo}')
            url = f'https://api.github.com/repos/{selected_repo}/branches/{app_id}'
            async with session.get(url, headers=headers, ssl=False) as r:
                r_json = await r.json()
                if 'commit' in r_json:
                    sha = r_json['commit']['sha']
                    url = r_json['commit']['commit']['tree']['url']
                    async with session.get(url, headers=headers, ssl=False) as r2:
                        r2_json = await r2.json()
                        if 'tree' in r2_json:
                            collected_depots = []
                            for i in r2_json['tree']:
                                result = await get_manifest(sha, i['path'], steam_path, selected_repo, session)
                                collected_depots.extend(result)
                            if collected_depots:
                                if isSteamTools:
                                    await stunlock(collected_depots, app_id)
                                    log.info(' ✅ 找到SteamTools，已添加解锁文件')
                                if isGreenLuma:
                                    await glunlock([app_id])
                                    depot_config = {'depots': {depot_id: {'DecryptionKey': depot_key} for depot_id, depot_key in collected_depots}}
                                    await depotkey_merge(steam_path / 'config' / 'config.vdf', depot_config)
                                    if await glunlock([int(i) for i in depot_config['depots'] if i.isdecimal()]):
                                        log.info(' ✅ 找到GreenLuma，已添加解锁文件')
                                log.info(f' ✅ 清单最后更新时间：{date}')
                                log.info(f' ✅ 入库成功: {app_id}')
                                os.system('pause')
                                return True
        log.error(f' ⚠ 清单下载或生成失败: {app_id}')
        os.system('pause')
        return False

repos = [
         'ManifestHub/ManifestHub',
         'ikun0014/ManifestHub',
         'Auiowu/ManifestAutoUpdate',
         'tymolu233/ManifestAutoUpdate'
        ]
if __name__ == '__main__':
    try:
        log.info('App ID可以在SteamDB或Steam商店链接页面查看')
        app_id = input("请输入游戏AppID：").strip()
        asyncio.run(main(app_id))
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        log.error(f' ⚠ 发生错误: {stack_error(e)}')
        traceback.print_exc()