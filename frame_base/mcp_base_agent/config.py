
#定义配置文件
class Config(object):
    def __init__(self):
        #大模型信息
        self.api_key="sk-8d633094dd79409fad02d1aa83c6c84c"
        self.base_url="https://api.deepseek.com/v1"
        self.model_name="deepseek-chat" #支持function call
        # self.model_name="deepseek-reasoner"  # 不支持function call
        #https://api-docs.deepseek.com/zh-cn/guides/reasoning_model


        #数据库信息
        self.db_host="localhost"
        self.db_port=3306
        self.db_user="root"
        self.db_password="root1234"
        self.db_database="insurance_db"

