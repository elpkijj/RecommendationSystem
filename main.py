from flask import Flask, make_response
from flask_cors import CORS
# 导入蓝图
from Register_and_Login.User import users
from sms import sms

app = Flask(__name__)
CORS(app, resources=r'/*', origins='*', allow_headers='*')

# 注册蓝图
app.register_blueprint(users)
app.register_blueprint(sms)


@app.after_request
def func_res(resp):
    res = make_response(resp)
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Methods'] = '*'
    res.headers['Access-Control-Allow-Headers'] = '*'
    return res


# 注册蓝图
# app.register_blueprint(users_bp)
# app.register_blueprint(resumes_bp)
# app.register_blueprint(auth_bp, url_prefix='/api')  # 注册蓝图并添加前缀

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
