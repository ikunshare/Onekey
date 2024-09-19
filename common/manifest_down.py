from aiohttp import ClientError
from tqdm.asyncio import tqdm_asyncio

from .log import log


async def get(sha, path, repo, session):
    url_list = [
        f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
        f'https://jsd.onmicrosoft.cn/gh/{repo}@{sha}/{path}',
        # f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',
    ]
    retry = 3
    while retry:
        for url in url_list:
            try:
                async with session.get(url, ssl=False) as r:
                    if r.status == 200:
                        total_size = int(r.headers.get('Content-Length', 0))
                        chunk_size = 1024
                        content = bytearray()

                        with tqdm_asyncio(total=total_size, unit='B', unit_scale=True, desc=f'下载 {path}', colour='#ffadad') as pbar:
                            async for chunk in r.content.iter_chunked(chunk_size):
                                content.extend(chunk)
                                pbar.update(len(chunk))
                        
                        return content
                    else:
                        log.error(f' 🔄 获取失败: {path} - 状态码: {r.status}')
            except ClientError:
                log.error(f' 🔄 获取失败: {path} - 连接错误')
        retry -= 1
        log.warning(f' 🔄 重试剩余次数: {retry} - {path}')
    log.error(f' 🔄 超过最大重试次数: {path}')
    raise Exception(f' 🔄 无法下载: {path}')
