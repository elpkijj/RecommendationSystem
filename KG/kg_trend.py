# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 08:20:30 2024

@author: Z sane
"""

import matplotlib.pyplot as plt
from py2neo import Graph
import heapq
from PIL import Image
from wordcloud import WordCloud
import numpy as np
import pandas as pd
import spacy



 


# 连接到Neo4j数据库
graph = Graph("http://localhost:7474", auth=("neo4j", "Zsane0724"), name="neo4j")



# 执行Cypher查询语句
query3 = f"""
MATCH (c:Keyword)
OPTIONAL MATCH ()-[r_in]->(c)
WITH c,  count(r_in) AS inDegree
RETURN c AS nodeName, inDegree
"""

query1 = f"""
MATCH (c:Job)
OPTIONAL MATCH ()-[r_in]->(c)
WITH c,  count(r_in) AS inDegree
RETURN c, inDegree
"""

query2 = f"""
MATCH (c:Company)
RETURN count(c) AS numberOfCompanies

"""
result1 = graph.run(query1)

result2 = graph.run(query2).data()
result3=graph.run(query3)
#%%
# 输出匹配到的岗位描述

numberOfCompanies=result2[0]["numberOfCompanies"]
indegree=[];
jobname=[];
indegree_skill=[]
skillname=[]
for [k,i] in result1:
    indegree.append(i/(numberOfCompanies-1))
    jobname.append(k["title"])
    #print(indegree,jobname)
for [k,i] in result3:  
    skillname.append(k["name"])
    indegree_skill.append(i/(numberOfCompanies-1))  


#%%


# 加载中文语言模型
nlp = spacy.load("zh_core_web_sm")

# 示例职位名称列表
positions = jobname

# 设置相似度阈值
similarity_threshold = 0.7

# 创建一个空字典来存储合并后的职位名称
merged_positions = {}
merged_index={}

for i in range(len(positions)):
    position=positions[i]
    # 检查当前职位是否已经在合并字典中
    found = False
    position_doc = nlp(position)
    for key in merged_positions.keys():
        key_doc = nlp(key)
        # 计算语义相似度
        similarity = position_doc.similarity(key_doc)
        if similarity > similarity_threshold:
            # 如果找到相似的职位名称，则合并
            merged_positions[key].append(position)
            merged_index[key].append(i)
            found = True
            break
    if not found:
        # 如果没有找到相似的职位，则添加新的职位
        merged_positions[position] = [position]
        merged_index[position] = [i]
#%%
# 打印合并后的职位名称
sumindegree={}
for key, value in merged_index.items():
    #print(f"主职位: {key}, 包含职位编号: {value}")    
    tot=0
    for dex in value:
        tot=tot+indegree[dex]
        sumindegree[key]=tot
#%%    
mask = np.array(Image.open("hat.png"))

wordcloud = WordCloud(scale=32,
                      width=800, 
                      height=400,
                      mask=mask,
                      background_color='white',
                      min_font_size=2
                      ).generate_from_frequencies(sumindegree)

plt.figure(figsize=(10, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()
#%%
#画热门技能 
        
sumindegree_skill={}        
for i in range(len(skillname)):
    sumindegree_skill[skillname[i]]=indegree_skill[i]
mask = np.array(Image.open("hat.png"))

wordcloud = WordCloud(scale=32,
                      width=800, 
                      height=400,
                      mask=mask,
                      background_color='white',
                      min_font_size=2
                      ).generate_from_frequencies(sumindegree_skill)

plt.figure(figsize=(10, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()
#%%
x = list(sumindegree.keys())  
y = list(sumindegree.values())

re1 = map(y.index, heapq.nlargest(10, y)) #求最大的n个索引   
re2 = heapq.nlargest(10, y) #求最大的n个元素
re1=list(re1)

# 假设你有以下x轴和y轴的数据  
  
# 使用bar函数来绘制直方图
plt.rcParams['font.sans-serif'] = ['SimHei']

xx=[x[i] for i in re1]  
plt.barh(xx, re2)  
  
# 设置x轴和y轴的标签  
plt.ylabel('岗位名称')  
plt.xlabel('中心度')  
  
# 设置图表的标题  
plt.title('直方图')  
  
# 显示图表  
plt.show()
#%%
dict_data=sumindegree
# 将字典转换为DataFrame，其中字典的键成为行索引，值成为列'value'下的内容  
df = pd.DataFrame.from_dict(dict_data, orient='index', columns=['value'])  
  
# 重置索引，使得原来的键成为普通的列  
df = df.reset_index()  
df.columns = ['岗位名称', '中心度']  # 重命名列名  
  
# 将DataFrame写入Excel文件  
df.to_excel('output.xlsx', index=False, engine='openpyxl')
#%%
dict_data=sumindegree_skill
# 将字典转换为DataFrame，其中字典的键成为行索引，值成为列'value'下的内容  
df = pd.DataFrame.from_dict(dict_data, orient='index', columns=['value'])  
  
# 重置索引，使得原来的键成为普通的列  
df = df.reset_index()  
df.columns = ['技能名称', '中心度']  # 重命名列名  
  
# 将DataFrame写入Excel文件  
df.to_excel('output_skill.xlsx', index=False, engine='openpyxl')














