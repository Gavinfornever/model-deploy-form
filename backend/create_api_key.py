from pymongo import MongoClient
import datetime

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    api_keys_collection = db['api_keys']
    print("MongoDB API密钥集合连接成功")
    
    # 创建新的API密钥
    new_api_key = {
        "id": "key2",
        "name": "王高3的API密钥",
        "key": "sk-test-abcdefghijklmnopqrstuvwxyz123456",
        "scope": "只读",
        "user_id": "5da7dce1",
        "created_at": datetime.datetime.now().isoformat(),
        "last_used": None
    }
    
    result = api_keys_collection.insert_one(new_api_key)
    print(f"API密钥创建成功，ID: {result.inserted_id}")
    
    # 查询所有API密钥
    all_keys = list(api_keys_collection.find({}))
    print(f"数据库中共有 {len(all_keys)} 个API密钥:")
    for key in all_keys:
        print(f"- {key['name']} (user_id: {key['user_id']})")
    
except Exception as e:
    print(f"MongoDB操作失败: {e}")
