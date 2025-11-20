# 修改 plotinus_index/app.py
from flask import Flask, render_template
from exts import db
# 新增：导入 Flask-Migrate
from flask_migrate import Migrate
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
from history.blueprints.auth import bp as auth_bp
from history.blueprints import bp as constellation_bp
from history.blueprints.satellite import bp as satellite_bp
from history.blueprints.base import bp as base_bp


app = Flask(__name__)


app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# 初始化数据库
db.init_app(app)


migrate = Migrate(app, db)


app.register_blueprint(auth_bp)
app.register_blueprint(constellation_bp)
app.register_blueprint(satellite_bp)
app.register_blueprint(base_bp)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)