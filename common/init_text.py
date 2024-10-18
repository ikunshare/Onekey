from terminaltexteffects.effects.effect_print import Print

from .log import log

def init():
    text = (
        "  _____   __   _   _____   _   _    _____  __    __ \n"
        " /  _  \\ |  \\ | | | ____| | | / /  | ____| \\ \\  / /\n"
        " | | | | |   \\| | | |__   | |/ /   | |__    \\ \\/ /\n"
        " | | | | | |\\   | |  __|  | |\\ \\   |  __|    \\  / \n"
        " | |_| | | | \\  | | |___  | | \\ \\  | |___    / / \n"
        " \\_____/ |_|  \\_| |_____| |_|  \\_\\ |_____|  /_/  "
    )
    
    effect = Print(text)
    
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)
    
    log(f'作者: ikun0014')
    log(f'本项目采用GNU General Public License v3开源许可证，请勿用于商业用途')
    log('版本: 1.3.0')
    log(f'项目Github仓库: https://github.com/ikunshare/Onekey')
    log('官网: ikunshare.com')
    log('本项目完全开源免费, 如果你在淘宝, QQ群内通过购买方式获得, 赶紧回去骂商家死全家\n交流群组:\n    https://t.me/ikunshare_qun')
    log('如果本项目中的Emoji(即表情包)无法正常显示, 请使用支持Emoji的终端(例如Windows Terminal)')
