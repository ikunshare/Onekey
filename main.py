import os
import asyncio

if __name__ == "__main__":
    try:
        from src.main import main

        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\n程序已退出")
    except Exception as e:
        print(f"错误：{e}")
    finally:
        os.system("pause")
