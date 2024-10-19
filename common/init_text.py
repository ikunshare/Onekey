from colorama import Fore, Back, Style, init

init()

from .log import log

def init():
    banner_lines = [
        f"  _____   __   _   _____   _   _    _____  __    __ ",
        f" /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /",
        f" | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /",
        f" | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / ",
        f" | |_| | | | \\  | | |___  | | \\ \\  | |___    / /",
        f" \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/",
    ]
    for line in banner_lines:
        log.info(line)
    
    log.info(f'作者: ikun0014')
    log.warning(f'本项目采用GNU General Public License v3开源许可证，请勿用于商业用途')
    log.info(f'版本: 1.3.0')
    log.info(f'项目Github仓库: https://github.com/ikunshare/Onekey')
    log.info(f'官网: ikunshare.com')
    log.warning(f'本项目完全开源免费, 如果你在淘宝, QQ群内通过购买方式获得, 赶紧回去骂商家死全家\n   交流群组:\n    https://t.me/ikunshare_qun')