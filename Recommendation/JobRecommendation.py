from flask import Flask, request, jsonify, Blueprint
import sqlite3

app = Flask(__name__)
jobs = Blueprint('jobs', __name__)

DATABASE = 'Information.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 方便后面将行数据转化为字典
    return conn


@jobs.route('/jobs/recommended/<int:user_id>', methods=['GET'])
def get_recommended_jobs(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查询推荐职位ID和匹配度
    cursor.execute('''
           SELECT ci.name, ci.job, ci.description, ci.education, ci.manager, ci.salary, ci.address, ci.link,
                  rj.match, rj.educationMatch, rj.addressMatch, rj.salaryMatch, rj.abilityMatch
           FROM recommended_jobs rj
           JOIN company_info ci ON rj.job_id = ci.id
           WHERE rj.user_id = ?
           ORDER BY rj.match DESC
           LIMIT 20
       ''', (user_id,))
    jobs = cursor.fetchall()
    if not jobs:
        return jsonify({'message': '未找到推荐职位'}), 404

    # 获取列名
    columns = [column[0] for column in cursor.description]
    # 将每个查询结果转换为字典
    jobs_list = [dict(zip(columns, job)) for job in jobs]

    conn.close()
    return jsonify(jobs_list), 200


@jobs.route('/jobs/sort/<int:user_id>/<criteria>', methods=['GET'])
def sort_jobs(user_id, criteria):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 定义排序字段映射
    sort_fields = {
        'education': 'educationMatch',
        'location': 'addressMatch',
        'salary': 'salaryMatch',
        'skills': 'skillsMatch'
    }

    # 检查是否为有效的筛选条件
    if criteria not in sort_fields:
        return jsonify({'message': '无效的筛选条件'}), 400

    # 获取排序字段
    sort_field = sort_fields[criteria]

    # 筛选并查询推荐职位ID和匹配度
    sql_query = '''
               SELECT ci.name, ci.job, ci.description, ci.education, ci.manager, ci.salary, ci.address, ci.link,
                      rj.match, rj.educationMatch, rj.addressMatch, rj.salaryMatch, rj.abilityMatch
               FROM recommended_jobs rj
               JOIN company_info ci ON rj.job_id = ci.id
               WHERE rj.user_id = ?
               ORDER BY {} DESC
               LIMIT 20
           '''.format(sort_field)

    cursor.execute(sql_query, (user_id,))
    jobs = cursor.fetchall()

    if not jobs:
        return jsonify({'message': '未找到推荐职位'}), 404

    # 获取列名
    columns = [column[0] for column in cursor.description]
    # 将每个查询结果转换为字典
    jobs_list = [dict(zip(columns, job)) for job in jobs]

    conn.close()
    return jsonify(jobs_list), 200
