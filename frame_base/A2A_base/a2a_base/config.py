
#定义配置文件
class Config(object):
    def __init__(self):
        #大模型信息
        self.api_key="sk-52e226ac3cac46838cb282b45b1a648e"
        self.api_url="https://gateway.ai.cloudflare.com/v1/d2cbfe461e343906da9615cbceab35c6/itcast_bilibili-share/deepseek"
        self.model_name="deepseek-chat" #支持function call
        # self.model_name="deepseek-reasoner"  # 不支持function call
        #https://api-docs.deepseek.com/zh-cn/guides/reasoning_model

        #数据库信息
        self.db_host="localhost"
        self.db_port=3306
        self.db_user="root"
        self.db_password="root1234"
        self.db_database="insurance_db"

