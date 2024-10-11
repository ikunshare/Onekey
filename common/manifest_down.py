from aiohttp import ClientError
from tqdm.asyncio import tqdm_asyncio

from .log import log


async def get(sha: str, path: str, repo: str, session, chunk_size: int = 1024) -> bytearray:
    url_list = [
        f'https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}',
        f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
        f'https://raw.kkgithub.com/{repo}/{sha}/{path}',
        f'https://raw.dgithub.xyz/{repo}/{sha}/{path}',
        f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
    ]
    '''
    下载时间 (20MB 从小到大):
    https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path} - 0.95秒
    https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path} - 6.74秒
    https://raw.kkgithub.com/{repo}/{sha}/{path} - 6.76秒
    https://raw.dgithub.xyz/{repo}/{sha}/{path} - 8.30秒
    https://raw.gitmirror.com/{repo}/{sha}/{path} - 15.60秒
    https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{sha}/{path} - 16.59秒
    https://fastly.jsdelivr.net/gh/{repo}@{sha}/{path} - 20.08秒
    https://jsd.onmicrosoft.cn/gh/{repo}@{sha}/{path} - 22.07秒
    https://gitdl.cn/https://raw.githubusercontent.com/{repo}/{sha}/{path} - 47.33秒
    https://ghp.ci/https://raw.githubusercontent.com/{repo}/{sha}/{path} - 96.56秒
    https://raw.githubusercontent.com/{repo}/{sha}/{path} - 458.75秒
    https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path} - 下载时出错
    '''
    retry = 3
    while retry > 0:
        for url in url_list:
            try:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('Content-Length', 0))
                        content = bytearray()

                        with tqdm_asyncio(total=total_size, unit='B', unit_scale=True, desc=f'🔄 下载 {path}', colour='#ffadad') as pbar:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                content.extend(chunk)
                                pbar.update(len(chunk))
                        
                        return content
                    else:
                        log.error(f'🔄 获取失败: {path} - 状态码: {response.status}')
            except ClientError as e:
                log.error(f'🔄 获取失败: {path} - 连接错误: {str(e)}')
        
        retry -= 1
        log.warning(f'🔄 重试剩余次数: {retry} - {path}')
    
    log.error(f'🔄 超过最大重试次数: {path}')
    raise Exception(f'🔄 无法下载: {path}')
