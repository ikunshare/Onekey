from pathlib import Path
import aiofiles
import vdf

from .log import log
from .manifest_down import get
from .stack_error import stack_error


async def get_manifest(sha, path, steam_path: Path, repo, session):
    collected_depots = []
    try:
        if path.endswith('.manifest'):
            depot_cache_path = steam_path / 'depotcache'
            depot_cache_path.mkdir(exist_ok=True) if not depot_cache_path.exists() else None
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
            depots_config = vdf.loads(content.decode('utf-8'))
            
            for depot_id, depot_info in depots_config['depots'].items():
                collected_depots.append((depot_id, depot_info['DecryptionKey']))
                
    except Exception as e:
        log.error(f'处理失败: {path} - {stack_error(e)}')
        raise
        
    return collected_depots