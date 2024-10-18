import time
from aiohttp import ClientError, ConnectionTimeoutError
from .log import log
from .stack_error import stack_error

async def check_github_api_rate_limit(headers, session):
    try:
        async with session.get('https://api.github.com/rate_limit', headers=headers, ssl=False) as r:
            r_json = await r.json()

            if r.status == 200:
                rate_limit = r_json.get('rate', {})
                remaining_requests = rate_limit.get('remaining', 0)
                reset_time = rate_limit.get('reset', 0)
                reset_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
                
                log(f'🔄 剩余请求次数: {remaining_requests}')

                if remaining_requests == 0:
                    log(f'⚠ GitHub API 请求数已用尽, 将在 {reset_time_formatted} 重置,建议生成一个填在配置文件里')
            else:
                log('⚠ Github请求数检查失败, 网络错误')
    except KeyboardInterrupt:
        log("👋 程序已退出")
    except ClientError as e:
        log(f'⚠ 检查Github API 请求数失败,{stack_error(e)}')
    except ConnectionTimeoutError as e:
        log(f'⚠ 检查Github API 请求数超时: {stack_error(e)}')
    except Exception as e:
        log(f'⚠ 发生错误: {stack_error(e)}')
