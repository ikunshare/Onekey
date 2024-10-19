import sys
import asyncio
import re

from colorama import Fore, Back, Style
from colorama import init as cinit
from common.log import log
from common.stack_error import stack_error
from common.init_text import init
from common.main_func import main

lock = asyncio.Lock()

init()
cinit()

repos = [
    'ikun0014/ManifestHub',
    'Auiowu/ManifestAutoUpdate',
    'tymolu233/ManifestAutoUpdate',
]

def prompt_app_id():
    while True:
        app_id = input(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}请输入游戏AppID: {Style.RESET_ALL}").strip()
        if re.match(r'^\d+$', app_id):
            return app_id
        else:
            print(f"{Fore.RED}无效的AppID, 请输入数字!{Style.RESET_ALL}")

async def main_loop():
    while True:
        try:
            app_id = prompt_app_id()
            await main(app_id, repos)
        except KeyboardInterrupt:
            log.info("程序已退出")
        except EOFError:
            break

async def run():
    try:
        log.info('App ID可以在SteamDB或Steam商店链接页面查看')
        await main_loop()
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'发生错误: {stack_error(e)}, 将在5秒后退出')
        await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("程序已退出")
    except SystemExit:
        sys.exit()
