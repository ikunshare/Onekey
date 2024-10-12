import sys
import asyncio
import re
import platform

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

def check_system_msg():
    os_type = platform.system()
    try:
        if os_type != 'Windows':
            log.error(f'❌ 不用Windows你想上天？{os_type}')
            sys.quit()
    except Exception as e:
        log.error(f'❌ 获取系统类型失败：{stack_error(e)}')
        sys.quit()
    os_version = sys.getwindowsversion().major
    try:
        if os_version < 10:
            log.error(f'❌ 低于Windows10就别用了买台新电脑吧！当前版本：Windows {os_version}')
            sys.quit()
    except Exception as e:
        log.error(f'❌ 获取系统版本失败：{stack_error(e)}')
        sys.quit()

def prompt_app_id():
        app_id = input(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}🤔 请输入游戏AppID：{Style.RESET_ALL}").strip()
        if re.match(r'^\d+$', app_id):
            return app_id
        else:
            print(f"{Fore.RED}⚠ 无效的AppID，请输入数字！{Style.RESET_ALL}")

async def main_loop():
    while True:
        try:
            app_id = prompt_app_id()
            await main(app_id, repos)
        except EOFError:
            break

async def run():
    try:
        log.info('❗ App ID可以在SteamDB或Steam商店链接页面查看')
        await main_loop()
    except KeyboardInterrupt:
        log.info("👋 程序已退出")
    except Exception as e:
        log.error(f' ⚠ 发生错误: {stack_error(e)}，将在5秒后退出')
        await asyncio.sleep(5)
    finally:
        asyncio.get_event_loop().stop()

if __name__ == '__main__':
    try:
        check_system_msg()
        asyncio.run(run())
    except SystemExit:
        sys.exit()
