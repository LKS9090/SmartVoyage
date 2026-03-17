
#定义配置文件
class Config(object):
    def __init__(self):
        #大模型信息
        self.api_key="sk-945138b82e0e4f7da47f498400c94f05"
        self.api_url="https://api.deepseek.com/v1"
        self.model_name="deepseek-chat" #支持function call
        # self.model_name="deepseek-reasoner"  # 不支持function call
        #https://api-docs.deepseek.com/zh-cn/guides/reasoning_model

        #数据库信息
        self.db_host="localhost"
        self.db_port=3307
        self.db_user="root"
        self.db_password="123456"
        self.db_database="insurance_db"

