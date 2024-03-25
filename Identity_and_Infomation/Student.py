from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import sqlite3
import pdfplumber
import re
import json

students = Blueprint('students', __name__)

DATABASE = 'Information.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@students.route('/resume/upload', methods=['POST'])
def upload_resume():
    user_id = request.form['userId']
    privacy_setting = request.form['privacySetting']
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 实体提取逻辑
        text = read_pdf_file(file_path)
        resume_info = extract_info_from_pdf_resume(text)

        # 将提取的信息和隐私设置存储到学生信息表中
        conn = get_db_connection()
        cursor = conn.cursor()
        # ljl:创建数据表
        cursor.execute('''CREATE TABLE IF NOT EXISTS student_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            name nchar(5),
                            sex nchar(2),
                            lowestSalary varchar(5),
                            highestSalary varchar(5),
                            phone char(15),
                            education nchar(4),
                            year int,
                            intention nvarchar(20),
                            intentionCity nvarchar(5),
                            email varchar(30),
                            profession nvarchar(20),
                            educationExperience text,
                            internship text,
                            project text,
                            advantage text,
                            privacy-setting int check(privacy-setting in(0,1,2)),
                            skills varchar(255),
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )''')
        # ljl:插入数据
        cursor.execute('
            INSERT INTO student_info (user_id, name,sex,lowestSalary, highestSalary,phone,education,year,intention,intentionCity,email,profession,educationExperience,internship,project,advantage,privacy-setting,skills)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, resume_info.get('姓名'), resume_info.get('性别'),resume_info.get('期望薪资下限'),resume_info.get('期望薪资上限'),resume_info.get('联系电话'),
            resume_info.get('学历'),resume_info.get('年龄'),resume_info.get('求职意向'),resume_info.get('意向城市'),resume_info.get('电子邮箱'),
            resume_info.get('专业'),resume_info.get('教育经历'),resume_info.get('实习经历'),resume_info.get('项目经历'),resume_info.get('个人优势'),privacy_setting,resume_info.get('专业技能')))

        conn.commit()

        return jsonify({'message': '简历上传成功', 'resume_info': resume_info}), 200
    else:
        return jsonify({'message': '文件上传失败'}), 400

@students.route('/students/update-info', methods=['PUT'])
def update_student_info():
    data = request.get_json()
    user_id = data['userId']
    # 提取其他所有字段

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM student_info WHERE user_id = ?
    ''', (user_id,))
    existing_info = cursor.fetchone()

    if existing_info:
        # ljl:如果已存在，更新信息
        cursor.execute('''
                UPDATE student_info SET name = ?, sex = ?, lowest_salary = ?, highest_salary = ?,
                phone = ?, education = ?, year = ?, intention = ?, intention_city = ?, email = ?, 
                profession = ?, education_experience = ?, internship = ?, project = ?, advantage = ? ,privacy-setting = ? ,skills = ?
                WHERE user_id = ?
            ''', (data['name'], data['sex'], data['lowestSalary'], data['highestSalary'],
                  data['phone'], data['education'], data['year'], data['intention'], data['intentionCity'],
                  data['email'], data['profession'], data['educationExperience'], data['internship'],
                  data['project'], data['advantage'], data['privacy-setting'], data['skills'], user_id))
    else:
        # ljl:如果不存在，插入新记录
        cursor.execute('''
                INSERT INTO student_info (user_id, name, sex, lowest_salary, highest_salary,
                phone, education, year, intention, intention_city, email, profession, 
                education_experience, internship, project, advantage, privacy-setting, skills) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
            ''', (user_id, data['name'], data['sex'], data['lowestSalary'], data['highestSalary'],
                  data['phone'], data['education'], data['year'], data['intention'], data['intentionCity'],
                  data['email'], data['profession'], data['educationExperience'], data['internship'],
                  data['project'], data['advantage'],data['privacy-setting'], data['skills']))

    conn.commit()
    return jsonify({'message': '信息更新成功'}), 200

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


# ljl:实体识别功能更新
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
     # 提取性别
    gender_pattern = r'(男|女)'
    gender_match = re.search(gender_pattern, text)
    info['性别'] = gender_match.group(1) if gender_match else None

    # 提取教育经历
    education_pattern = r'教育经历([\s\S]*?)((实习经历)|(项目经历)|(个人优势)|$)'
    education_match = re.search(education_pattern, text)
    info['教育经历'] = education_match.group(1).strip() if education_match else None

    # 提取期望薪资下限和上限
    salary_pattern = r'期望薪资：(\d+)-(\d+)K'
    salary_match = re.search(salary_pattern, text)
    info['期望薪资下限'] = int(salary_match.group(1)) if salary_match else None
    info['期望薪资上限'] = int(salary_match.group(2)) if salary_match else None

    # 提取实习经历
    internship_pattern = r'实习经历([\s\S]*?)((教育经历)|(项目经历)|(个人优势)|$)'
    internship_match = re.search(internship_pattern, text)
    info['工作经历'] = internship_match.group(1).strip() if internship_match else None

    # 提取项目经历
    project_pattern = r'项目经历([\s\S]*?)((个人优势)|(教育经历)|(工作经历)|$)'
    project_match = re.search(project_pattern, text)
    info['项目经历'] = project_match.group(1).strip() if project_match else None

    # 提取个人优势
    strengths_pattern = r'个人优势([\s\S]*)((项目经历)|(教育经历)|(工作经历)|$)'
    strengths_match = re.search(strengths_pattern, text)
    info['个人优势'] = strengths_match.group(1).strip() if strengths_match else None
    
    # 插入数据到数据库
    # cursor.execute(
    #     "INSERT INTO resumes (name, age, phone, email, intention, major, city, education, skills) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    #     (info['姓名'], info['年龄'], info['联系电话'], info['电子邮件'], info['求职意向'],
    #      info['专业'], info['意向城市'], info['学历'],
    #      ', '.join(info['专业技能']) if info['专业技能'] else None))
    # conn.commit()
    # 将信息转换为 JSON 字符串
    # json_data = json.dumps(info, ensure_ascii=False, indent=4)

    # 将 JSON 字符串写入文件
    # with open('resume_info.json', 'w', encoding='utf-8') as file:
    # file.write(json_data)
    return info


# # 示例用法
# resume_text = read_pdf_file('凡广的简历.pdf')
# resume_info = extract_info_from_pdf_resume(resume_text)
# 关闭数据库连接
# cursor.close()
# conn.close()
# print(resume_info)
