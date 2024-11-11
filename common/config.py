import os
import sys
import asyncio
import ujson as json
import aiofiles
from .stack_error import stack_error
from .log import log

DEFAULT_CONFIG = {
    "Github_Personal_Token": "",
    "Custom_Steam_Path": "",
    "QA1": "温馨提示: Github_Personal_Token可在Github设置的最底下开发者选项找到，详情看教程",
    "教程": "https://ikunshare.com/Onekey_tutorial"
}


async def gen_config_file():
    try:
        async with aiofiles.open("./config.json", mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False, escape_forward_slashes=False))

        log.info('程序可能为第一次启动或配置重置,请填写配置文件后重新启动程序')
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f'配置文件生成失败,{stack_error(e)}')


async def load_config():
    if not os.path.exists('./config.json'):
        await gen_config_file()
        os.system('pause')
        sys.exit()

    try:
        async with aiofiles.open("./config.json", mode="r", encoding="utf-8") as f:
            config = json.loads(await f.read())
            return config
    except KeyboardInterrupt:
        log.info("程序已退出")
    except Exception as e:
        log.error(f"配置文件加载失败，原因: {stack_error(e)},重置配置文件中...")
        os.remove("./config.json")
        await gen_config_file()
        os.system('pause')
        sys.exit()

config = asyncio.run(load_config())
