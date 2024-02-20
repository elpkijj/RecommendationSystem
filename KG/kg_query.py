from py2neo import Graph

# 连接到Neo4j数据库
graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")

# 接收用户输入的期望岗位和学历
desired_job_title = input("请输入期望岗位：")
desired_education = input("请输入期望学历：")

# 执行Cypher查询语句
query = f"""
MATCH (company:Company)-[:RECRUITS]->(job:Job {{title: '{desired_job_title}'}})
MATCH (job)-[:REQUIRES]->(education:EducationRequirement {{name: '{desired_education}'}})
RETURN job.title AS JobTitle, job.responsibilities AS JobDescription
"""

result = graph.run(query)

# 输出匹配到的岗位描述
for record in result:
    print(f"岗位名称: {record['JobTitle']}")
    print(f"岗位描述: {record['JobDescription']}")
