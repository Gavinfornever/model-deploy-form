from pymongo import MongoClient

# 连接MongoDB
client = MongoClient('mongodb://root:650803@localhost:27017/')
db = client['model_deploy_db']
model_configs_collection = db['model_configs']

print("开始更新模型配置字段...")

# 更新所有记录，将cluster字段改为cluster_id
result = model_configs_collection.update_many(
    {"cluster": {"$exists": True}},
    [
        {
            "$set": {
                "cluster_id": "$cluster",
            }
        },
        {
            "$unset": "cluster"
        }
    ]
)

print(f"更新了 {result.modified_count} 条记录，将cluster字段改为cluster_id")

# 更新所有记录，将image字段改为image_id
result = model_configs_collection.update_many(
    {"image": {"$exists": True}},
    [
        {
            "$set": {
                "image_id": "$image",
            }
        },
        {
            "$unset": "image"
        }
    ]
)

print(f"更新了 {result.modified_count} 条记录，将image字段改为image_id")

print("模型配置字段更新完成")
