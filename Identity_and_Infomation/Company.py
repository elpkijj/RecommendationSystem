from flask import Flask, request, jsonify, Blueprint
import sqlite3
import threading
from py2neo import Graph, Node, Relationship
import json
from loginRec import recommend_resumes

companies = Blueprint('companies', __name__)
DATABASE = 'Information.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@companies.route('/companies/get-info/<int:user_id>', methods=['GET'])
def get_company_info(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
            SELECT name, job, description, education,
                   manager, salary, address, link
            FROM company_info WHERE user_id = ?
        ''', (user_id,))
    info = cursor.fetchone()

    if not info:
        return jsonify({'message': '用户信息不存在'}), 404

    # 获取列名
    columns = [column[0] for column in cursor.description]
    # 将每个查询结果转换为字典
    info_list = [dict(zip(columns, i)) for i in info]

    conn.close()
    return jsonify(info_list), 200


@companies.route('/companies/create-info', methods=['POST'])
def create_company_info():
    data = request.get_json()
    required_fields = ['userId', 'name', 'job', 'description', 'education', 'manager', 'salary', 'address', 'link']

    # 检查所有必填字段是否已填写
    if not all(field in data for field in required_fields):
        return jsonify({'message': '缺少必填信息'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # ljl:创建数据表
    cursor.execute('''CREATE TABLE IF NOT EXISTS company_info (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                name nchar(5),
                                job nchar(30),
                                description nvarchar(255),
                                education nchar(4),
                                manager nchar(10),
                                salary char(20),
                                address nvarchar(30),
                                link varchar(150)
                                FOREIGN KEY(user_id) REFERENCES users(id)
                            )''')

    # 检查是否已有企业信息
    cursor.execute('SELECT * FROM company_info WHERE user_id = ?', (data['userId'],))
    existing_info = cursor.fetchone()
    #实体抽取
    skills=[]
    city=None

    # 创建关键词节点并建立关系
    for keyword in keywords:
        if keyword in data['description']:
            skills.append(keyword)
    for c in cities:
        if c in data['address']:
            city=c
            break
    # 插入新数据
    skills_json = json.dumps(skills)
    data_to_insert = [data['name'], data['job'], data['description'], data['education'], data['manager'],
            data['salary'], data['address'], data['link'],skills_json,city]
    if existing_info:
        # 更新现有记录
        cursor.execute('''
                        UPDATE company_info
                        SET name = ?, job = ?, description = ?, education = ?, manager = ?, salary = ?, address = ?, link = ?, skills = ?, city = ?
                        WHERE user_id = ?
                        ''', data_to_insert + [user_id])
    else:
        cursor.execute('''
                        INSERT INTO company_info (user_id, name, job, salary, education, description, manager, address, link,skills,city) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
                    ''', data_to_insert)     
    conn.commit()

    def async_process():
        # ljl:将企业信息转换为json文件
        data = request.get_json()
        user_id = data['userId']
        company_info = fetch_company_info(user_id)
        save_company_info_to_json(company_info)
        # ljl:加入为学生匹配职位的知识图谱中(职位id+职位要求)
        graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")
        data = request.get_json()
        identity = data['user_id']
        # 添加关键词列表
        with open('keywords.txt', 'r', encoding='utf-8') as file:
            keywords = file.read().split('、')

        # 创建identity节点
        identity_node = Node("Identity", name=identity, responsibility=data['description'])
        graph.merge(identity_node, "Identity", "name")

        # 为行中的每个关键词创建keyword节点并建立关系
        for keyword in keywords:
            if keyword in data['description']:
                keyword_node = graph.nodes.match("Keyword", name=keyword).first()
                if not keyword_node:
                    keyword_node = Node("Keyword", name=keyword)
                    graph.merge(keyword_node, "Keyword", "name")
                relationship = Relationship(identity_node, "CONTAINS", keyword_node)
                graph.merge(relationship)
        # grj:调用人才推荐函数(ljl:推荐函数中记得增加创建及存储推荐人才（学生）id+契合度的数据库)
        resumes_data_path = 'resumes.json'
        work_id = 63
        # 假设的特定工作ID
        all_info_path = 'all_info.json'
        city_location_path= 'city_coordinates_cache.json'
        all_scores = recommend_resumes(resumes_data_path, work_id, all_info_path,city_location_path)
        #数据库操作
        conn = get_db_connection()
        cursor = conn.cursor()
        # 创建推荐候选人表
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommended_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    candidate_id INTEGER NOT NULL,
                    match REAL NOT NULL,
                    educationMatch REAL NOT NULL,
                    addressMatch REAL NOT NULL,
                    salaryMatch REAL NOT NULL,
                    abilityMatch REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(candidate_id) REFERENCES student_info(id)
                );
                ''')

        # 遍历返回的数据并插入数据库表中
        for score_data in all_scores:
            # 提取各项数据
            resume_id = score_data["resume_id"]
            weighted_score = score_data["weighted_score"]
            skill_score = score_data["skill_score"]
            education_score = score_data["education_score"]
            salary_score = score_data["salary_score"]
            city_score = score_data["city_score"]

            # 执行插入操作
            cursor.execute('''
                        INSERT INTO recommended_candidates (user_id,resume_id, weighted_score, skill_score, education_score, salary_score, city_score)
                        VALUES (?,?, ?, ?, ?, ?, ?)
                    ''', (user_id,resume_id, weighted_score, skill_score, education_score, salary_score, city_score))

        # 执行数据库查询
        cursor.execute('SELECT * FROM recommended_candidates where id=?', (user_id,))

        # 获取查询结果
        rows = cursor.fetchone()

        # 将查询结果转换为字典列表
        results = []
        for row in rows:
            result = {
                'resume_id': row[0],
                'weighted_score': row[1],
                'skill_score': row[2],
                'education_score': row[3],
                'salary_score': row[4],
                'city_score': row[5]
            }
            results.append(result)

        # 将字典列表转换为JSON格式的字符串
        json_data = json.dumps(results)

        # 打印JSON数据（或者根据需要进行其他处理）
        print(json_data)
        conn.commit()
        conn.close()
    # 在另一个线程中运行推荐算法和其他耗时操作
    threading.Thread(target=async_process).start()

    return jsonify({'message': '企业信息提交成功'}), 200


# ljl修改
def fetch_company_info(user_id):
    conn = sqlite3.connect('Information.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM company_info where user_id=?', (user_id,))
    company_info_rows = cursor.fetchone()
    company_info_list = [dict(row) for row in company_info_rows]
    conn.close()
    return company_info_list

# 修改了一下函数
def save_company_info_to_json(company_info, filename='all_info.json'):
    try:
        # 尝试以读模式打开文件并加载现有数据
        with open(filename, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或文件为空，则创建一个新的列表
        existing_data = []

    # 将新的学生信息追加到现有数据中
    existing_data.append(company_info)

    # 以写模式打开文件并更新数据
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)
