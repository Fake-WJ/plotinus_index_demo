from flask import Blueprint, request, render_template, redirect, url_for, g
from history.exts import db
from history.model import BaseModel
from history.decorators import login_required

bp = Blueprint("base", __name__, url_prefix="/bases")


@bp.route('/')
@login_required
def list():
    """基座列表：展示当前用户的所有基座"""
    bases = BaseModel.query.filter_by(user_id=g.user.id).all()
    return render_template('base/list.html', bases=bases)


@bp.route('/<int:id>')
@login_required
def detail(id):
    """基座详情"""
    base = BaseModel.query.filter_by(id=id, user_id=g.user.id).first()
    if not base:
        return redirect(url_for('base.list'))
    return render_template('base/detail.html', base=base)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加基座"""
    if request.method == 'POST':
        name = request.form['base_name']
        info = request.form['info']

        if not name or not info:
            return render_template('base/form.html', error="名称和信息不能为空")

        # 检查同名基座
        if BaseModel.query.filter_by(base_name=name, user_id=g.user.id).first():
            return render_template('base/form.html', error="该基座名称已存在")

        # 创建基座
        base = BaseModel(
            base_name=name,
            info=info,
            user_id=g.user.id
        )
        db.session.add(base)
        db.session.commit()
        return redirect(url_for('base.list'))

    return render_template('base/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑基座"""
    base = BaseModel.query.filter_by(id=id, user_id=g.user.id).first()
    if not base:
        return redirect(url_for('base.list'))

    if request.method == 'POST':
        name = request.form['base_name']
        info = request.form['info']

        if not name or not info:
            return render_template('base/form.html', base=base, error="名称和信息不能为空")

        # 检查同名（排除自身）
        if (BaseModel.query.filter_by(base_name=name, user_id=g.user.id).first() and
                name != base.base_name):
            return render_template('base/form.html', base=base, error="该基座名称已存在")

        # 更新基座
        base.base_name = name
        base.info = info
        db.session.commit()
        return redirect(url_for('base.detail', id=id))

    return render_template('base/form.html', base=base)


@bp.route('/<int:id>/delete')
@login_required
def delete(id):
    """删除基座"""
    base = BaseModel.query.filter_by(id=id, user_id=g.user.id).first()
    if base:
        db.session.delete(base)
        db.session.commit()
    return redirect(url_for('base.list'))