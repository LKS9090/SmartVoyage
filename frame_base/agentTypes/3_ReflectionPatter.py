# -*- coding: utf-8 -*-
# ======================== 板块1：导入依赖模块 ========================
# 导入LangChain对接OpenAI API的Chat模型类（DeepSeek兼容该接口）
from langchain_openai import ChatOpenAI
# 导入LangChain核心的提示词模板类，用于构建结构化的Prompt
from langchain_core.prompts import ChatPromptTemplate
# 导入字符串输出解析器，用于将LLM的响应转换为纯字符串（便于后续处理）
from langchain_core.output_parsers import StrOutputParser
"""
这段代码基于 LangChain 框架对接 DeepSeek 大模型，实现了AI 回答的 “反思 - 优化” 闭环机制：
核心流程是先让模型针对用户问题生成初步回答，再接收用户对该回答的反馈（如指出不足、补充要求），
最后模型根据反馈反思自身回答的问题，生成更准确、更完善的优化版回答。
整个流程通过 LangChain 的 “Prompt 模板 + 模型调用 + 输出解析” 链式调用实现，模拟了 AI 自主反思、迭代优化回答的能力。
"""
# ======================== 板块2：DeepSeek API 配置 ========================
# --- DeepSeek API 配置 ---
# 请替换为你的 DeepSeek API 密钥
API_KEY = "sk-8d633094dd79409fad02d1aa83c6c84c"
# DeepSeek API的基础请求地址（兼容OpenAI API格式）
API_URL = "https://api.deepseek.com/v1"
# 指定要调用的DeepSeek模型名称
MODEL = "deepseek-chat"

# ======================== 板块3：初始化ChatOpenAI实例 ========================
# --- 步骤1: 初始化 ChatOpenAI ---
# 创建大模型实例，对接DeepSeek API（因DeepSeek兼容OpenAI格式，可直接用ChatOpenAI类）
llm = ChatOpenAI(
    model=MODEL,          # 指定使用的模型名称（deepseek-chat）
    api_key=API_KEY,      # 传入DeepSeek API密钥，用于身份验证
    base_url=API_URL,     # 指定DeepSeek的API地址，覆盖OpenAI默认地址
    temperature=0.8,      # 模型生成的随机性（0-1，值越高回答越灵活，0则更严谨）
    max_tokens=300        # 模型单次响应的最大令牌数，限制回答长度
)


# ======================== 板块4：自定义Prompt并构建链式调用 ========================
# --- 步骤2: 自定义 Prompt ---

# 2.1 初始响应 Prompt: 用于生成第一次的回答
# 构建初始回答的Prompt模板，仅接收{question}占位符（用户的原始问题）
initial_response_prompt = ChatPromptTemplate.from_template(
    "请根据以下问题给出你的初步回答: {question}"
)
# 构建初始回答的链式调用（Prompt模板 → LLM模型 → 字符串解析器）
# 链式调用是LangChain核心特性，| 符号表示“将前一步输出作为后一步输入”
initial_response_chain = initial_response_prompt | llm | StrOutputParser()

# 2.2 反思 Prompt: 用于接收用户反馈并优化回答
# 构建反思优化的Prompt模板，包含3个占位符：
# - {previous_response}: 模型之前生成的初步回答
# - {user_feedback}: 用户对初步回答的反馈
reflection_prompt = ChatPromptTemplate.from_template(
    """你是一个专业的、善于反思的AI助手。你之前给出了以下回答：
---
{previous_response}
---
现在，你收到了用户对你的回答给出的反馈：
---
{user_feedback}
---
请根据用户的反馈，认真反思你之前的回答，并生成一个更准确、更完善的新回答。
新回答:"""
)
# 构建反思优化的链式调用（反思Prompt → LLM模型 → 字符串解析器）
reflection_chain = reflection_prompt | llm | StrOutputParser()




# ======================== 板块5：定义反射优化核心函数 ========================
# --- 步骤3: 模拟反射过程 ---
def reflect_and_refine(query: str, feedback: str):
    """模拟一个完整的反射过程，从初始响应到优化后的响应。"""
    # 打印反射模式启动提示，便于查看流程进度
    print("--- 启动反射模式 ---")
    # 打印用户的原始查询，清晰展示当前处理的问题
    print(f"用户查询: {query}")

    # LLM 生成初步响应
    print("\n生成初步响应...")
    # 调用初始回答的链式调用，传入用户查询（字典格式，key对应Prompt中的{question}）
    initial_response = initial_response_chain.invoke({"question": query})
    # 打印模型生成的初步回答，便于对比优化前后的差异
    print(f"LLM 初步响应:\n{initial_response}")

    # 模拟用户反馈
    print(f"\n用户反馈:\n{feedback}")

    # LLM 进行反思，并生成新的回答
    print("\nLLM 正在反思并生成新响应...")
    # 调用反思优化的链式调用，传入两个参数：
    # - previous_response: 模型的初步回答
    # - user_feedback: 用户的反馈内容
    refined_response = reflection_chain.invoke({
        "previous_response": initial_response,
        "user_feedback": feedback
    })

    # 打印反思后的优化回答，展示最终结果
    print("\n--- LLM 经过反思后的新响应 ---")
    print(refined_response)

    # 返回优化后的回答，便于后续复用（如保存、进一步处理）
    return refined_response



# ======================== 板块6：测试运行反射流程 ========================
# --- 步骤4: 运行并测试 ---
# 主程序入口：仅当脚本直接运行时执行以下代码（导入时不执行）
if __name__ == "__main__":
    # 模拟用户查询：原始问题（要求介绍LangChain）
    initial_question = "请用一句话介绍一下 LangChain。"
    # 模拟用户反馈：指出初步回答的不足，要求补充核心概念和区别
    user_feedback_text = "你的回答太简单了，请更详细地解释一下 LangChain 的核心概念，比如 Agent 和 Chain 的区别。"

    # 运行反射过程：传入原始问题和用户反馈，触发“初始回答→反思→优化”全流程
    reflect_and_refine(initial_question, user_feedback_text)