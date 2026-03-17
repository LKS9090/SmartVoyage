from python_a2a import A2AClient, Message, MessageRole, TextContent

# 创建 A2AClient 实例，指向服务器 URL
client = A2AClient(
    endpoint_url="http://127.0.0.1:5009",
    timeout=30  # 设置超时
)
# 创建一个测试消息
message = Message(
    content=TextContent(text="我想预订从上海到北京的火车票"),
    role=MessageRole.USER
)
# 发送消息并获取响应
try:
    response = client.send_message(message)
    # 打印响应字典
    print("服务器响应：")
    print(response.to_dict())
except Exception as e:
    print("错误：", str(e))

"""
服务器响应：
{'content': {'text': '我想预订从上海到北京的火车票', 'type': <ContentType.TEXT: 'text'>}, 'role': 'agent', 'message_id': '36cdd213-18b2-4006-b107-e246cacf9ec0', 'parent_message_id': '26ec5409-73c8-4d2d-b1a1-697e63c4feb9'}
解析：
content: "我想预订从上海到北京"  │
│ message_id: 26ec5... (生成)  
服务器返回的消息：
Message                         │
│ role: agent                    │
│ content: "我想预订..." (⚠️)    │
│ message_id: 36cdd... (新 ID)   │
│ parent_message_id: 26ec5... 
"""