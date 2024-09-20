import os

from aiohttp import ClientSession

from common.config import config
from common.dkey_merge import depotkey_merge
from common.migration import migrate
from common.st_unlock import stool_add
from common.gl_unlock import greenluma_add
from common.get_manifest_info import get_manifest
from common.check import check_github_api_rate_limit
from common.log import log
from common.get_steam_path import steam_path
from common.stack_error import stack_error

isGreenLuma = any((steam_path / dll).exists() for dll in ['GreenLuma_2024_x86.dll', 'GreenLuma_2024_x64.dll', 'User32.dll'])
isSteamTools = (steam_path / 'config' / 'stUI').is_dir()

async def main(app_id, repos):
    app_id_list = list(filter(str.isdecimal, app_id.strip().split('-')))
    if not app_id_list:
        log.error(f'⚠  App ID无效')
        return False
    else:
        app_id = app_id_list[0]
    
    async with ClientSession() as session:
        github_token = config["Github_Personal_Token"]
        headers = {'Authorization': f'Bearer {github_token}'} if github_token else None
        latest_date = None
        selected_repo = None
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
                log.error(f'⚠ 获取分支信息失败: {stack_error(e)}')

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
                                    await migrate(st_use=True, session=session)
                                    await stool_add(collected_depots, app_id)
                                    log.info(' ✅ 找到SteamTools，已添加解锁文件')
                                if isGreenLuma:
                                    await migrate(st_use=False, session=session)
                                    await greenluma_add([app_id])
                                    depot_config = {'depots': {depot_id: {'DecryptionKey': depot_key} for depot_id, depot_key in collected_depots}}
                                    await depotkey_merge(steam_path / 'config' / 'config.vdf', depot_config)
                                    if await greenluma_add([int(i) for i in depot_config['depots'] if i.isdecimal()]):
                                        log.info('✅ 找到GreenLuma，已添加解锁文件')
                                log.info(f'✅ 清单最后更新时间：{date}')
                                log.info(f'✅ 入库成功: {app_id}')
                                os.system('pause')
                                return True
                            
        log.error(f'⚠ 清单下载或生成失败: {app_id}')
        os.system('pause')
        return False