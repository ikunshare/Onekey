from colorama import Fore, Back, Style, init

init()

from .log import log

def init():
    banner_lines = [
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}  _____   __   _   _____   _   _    _____  __    __ {Style.RESET_ALL}",
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /{Style.RESET_ALL}",
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /{Style.RESET_ALL}",
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / {Style.RESET_ALL}",
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} | |_| | | | \\  | | |___  | | \\ \\  | |___    / /{Style.RESET_ALL}",
        f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT} \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/{Style.RESET_ALL}",
    ]
    for line in banner_lines:
        print(line)
    
    log.info(f'作者: {Fore.RED}{Back.BLACK}{Style.BRIGHT}ikun0014{Style.RESET_ALL}')
    log.info(f'{Fore.RED}{Back.BLACK}{Style.BRIGHT}本项目采用GNU General Public License v3开源许可证，请勿用于商业用途{Style.RESET_ALL}')
    log.info('版本: 1.3.0')
    log.info(f'{Fore.RED}{Back.BLACK}{Style.BRIGHT}项目Github仓库: https://github.com/ikunshare/Onekey{Style.RESET_ALL}')
    log.info('官网: ikunshare.com')
    log.warning('本项目完全开源免费, 如果你在淘宝, QQ群内通过购买方式获得, 赶紧回去骂商家死全家\n交流群组:\n    https://t.me/ikunshare_qun')
    log.warning('如果本项目中的Emoji(即表情包)无法正常显示, 请使用支持Emoji的终端(例如Windows Terminal)')
