from pathlib import Path
import aiofiles
import vdf

from .log import log
from .manifest_down import get
from .stack_error import stack_error


async def get_manifest(sha: str, path: str, steam_path: Path, repo: str, session) -> list:
    collected_depots = []
    depot_cache_path = steam_path / 'depotcache'
    
    try:
        depot_cache_path.mkdir(exist_ok=True)

        if path.endswith('.manifest'):
            save_path = depot_cache_path / path
            if save_path.exists():
                log(f'👋 已存在清单: {save_path}')
                return collected_depots

            content = await get(sha, path, repo, session)
            log(f'🔄 清单下载成功: {path}')

            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(content)

        elif path == 'Key.vdf':
            content = await get(sha, path, repo, session)
            log(f'🔄 密钥下载成功: {path}')

            depots_config = vdf.loads(content.decode('utf-8'))
            collected_depots = [
                (depot_id, depot_info['DecryptionKey'])
                for depot_id, depot_info in depots_config['depots'].items()
            ]

    except KeyboardInterrupt:
        log("👋 程序已退出")
    except Exception as e:
        log(f'❌ 处理失败: {path} - {stack_error(e)}')
        raise

    return collected_depots
