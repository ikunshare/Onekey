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
        content = await f.read()
        
    config = vdf.loads(content)
    software = config['InstallConfigStore']['Software']
    valve = software.get('Valve') or software.get('valve')
    steam = valve.get('Steam') or valve.get('steam')
    
    steam.setdefault('depots', {}).update(depots_config['depots'])
    
    async with aiofiles.open(config_path, mode='w', encoding='utf-8') as f:
        new_content = vdf.dumps(config, pretty=True)
        await f.write(new_content)
        
    return True
