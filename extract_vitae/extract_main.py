import sqlite3
import pdfplumber
import re
import json

# 连接到 SQLite 数据库
conn = sqlite3.connect('resumes.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    age INTEGER,
                    phone TEXT,
                    email TEXT,
                    intention TEXT,
                    skills TEXT,
                    major TEXT,
                    city TEXT,
                    education TEXT
                )''')


def read_pdf_file(filename):
    with pdfplumber.open(filename) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
    return text


# 其他函数保持不变
# 提取专业、城市、学历
def load_keywords_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        keywords = file.read().splitlines()
    return keywords


# 加载专业、城市、学历关键词
major_keywords = load_keywords_from_file('major.txt')
city_keywords = load_keywords_from_file('city.txt')
education_keywords = load_keywords_from_file('education.txt')


def match_keywords(text, keyword_file):
    with open(keyword_file, 'r', encoding='utf-8') as file:
        keywords = file.read().splitlines()
    matched_keywords = [keyword for keyword in keywords if keyword in text]
    return matched_keywords


def load_titles_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        titles = file.read().splitlines()
    return titles


def match_exact_keywords(text, keywords):
    matched_keywords = [keyword for keyword in keywords if keyword == text]
    return matched_keywords


def extract_info_from_pdf_resume(text):
    info = {}

    # 提取姓名
    name_pattern = r'([\u4e00-\u9fa5]{2,3})'  # 匹配2-3个汉字作为姓名
    name_match = re.search(name_pattern, text)
    info['姓名'] = name_match.group(1) if name_match else None

    # 提取年龄
    age_pattern = r'(\d{2})岁'  # 匹配两位数字加上"岁"字符
    age_match = re.search(age_pattern, text)
    info['年龄'] = int(age_match.group(1)) if age_match else None

    # 提取联系电话
    phone_pattern = r'(\d{11})'  # 匹配11位数字作为联系电话
    phone_match = re.search(phone_pattern, text)
    info['联系电话'] = phone_match.group(1) if phone_match else None

    # 提取电子邮件
    email_pattern = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'  # 匹配常见的电子邮件格式
    email_match = re.search(email_pattern, text)
    info['电子邮件'] = email_match.group(1) if email_match else None

    # 提取求职意向
    intention_keywords = ['求职意向', '期望岗位']
    intention = None
    for keyword in intention_keywords:
        if keyword in text:
            start_index = text.index(keyword) + len(keyword)
            end_index = text.find('\n\n', start_index)
            intention = text[start_index:end_index].strip()
            break
    if intention:
        titles = load_titles_from_file('title.txt')
        for title in titles:
            if title in intention:
                intention = title
                break
    info['求职意向'] = intention

    # 提取专业技能
    skills_keywords = ['技能', '熟悉', '了解']
    skills = None
    for keyword in skills_keywords:
        if keyword in text:
            start_index = text.index(keyword) + len(keyword)
            end_index = text.find('\n\n', start_index)  # 假设信息之间以双换行符分隔
            skills = text[start_index:end_index].strip()
            break
    if skills:
        matched_skills = match_keywords(skills, 'description.txt')
        skills = matched_skills
    info['专业技能'] = skills

    # 提取专业
    major = None
    for keyword in major_keywords:
        if keyword in text:
            major = keyword
            break
    info['专业'] = major

    # 提取城市
    city = None
    for keyword in city_keywords:
        if keyword in text:
            city = keyword
            break
    info['意向城市'] = city
    # 提取学历
    education = None
    for keyword in education_keywords:
        if keyword in text:
            education = keyword
            break
    info['学历'] = education
    # 插入数据到数据库
    cursor.execute(
        "INSERT INTO resumes (name, age, phone, email, intention, major, city, education, skills) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (info['姓名'], info['年龄'], info['联系电话'], info['电子邮件'], info['求职意向'],
         info['专业'], info['意向城市'], info['学历'],
         ', '.join(info['专业技能']) if info['专业技能'] else None))
    conn.commit()
    # 将信息转换为 JSON 字符串
    #json_data = json.dumps(info, ensure_ascii=False, indent=4)

    # 将 JSON 字符串写入文件
    #with open('resume_info.json', 'w', encoding='utf-8') as file:
        #file.write(json_data)
    return info


# 示例用法
resume_text = read_pdf_file('凡广的简历.pdf')
resume_info = extract_info_from_pdf_resume(resume_text)
# 关闭数据库连接
cursor.close()
conn.close()
print(resume_info)

