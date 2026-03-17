from python_a2a import Task, TaskStatus, TaskState, Message, MessageRole, TextContent

# 创建任务
message = Message(content=TextContent(text="查询天气"), role=MessageRole.USER)
task = Task(message=message.to_dict())
print(task)
"""
Task(id='9e3be136-2a43-4cad-9918-f4b18b1aa0a1', session_id='c71babbf-68de-46bb-b546-5f0619a54871', 
status=TaskStatus(state=<TaskState.SUBMITTED: 'submitted'>, message=None, timestamp='2026-03-10T07:01:54.829015'), 
message={'content': {'text': '查询天气', 'type': <ContentType.TEXT: 'text'>}, 'role': 'user', 
'message_id': '7137e725-9f8c-4ff8-980e-115d8c29d2b0'}, history=[], artifacts=[], metadata={})
"""
# 处理中更新状态
task.status = TaskStatus(state=TaskState.WAITING, message={"info": "调用工具"})

# 完成任务
# task.artifacts = [{"parts": [{"type": "text", "text": "晴天"}]}]
task.status = TaskStatus(state=TaskState.COMPLETED)

# 序列化输出
print(task.to_dict())