#!/usr/bin/env python
import asyncio
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 提高日志级别以捕获更多信息
    format='[客户端] %(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """
    客户端异步主函数
    """
    # 定义服务器地址
    server_url = "http://127.0.0.1:8001/mcp"
    logging.info(f"准备连接到 Streamable-HTTP 服务器: {server_url}")

    try:
        # 建立连接
        async with streamablehttp_client(server_url) as (read, write, _):
            logging.info("连接已成功建立！")

            # 创建并初始化会话
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                    logging.info("会话初始化成功，可以开始调用工具。")

                    # 调用远程工具
                    logging.info("--> 正在调用工具: query_high_frequency_question")
                    response_faq = await session.call_tool("query_high_frequency_question", {})
                    print("-" * 30)
                    print(response_faq)
                    logging.info(f"<-- 收到响应: {response_faq}")

                    print("-" * 30)

                    logging.info("--> 正在调用工具: get_weather")
                    response_weather = await session.call_tool("get_weather", {})
                    print("-" * 30)
                    print(response_weather)
                    logging.info(f"<-- 收到响应: {response_weather}")
                except Exception as e:
                    logging.error(f"调用工具时发生错误: {e}", exc_info=True)  # 打印完整异常堆栈
                    raise
    except Exception as e:
        logging.error(f"连接或会话初始化时发生错误: {e}", exc_info=True)  # 打印完整异常堆栈
        logging.error("请确认服务端脚本已启动并运行在 http://127.0.0.1:8001/mcp")
        raise
    logging.info("客户端任务完成，连接已关闭。")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"客户端运行失败: {e}", exc_info=True)  # 打印完整异常堆栈