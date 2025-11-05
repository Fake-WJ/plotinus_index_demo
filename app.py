# 修改 plotinus_index/app.py
from flask import Flask, render_template, g
from exts import db
# 新增：导入 Flask-Migrate
from flask_migrate import Migrate
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
from blueprints.auth import bp as auth_bp
from blueprints.constellation import bp as constellation_bp
from blueprints.satellite import bp as satellite_bp
from blueprints.base import bp as base_bp

# 初始化Flask应用
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# 初始化数据库
db.init_app(app)

# 新增：初始化迁移工具（关联app和db）
migrate = Migrate(app, db)

# 注册蓝图（保持不变）
app.register_blueprint(auth_bp)
app.register_blueprint(constellation_bp)
app.register_blueprint(satellite_bp)
app.register_blueprint(base_bp)

# 首页（保持不变）
@app.route('/')
def index():
    return render_template('index.html')

# 注意：移除原有的 db.create_all()，迁移工具会替代此功能
# 旧代码：with app.app_context(): db.create_all()

if __name__ == '__main__':
    app.run(debug=True)