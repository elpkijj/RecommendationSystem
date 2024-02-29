from fuzzywuzzy import process
import pandas as pd

# 示例职位名称列表
positions = ["软件工程师", "软件开发工程师", "系统工程师", "数据分析师", "数据科学家", "大数据分析师"]

# 设置相似度阈值
similarity_threshold = 80

# 创建一个空字典来存储合并后的职位名称
merged_positions = {}

for position in positions:
    # 检查当前职位是否已经在合并字典中
    found = False
    for key in merged_positions.keys():
        # 计算相似度
        similarity = process.extractOne(position, [key])[1]
        if similarity > similarity_threshold:
            # 如果找到相似的职位名称，则合并
            merged_positions[key].append(position)
            found = True
            break
    if not found:
        # 如果没有找到相似的职位，则添加新的职位
        merged_positions[position] = [position]

# 打印合并后的职位名称
for key, value in merged_positions.items():
    print(f"主职位: {key}, 包含职位: {value}")
