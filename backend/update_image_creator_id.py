from pymongo import MongoClient
import datetime

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    images_collection = db['images']
    users_collection = db['users']
    print("MongoDB连接成功")
    
    # 查询王高3的用户ID
    user = users_collection.find_one({"username": "王高3"})
    if user:
        wang_gao_id = str(user["_id"])
        print(f"找到王高3的用户ID: {wang_gao_id}")
        
        # 更新所有镜像的创建者ID为王高3的ID
        result = images_collection.update_many(
            {"creator_id": "5da7dce1"},
            {"$set": {"creator_id": wang_gao_id}}
        )
        
        print(f"已更新 {result.modified_count} 个镜像的创建者ID")
        
        # 查询更新后的镜像
        images = list(images_collection.find({}))
        print("\n更新后的镜像数据:")
        for image in images:
            print(f"- {image['name']} v{image['version']} (creator_id: {image.get('creator_id', 'N/A')})")
    else:
        print("未找到用户'王高3'")
    
except Exception as e:
    print(f"MongoDB操作失败: {e}")
