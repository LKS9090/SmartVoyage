#!/usr/bin/env python
import os
import sys
# 设置项目根目录以导入 MCP 库
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from mcp.server.fastmcp import FastMCP  # 导入 FastMCP 核心类

# 创建 MCP 实例，指定服务名称、日志级别、主机和端口
mcp = FastMCP("sdg", log_level="ERROR", host="127.0.0.1", port=8001)

# 定义工具：查询高频问题
@mcp.tool(
    name="query_high_frequency_question",
    description="Retrieves frequently asked questions (FAQ) from knowledge base."
)

async def query_high_frequency_question() -> str:
    """
    从知识库中获取高频问题及其答案。
    返回值：字符串，模拟 FAQ 结果。
    """
    try:
        print("调用查询高频问题的tool成功！！")
        return "高频问题是: 恐龙是怎么灭绝的？"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

# 定义工具：查询天气
@mcp.tool(
    name="get_weather",
    description="查询天气"
)
async def get_weather() -> str:
    """
    查询天气的工具。
    返回值：字符串，模拟天气结果。
    """
    try:
        print("调用查询天气的tools")
        return "北京的天气是多云"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise



def main():
    """
    启动 Streamable HTTP 服务器。
    """
    print("正在启动MCP Streamable服务器...")
    print("服务器将在 http://localhost:8001 上运行")
    print("按 Ctrl+C 停止服务器")
    try:
        mcp.run(transport="streamable-http")  # 使用 streamable-http 传输方式
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")

if __name__ == "__main__":
    main()