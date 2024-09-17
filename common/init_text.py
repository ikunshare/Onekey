from colorama import Fore, Back, Style, init

init()

from .log import log

def init():
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}  _____   __   _   _____   _   _    _____  __    __ {Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / {Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | |_| | | | \\  | | |___  | | \\ \\  | |___    / /{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/{Style.RESET_ALL}")
    log.info('作者ikun0014')
    log.info('本项目采用GNU General Public License v3开源许可证')
    log.info('版本：1.2.2')
    log.info('项目仓库：https://github.com/ikunshare/Onekey')
    log.info('官网：ikunshare.com')
    log.warning('本项目完全开源免费，如果你在淘宝，QQ群内通过购买方式获得，赶紧回去骂商家死全家\n交流群组：\nhttps://qm.qq.com/q/d7sWovfAGI\nhttps://t.me/ikunshare_group')