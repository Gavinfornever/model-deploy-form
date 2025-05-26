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
        print(f"- {image['name']} v{image['version']} (creator: {image.get('creator', 'N/A')})")
    
    # 更新所有镜像，将creator字段改名为creator_id
    for image in all_images:
        # 获取当前creator字段的值
        creator_value = image.get('creator')
        
        # 如果存在creator字段，则添加creator_id字段并删除creator字段
        if creator_value:
            # 更新文档，添加creator_id字段
            images_collection.update_one(
                {'_id': image['_id']},
                {'$set': {'creator_id': creator_value}}
            )
            
            # 删除原来的creator字段
            images_collection.update_one(
                {'_id': image['_id']},
                {'$unset': {'creator': ""}}
            )
    
    print("已将所有镜像的creator字段改名为creator_id")
    
    # 查询更新后的镜像
    updated_images = list(images_collection.find({}))
    print("\n更新后的镜像数据:")
    for image in updated_images:
        print(f"- {image['name']} v{image['version']} (creator_id: {image.get('creator_id', 'N/A')})")
    
except Exception as e:
    print(f"MongoDB操作失败: {e}")
