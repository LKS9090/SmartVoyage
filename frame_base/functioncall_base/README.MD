## Function call


```python  
tools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "sql查询",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "str",
                        "description": "第一个str参数，sql语句"
                    },
                },
                "required": ["sql"]
            }
        }
    }
]
```


```python Function Calling JSON:
Function_Calling_JSON={
  "tool_calls": [
    {
      "id": "call_0_5a621a97-e7d8-4ca0-b124-30e9c68e0f37",
      "name": "ask_database",
      "args": {
        "query": "SELECT COUNT(*) AS total_movies FROM movies;"
      }
    }
  ]
}