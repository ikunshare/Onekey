import os
from aiohttp import ClientError, ConnectionTimeoutError
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from .log import log

async def get(sha: str, path: str, repo: str, session, chunk_size: int = 1024) -> bytearray:
    if os.environ.get('IS_CN') == 'yes':
        url_list = [
            f'https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}',
            f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
            f'https://raw.gitmirror.com/{repo}/{sha}/{path}',
            f'https://raw.dgithub.xyz/{repo}/{sha}/{path}',
            f'https://gh.akass.cn/{repo}/{sha}/{path}'
        ]
    else:
        url_list = [
            f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
        ]
    retry = 3
    while retry > 0:
        for url in url_list:
            try:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('Content-Length', 0))
                        content = bytearray()

                        with Progress(
                            TextColumn("[progress.description]{task.description}", style="#66CCFF"),
                            BarColumn(style="#66CCFF", complete_style="#4CE49F", finished_style="#2FE9D9"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="#66CCFF"),
                            TimeElapsedColumn(),
                        ) as progress:
                            task = progress.add_task(f"下载{path}中...", total=total_size)

                            async for chunk in response.content.iter_chunked(chunk_size):
                                content.extend(chunk)
                                progress.update(task, advance=len(chunk))

                        return content
                    else:
                        log.error(f'获取失败: {path} - 状态码: {response.status}')
            except KeyboardInterrupt:
                log.info("\n 程序已退出")
            except ClientError as e:
                log.error(f'获取失败: {path} - 连接错误: {str(e)}')
            except ConnectionTimeoutError as e:
                log.error(f'连接超时: {url} - 错误: {str(e)}')

        retry -= 1
        log.warning(f'重试剩余次数: {retry} - {path}')

    log.error(f'超过最大重试次数: {path}')
    raise Exception(f'无法下载: {path}')
