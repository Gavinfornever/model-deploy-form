from pymongo import MongoClient
import datetime

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    images_collection = db['images']
    print("MongoDB镜像集合连接成功")
    
    # 查询所有镜像
    all_images = list(images_collection.find({}))
    print(f"数据库中共有 {len(all_images)} 个镜像:")
    for image in all_images:
        print(f"- {image['name']} v{image['version']} (creator: {image['creator']})")
    
    # 更新所有镜像的创建者字段为王高3的ID
    result = images_collection.update_many(
        {},  # 空查询条件表示匹配所有文档
        {"$set": {"creator": "5da7dce1"}}  # 设置creator字段为王高3的ID
    )
    
    print(f"已更新 {result.modified_count} 个镜像的创建者字段为王高3的ID (5da7dce1)")
    
    # 查询更新后的镜像
    updated_images = list(images_collection.find({}))
    print("\n更新后的镜像数据:")
    for image in updated_images:
        print(f"- {image['name']} v{image['version']} (creator: {image['creator']})")
    
except Exception as e:
    print(f"MongoDB操作失败: {e}")
