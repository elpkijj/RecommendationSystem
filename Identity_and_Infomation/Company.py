from flask import Flask, request, jsonify, Blueprint
import sqlite3

companies = Blueprint('companies', __name__)
DATABASE = 'Information.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


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
                                
                                FOREIGN KEY(user_id) REFERENCES users(id)
                            )''')

    # 检查是否已有企业信息
    cursor.execute('SELECT * FROM company_info WHERE user_id = ?', (data['userId'],))
    existing_info = cursor.fetchone()

    if existing_info:
        # 更新现有记录
        cursor.execute('''
            UPDATE company_info
            SET name = ?, job = ?, description = ?, education = ?, manager = ?, salary = ?, address = ?, link = ?
            WHERE user_id = ?
        ''', (data['name'], data['job'], data['description'], data['education'], data['manager'], data['salary'],
              data['address'], data['link'], data['userId']))
    else:
        # 插入新数据
        cursor.execute('''
            INSERT INTO company_info (user_id, name, job, description, education, manager, salary, address, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['userId'], data['name'], data['job'], data['description'], data['education'], data['manager'],
              data['salary'], data['address'], data['link']))

    conn.commit()
    return jsonify({'message': '企业信息提交成功'}), 200
