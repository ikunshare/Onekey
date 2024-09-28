import asyncio
import aiofiles
import vdf
from pathlib import Path
from .log import log

lock = asyncio.Lock()

async def depotkey_merge(config_path: Path, depots_config: dict) -> bool:
    if not config_path.exists():
        async with lock:
            log.error('👋 Steam默认配置不存在，可能是没有登录账号')
        return False

    try:
        async with aiofiles.open(config_path, encoding='utf-8') as f:
            content = await f.read()
        
        config = vdf.loads(content)
        software = config.get('InstallConfigStore', {}).get('Software', {})
        steam = software.get('Valve') or software.get('valve')
        if steam is None:
            log.error('⚠ 找不到Steam配置，请检查配置文件')
            return False
        
        if 'depots' not in steam:
            steam['depots'] = {}
        
        steam['depots'].update(depots_config.get('depots', {}))
        
        async with aiofiles.open(config_path, mode='w', encoding='utf-8') as f:
            new_content = vdf.dumps(config, pretty=True)
            await f.write(new_content)

        log.info('✅ 成功合并')
        return True
        
    except Exception as e:
        async with lock:
            log.error(f'❗ 合并失败，原因: {e}')
        return False
