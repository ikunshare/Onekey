from aiohttp import ClientError
from .log import log

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