import ujson as json
import aiofiles
from . import log
import os
import sys
import asyncio

log = log.log

# 生成配置文件
async def gen_config_file():
    default_config ={
                    "Github_Personal_Token": "",
                    "Custom_Steam_Path": "",
                    "QA1": "温馨提示：Github_Personal_Token可在Github设置的最底下开发者选项找到，详情看教程",
                    "教程": "https://lyvx-my.sharepoint.com/:w:/g/personal/ikun_ikunshare_com/EWqIqyCElLNLo_CKfLbqix0BWU_O03HLzEHQKHdJYrUz-Q?e=79MZjw"
                    }
    async with aiofiles.open("./config.json", mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(default_config, indent=2, ensure_ascii=False,
                escape_forward_slashes=False))
        await f.close()
    log.info(' 🖱️ 程序可能为第一次启动，请填写配置文件后重新启动程序')


# 加载配置文件
async def load_config():
    if not os.path.exists('./config.json'):
        await gen_config_file()
        os.system('pause')
        sys.exit()
    else:
        async with aiofiles.open("./config.json", mode="r", encoding="utf-8") as f:
            config = json.loads(await f.read())
            return config
        
config = asyncio.run(load_config())