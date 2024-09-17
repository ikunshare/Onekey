import os
import time
import asyncio

from common.log import log
from common.stack_error import stack_error
from common.init_text import init
from common.main_func import main

lock = asyncio.Lock()
init()

repos = [
    'ikun0014/ManifestHub',
    'Auiowu/ManifestAutoUpdate',
    'tymolu233/ManifestAutoUpdate'
]

def get_app_id():
    log.info('App ID可以在SteamDB或Steam商店链接页面查看')
    return input("请输入游戏AppID：").strip()

if __name__ == '__main__':
    try:
        while True:
            app_id = get_app_id()
            asyncio.run(main(app_id, repos))
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        log.error(f' ⚠ 发生错误: {stack_error(e)}，将在5秒后退出')
        time.sleep(5)