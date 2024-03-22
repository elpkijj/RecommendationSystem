from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 导入蓝图
from Register_and_Login.User import users
from sms import sms

# 注册蓝图
app.register_blueprint(users)
app.register_blueprint(sms)
# 注册蓝图
# app.register_blueprint(users_bp)
# app.register_blueprint(resumes_bp)
# app.register_blueprint(auth_bp, url_prefix='/api')  # 注册蓝图并添加前缀

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
