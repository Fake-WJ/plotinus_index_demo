from flask import Blueprint, request, render_template, redirect, url_for, session, g
from exts import db
from model import UserModel

bp = Blueprint("auth", __name__, url_prefix="/auth")


# 全局变量：当前登录用户
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = UserModel.query.get(user_id)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 验证
        if not username or not password:
            return render_template('auth/register.html', error="用户名和密码不能为空")
        if UserModel.query.filter_by(username=username).first():
            return render_template('auth/register.html', error="用户名已存在")

        # 创建用户
        user = UserModel(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = UserModel.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return render_template('auth/login.html', error="用户名或密码错误")

        # 记录登录状态
        session['user_id'] = user.id
        return redirect(url_for('index'))

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    return redirect(url_for('index'))