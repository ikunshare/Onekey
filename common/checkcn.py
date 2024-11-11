import os
import aiohttp
import ujson as json
from .log import log
from .stack_error import stack_error


async def checkcn(client) -> bool:
    try:
        req = await client.get('https://mips.kugou.com/check/iscn?&format=json')
        body = json.loads(await req.read())
        scn = bool(body['flag'])
        if not scn:
            log.info(
                f"您在非中国大陆地区({body['country']})上使用了项目, 已自动切换回Github官方下载CDN")
            os.environ['IS_CN'] = 'no'
            return False
        else:
            os.environ['IS_CN'] = 'yes'
            return True

    except KeyboardInterrupt:
        log.info("程序已退出")
    except aiohttp.ClientError as e:
        os.environ['IS_CN'] = 'yes'
        log.warning('检查服务器位置失败，已忽略，自动认为你在中国大陆')
        log.warning(stack_error(e))
        return False
