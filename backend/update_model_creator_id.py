from pymongo import MongoClient
import datetime

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    model_configs_collection = db['model_configs']
    users_collection = db['users']
    print("MongoDB连接成功")
    
    # 查询王高3的用户ID
    user = users_collection.find_one({"username": "王高3"})
    if user:
        wang_gao_id = str(user["_id"])
        print(f"找到王高3的用户ID: {wang_gao_id}")
        
        # 更新所有模型配置的创建者ID为王高3的ID
        result = model_configs_collection.update_many(
            {},  # 空查询条件表示匹配所有文档
            {"$set": {"creator_id": wang_gao_id}}
        )
        
        print(f"已更新 {result.modified_count} 个模型配置的创建者ID")
        
        # 查询更新后的模型配置
        models = list(model_configs_collection.find({}))
        print("\n更新后的模型配置数据:")
        for model in models:
            print(f"- {model.get('modelName', 'N/A')} (creator_id: {model.get('creator_id', 'N/A')})")
    else:
        print("未找到用户'王高3'")
    
except Exception as e:
    print(f"MongoDB操作失败: {e}")
