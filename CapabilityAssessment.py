import json
import os
from py2neo import Graph
from zhipuai import ZhipuAI
client = ZhipuAI(api_key="9a39f8fd6b3776ef950aeb2421a393b8.ed2wnpLn0VGh3YUX") # 填写您自己的APIKey
graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")
def query_skills(id):
    query = f"""
    MATCH (i:Identity {{name: '{id}'}})-[:CONTAINS]->(k:Keyword)
    RETURN k.name AS Keyword
    """
    result = graph.run(query).data()
    # 修改这里，直接返回一个平面列表
    return [item['Keyword'] for item in result]
def calculate_skills_match_percentage(resume_skills, work_keywords):
    # 将简历技能字符串分割为列表，并去除空格
    resume_skills_list = [skill.strip() for skill in resume_skills.split(',')]

    # 计算交集和并集
    skills_intersection = set(resume_skills_list).intersection(set(work_keywords))
    # 计算契合度百分比
    match_percentage = len(skills_intersection) / len(work_keywords) * 100

    return match_percentage
def identify_skill_gaps(resume_skills, work_keywords):
    resume_skills_list = [skill.strip() for skill in resume_skills.split(',')]
    resume_skills_set = set(resume_skills_list)
    work_keywords_set = set(work_keywords)

    # 找出简历中缺失的关键技能
    missing_skills = work_keywords_set - resume_skills_set
    return list(missing_skills)
def get_improvement_suggestions(skill_gaps):
    client = ZhipuAI(api_key="9a39f8fd6b3776ef950aeb2421a393b8.ed2wnpLn0VGh3YUX")
    messages = [
        {"role": "system", "content": "你是一名职业发展顾问,善于给出建设性的职业发展建议。"},
        {"role": "user", "content": f"我是一名求职者,以下是我与目标岗位的技能差距:{', '.join(skill_gaps)}。请给出我一些提升建议。"}
    ]
    response = client.chat.completions.create(
        model="glm-4",
        messages=messages,
        stream=True
    )
    for chunk in response:
        print(chunk.choices[0].delta)
    # suggestions = response.choices[0].message.content
    suggestions=""
    return suggestions

work_id = 4601


with open('resume.json', 'r', encoding='utf-8') as file:
    data = json.load(file)  # 直接从文件中读取并解析JSON数据

resume_skills = data['skills']
work_keywords = query_skills(work_id)
match_percentage = calculate_skills_match_percentage(resume_skills, work_keywords)
missing_skills= identify_skill_gaps(resume_skills, work_keywords)
suggestions = get_improvement_suggestions(missing_skills)
print(f"技能契合度百分比: {match_percentage:.2f}%")
print(f"缺失的技能有: {missing_skills}")
print(suggestions)


