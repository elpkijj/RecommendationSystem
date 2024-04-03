import pandas as pd
import numpy as np
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
geolocator = Nominatim(user_agent="city_distance_calculator")
preferred_cities = ["杭州", "厦门", "北京", "上海", "天津", "西安", "长沙",
                    "成都", "广州", "苏州", "郑州", "深圳", "武汉", "重庆"]
# 得到城市的经纬度
def get_coordinates_cached(city,city_coordinates_cache):
    if city not in city_coordinates_cache:
        location = geolocator.geocode(city, language="zh", timeout=7)
        if location:
            city_coordinates_cache[city] = (location.latitude, location.longitude)
        else:
            print(f"找不到城市 '{city}' 的经纬度信息")
            city_coordinates_cache[city] = None
    return city_coordinates_cache[city]
def parse_salary(salary_str):
    """解析薪资字符串，返回薪资范围的最小值和最大值"""
    # 将字符串转换为小写以统一处理大写和小写的'K'
    parts = salary_str.lower().replace('k', '000').split('-')
    if len(parts) == 2:
        min_salary, max_salary = int(parts[0].strip()), int(parts[1].strip())
    else:
        min_salary = max_salary = int(parts[0].strip())
    return min_salary, max_salary
#归一化总得分
def normalize_scores(scores):
    scores_array = np.array(list(scores.values()))
    mean_score = np.mean(scores_array)
    std_score = np.std(scores_array)
    normalized_scores = {work_id: 1 / (1 + np.exp(-(score - mean_score) / std_score)) for work_id, score in scores.items()}
    return normalized_scores
def calculate_skills_match_percentage(resume_skills, work_keywords):
    # 将简历技能字符串分割为列表，并去除空格
    resume_skills_list = [skill.strip() for skill in resume_skills.split(',')]

    # 计算交集和并集
    skills_intersection = set(resume_skills_list).intersection(set(work_keywords))
    skills_union = set(resume_skills_list).union(set(work_keywords))

    # 计算契合度百分比
    match_percentage = len(skills_intersection) / len(skills_union)

    return match_percentage
def calculate_salary_match_percentage(dream_salary_str, work_salary_str):
    if work_salary_str == "Unknown":
        return 0.02  # 将2%表示为0.02，以保持返回值的一致性
    """根据新规则计算薪资匹配度"""
    dream_salary = parse_salary(dream_salary_str)[0]  # 解析期望薪资
    _, max_work_salary = parse_salary(work_salary_str)  # 解析工作薪资范围的最大值
    if dream_salary <= max_work_salary:
        # 期望薪资小于等于工作薪资范围的最大值
        match_percentage = 1
    else:
        # 期望薪资大于工作薪资范围的最大值
        # 引入平滑因子，减少匹配度下降的速度
        smooth_factor = 0.5  # 平滑因子可以根据实际需要调整
        difference_ratio = (dream_salary - max_work_salary) / max_work_salary
        match_percentage = 1 - (difference_ratio * smooth_factor)
        match_percentage = max(0.01, match_percentage)  # 使用0.01作为最低匹配度，避免出现0%

    return match_percentage
def location_match_percentage(resume_city, work_city,city_coordinates_cache):
    if work_city== "Unknown":
        return 2
    """计算地点的偏好匹配度"""
    # 基于城市偏好名单计算匹配度
    if (resume_city in preferred_cities) == (work_city in preferred_cities):
        preference_1 = 1
    else:
        preference_1 = 0
    # 获取工作城市和居住城市的经纬度
    work_coordinates = city_coordinates_cache.get(work_city,city_coordinates_cache)
    resume_coordinates = city_coordinates_cache.get(resume_city,city_coordinates_cache)
    if work_coordinates and resume_coordinates:
        # 计算城市之间的地理距离
        distance_km = geodesic(work_coordinates, resume_coordinates).kilometers

        # 将距离转换为评分（距离越近，评分越高）
        # 这里采用一个简单的线性转换
        max_distance_km = 5000  # 假设最大距离为5000公里
        min_score = 0  # 最低评分
        max_score = 1  # 最高评分

        # 线性转换
        score2 = max_score - (distance_km / max_distance_km) * (max_score - min_score)
        score2 = max(min_score, min(score2, max_score))  # 确保评分在合理范围内
    score=0.5*preference_1+0.5*score2
    return score
def calculate_location_match_percentage(resume_city, work_city):
    if work_city== "Unknown":
        return 2
    """计算地点的偏好匹配度"""
    # 基于城市偏好名单计算匹配度
    if (resume_city in preferred_cities) == (work_city in preferred_cities):
        preference_1 = 1
    else:
        preference_1 = 0
    # 获取工作城市和居住城市的经纬度
    # work_coordinates = get_coordinates(work_city)
    # resume_coordinates = get_coordinates(resume_city)
    # if work_coordinates and resume_coordinates:
    #     # 计算城市之间的地理距离
    #     distance_km = geodesic(work_coordinates, resume_coordinates).kilometers
    #
    #     # 将距离转换为评分（距离越近，评分越高）
    #     # 这里采用一个简单的线性转换
    #     max_distance_km = 5000  # 假设最大距离为5000公里
    #     min_score = 0  # 最低评分
    #     max_score = 1  # 最高评分
    #
    #     # 线性转换
    #     score2 = max_score - (distance_km / max_distance_km) * (max_score - min_score)
    #     score2 = max(min_score, min(score2, max_score))  # 确保评分在合理范围内
    # score=0.5*preference_1+0.5*score2
    return preference_1
def calculate_education_match_percentage(resume_education, work_education):
    # 定义学历与数值权重的映射
    education_levels = {
        "大专": 1,
        "本科": 2,
        "硕士": 3,
        "博士": 4
    }

    # 获取简历和工作学历的数值权重
    resume_level = education_levels.get(resume_education, 0)
    work_level = education_levels.get(work_education, 0)

    # 定义衰减系数 \lambda
    lambda_ = 0.2  # 例如：超过岗位要求的每一级教育水平增加10%的契合度

    # 如果简历学历等于或高于工作学历
    if resume_level >= work_level:
        # 根据超出的教育水平计算契合度
        match_percentage = 1 + lambda_ * (resume_level - work_level)
    else:
        # 如果简历学历低于工作学历，则根据差距进行计算
        # 这里可以设定一个基础的衰减值，例如低于一个级别减少50%的契合度
        # 这个逻辑部分根据您之前的逻辑进行了简化处理，具体的衰减策略可以根据实际需求调整
        decay_factor = 0.5
        gap = work_level - resume_level
        match_percentage = max(0, 1 - gap * decay_factor)

    return match_percentage

def recommend_jobs(resume_data_path, all_info_path, city_location_path,top_n=30):

    # 加载简历数据
    with open(resume_data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    resume_city = data['city']
    resume_skills = data['skills']
    dream_salary = data['salary']
    resume_education = data['education']

    # 加载所有工作信息
    with open(all_info_path, 'r', encoding='utf-8') as f:
        work_data = json.load(f)
    work_info = {work['Identity']: work for work in work_data}

    # 从JSON文件中读取城市与坐标的映射信息
    with open(city_location_path, 'r') as f:
        city_coordinates_cache = json.load(f)

    # 计算简历向量与每个岗位向量之间的内积
    scores = {}
    skill_scores = {}
    edu_scores = {}
    salary_scores = {}
    city_scores={}
    for identity, work in work_info.items():
        work_id=int(work['Identity'])
        work_education = work_info[str(work_id)]['Education_Requirement']
        work_skill = work_info[str(work_id)]['Keywords']
        work_salary = work_info[str(work_id)]['Salary_Range']
        work_address = work_info[str(work_id)]['City']
        if calculate_location_match_percentage(resume_city, work_address) ==0:
            continue
        edu_scores[work_id]=calculate_education_match_percentage(resume_education,work_education)
        skill_scores[work_id] = calculate_skills_match_percentage(resume_skills, work_skill)
        salary_scores[work_id] = calculate_salary_match_percentage(dream_salary, work_salary)
        city_scores [work_id]= location_match_percentage(resume_city, work_address,city_coordinates_cache)
        scores[work_id]=0.4*skill_scores[work_id]+0.2*edu_scores[work_id]+0.2*salary_scores[work_id]+0.2*city_scores[work_id]

    i=0
    # 推荐结果输出
    for work_id, skill_score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]:
        work_info_item = work_info.get(str(work_id), {})
        work_keywords = work_info_item.get('Keywords', [])
        work_salary = work_info_item.get('Salary_Range', "Unknown")
        work_address = work_info_item.get('City', "Unknown")
        work_education = work_info_item.get('Education_Requirement', "Unknown")
        work_details = work_info_item.get('Responsibility')
        if work_address == "Unknown" or work_salary == "Unknown" or work_education == "Unknown":
            continue

        skill_percentage = skill_scores[work_id]
        salary_percentage = salary_scores[work_id]
        city_percentage =city_scores[work_id]
        education_percentage =edu_scores[work_id]
        weighted_score = scores[work_id]
        i+=1
        #ljl
        print(work_id, weighted_score, skill_percentage, salary_percentage, city_percentage, education_percentage,)
    # 五个契合度的存储及输出
    all_scores = []
    for work_id in scores:
        all_scores.append({
            "work_id": work_id,
            "weighted_score": scores.get(work_id, 0),
            "skill_score": skill_scores.get(work_id, 0),
            "education_score": edu_scores.get(work_id, 0),
            "salary_score": salary_scores.get(work_id, 0),
            "city_score": city_scores.get(work_id, 0)
        })
    return all_scores
# 调用推荐函数
resume_data_path = 'resume.json'
all_info_path = 'all_info.json'
city_location_path='city_coordinates_cache.json'
recommend_jobs(resume_data_path, all_info_path,city_location_path,30)