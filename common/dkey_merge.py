import asyncio
import aiofiles
import vdf
from .log import log

lock = asyncio.Lock()

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