import chardet
from flask import Blueprint, request, render_template, redirect, url_for, g, flash

from blueprints import constellation
from exts import db
from model import SatelliteModel, ConstellationModel, LinkedSatelliteModel
from decorators import login_required

bp = Blueprint("satellite", __name__, url_prefix="/satellites")


@bp.route('/')
@login_required
def list():
    """卫星列表：展示当前用户所有星座下的卫星（带分页）"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20个卫星

    # 分页查询用户所有星座下的卫星
    # 通过关联查询过滤用户权限
    pagination = SatelliteModel.query.join(
        ConstellationModel
    ).filter(
        ConstellationModel.user_id == g.user.id
    ).order_by(
        ConstellationModel.constellation_name.asc(),
        SatelliteModel.satellite_id.asc()
    ).paginate(page=page, per_page=per_page)

    satellites = pagination.items  # 当前页的卫星列表

    return render_template('satellite/list.html',
                           satellites=satellites,
                           pagination=pagination)  # 传递分页对象到模板


@bp.route('/links/import', methods=['GET', 'POST'])
@login_required
def import_links():
    """导入卫星关联：从txt文件批量导入同一星座的卫星关联"""
    # 从URL参数获取星座ID（如果有）
    constellation_id = request.args.get('constellation_id', type=int)
    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()

    if request.method == 'POST':
        constellation_id = request.form.get('constellation_id')
        file = request.files.get('link_file')

        # 验证星座
        constellation = ConstellationModel.query.filter_by(
            id=constellation_id,
            user_id=g.user.id
        ).first()
        if not constellation:
            return render_template('satellite/import_links.html',
                                   constellations=constellations,
                                   error="请选择有效的星座")

        # 验证文件
        if not file or file.filename == "":
            return render_template('satellite/import_links.html',
                                   constellations=constellations,
                                   error="请选择文件")

        if not file.filename.endswith('.txt'):
            return render_template('satellite/import_links.html',
                                   constellations=constellations,
                                   error="请上传txt格式的文件")

        # 检测文件编码
        raw_data = file.stream.read(1024)
        file.stream.seek(0)
        detected_encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        if detected_encoding.lower() in ["gb2312", "gbk"]:
            detected_encoding = "gbk"

        # 获取该星座下所有卫星ID映射（satellite_id -> id）
        satellite_map = {}
        satellites = SatelliteModel.query.filter_by(constellation_id=constellation_id).all()
        for sat in satellites:
            satellite_map[sat.satellite_id] = sat.satellite_id

        # 读取并解析文件
        success_count = 0
        fail_count = 0
        fail_reasons = []
        batch = []
        existing_links = set()

        # 预查询已存在的关联，避免重复导入
        try:
            links = LinkedSatelliteModel.query.filter_by(constellation_id=constellation_id).all()
            for link in links:
                # 存储两种可能的顺序，确保不会重复
                existing_links.add((link.satellite_id1, link.satellite_id2))
                existing_links.add((link.satellite_id2, link.satellite_id1))
        except Exception as e:
            return render_template('satellite/import_links.html',
                                   constellations=constellations,
                                   error=f"查询现有关联失败：{str(e)}")

        # 逐行处理
        for line_num, line in enumerate(file.stream, 1):
            line_str = line.decode(detected_encoding, errors="replace").strip()
            if not line_str:
                continue

            # 解析一行数据
            parts = line_str.split()
            if len(parts) != 2:
                fail_reasons.append(f"行{line_num}：格式错误，需两个卫星ID（空格分隔）")
                fail_count += 1
                continue

            try:
                sat1_num = int(parts[0])
                sat2_num = int(parts[1])
            except ValueError:
                fail_reasons.append(f"行{line_num}：卫星ID必须为数字")
                fail_count += 1
                continue

            # 检查是否为同一卫星
            if sat1_num == sat2_num:
                fail_reasons.append(f"行{line_num}：不能关联同一卫星")
                fail_count += 1
                continue

            # 检查卫星是否存在
            if sat1_num not in satellite_map:
                fail_reasons.append(f"行{line_num}：卫星{sat1_num}不存在")
                fail_count += 1
                continue

            if sat2_num not in satellite_map:
                fail_reasons.append(f"行{line_num}：卫星{sat2_num}不存在")
                fail_count += 1
                continue

            # 转换为数据库ID
            sat1_id = satellite_map[sat1_num]
            sat2_id = satellite_map[sat2_num]

            # 检查关联是否已存在
            if (sat1_id, sat2_id) in existing_links:
                fail_reasons.append(f"行{line_num}：关联已存在")
                fail_count += 1
                continue

            # 创建关联对象
            link = LinkedSatelliteModel(
                satellite_id1=sat1_id,
                satellite_id2=sat2_id,
                constellation_id=constellation_id
            )
            batch.append(link)
            existing_links.add((sat1_id, sat2_id))
            existing_links.add((sat2_id, sat1_id))
            success_count += 1

            # 批量提交
            if len(batch) >= 100:  # 每100条提交一次
                db.session.add_all(batch)
                db.session.commit()
                batch = []
        # 处理最后一批
        if batch:
            try:
                db.session.add_all(batch)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                fail_reasons.append(f"最后批次提交失败：{str(e)}")
                fail_count += len(batch)
                success_count -= len(batch)

        # 显示结果
        flash(f"导入完成：成功{success_count}条，失败{fail_count}条", "success")
        for reason in fail_reasons[:5]:
            flash(reason, "warning")
        if len(fail_reasons) > 5:
            flash(f"...还有{len(fail_reasons) - 5}条失败原因", "warning")

        return redirect(url_for('constellation.detail', id=constellation_id))

    return render_template(
        'satellite/import_links.html',
        constellations=constellations,
        preselected_constellation=constellation_id  # 传递预选中的星座ID
    )


@bp.route('/<int:id>')
@login_required
def detail(id):
    """卫星详情：展示卫星信息及关联关系"""
    satellite = SatelliteModel.query.get(id)
    # 验证权限（卫星所属星座必须属于当前用户）
    if not satellite or satellite.constellation.user_id != g.user.id:
        return redirect(url_for('satellite.list'))

    # 获取该卫星的所有关联
    links_from = LinkedSatelliteModel.query.filter_by(
        satellite_id1=satellite.satellite_id,
        constellation_id=satellite.constellation_id
    ).all()
    links_to = LinkedSatelliteModel.query.filter_by(
        satellite_id2=satellite.satellite_id,
        constellation_id=satellite.constellation_id
    ).all()
    return render_template('satellite/detail.html',
                           satellite=satellite,
                           links_from=links_from,
                           links_to=links_to)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加卫星：成功后更新对应星座的卫星数量"""
    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()
    if not constellations:
        return render_template('satellite/form.html', error="请先创建星座")

    if request.method == 'POST':
        satellite_id = request.form['satellite_id']
        constellation_id = request.form['constellation_id']
        info1 = request.form['info_line1']
        info2 = request.form['info_line2']

        # 验证
        if not all([satellite_id, constellation_id, info1, info2]) or not satellite_id.isdigit():
            return render_template('satellite/form.html',
                                   constellations=constellations,
                                   error="请输入有效的卫星信息")

        # 检查卫星编号是否在同一星座中重复
        if SatelliteModel.query.filter_by(
                satellite_id=satellite_id,
                constellation_id=constellation_id
        ).first():
            return render_template('satellite/form.html',
                                   constellations=constellations,
                                   error="该星座中已存在此卫星编号")

        # 创建卫星
        satellite = SatelliteModel(
            satellite_id=int(satellite_id),
            constellation_id=constellation_id,
            info_line1=info1,
            info_line2=info2
        )
        db.session.add(satellite)

        # 关键：更新星座的卫星数量（+1）
        constellation = ConstellationModel.query.get(constellation_id)
        constellation.satellite_count += 1  # 数量+1

        db.session.commit()
        return redirect(url_for('satellite.list'))

    return render_template('satellite/form.html', constellations=constellations)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑卫星"""
    satellite = SatelliteModel.query.get(id)
    if not satellite or satellite.constellation.user_id != g.user.id:
        return redirect(url_for('satellite.list'))

    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()
    if request.method == 'POST':
        satellite_id = request.form['satellite_id']
        constellation_id = request.form['constellation_id']
        info1 = request.form['info_line1']
        info2 = request.form['info_line2']

        if not all([satellite_id, constellation_id, info1, info2]) or not satellite_id.isdigit():
            return render_template('satellite/form.html',
                                   satellite=satellite,
                                   constellations=constellations,
                                   error="请输入有效的卫星信息")

        # 检查卫星编号是否重复（同星座内）
        if (SatelliteModel.query.filter_by(
                satellite_id=satellite_id,
                constellation_id=constellation_id
        ).first() and
                (satellite_id != str(satellite.satellite_id) or
                 constellation_id != str(satellite.constellation_id))):
            return render_template('satellite/form.html',
                                   satellite=satellite,
                                   constellations=constellations,
                                   error="该星座中已存在此卫星编号")

        # 更新卫星
        satellite.satellite_id = int(satellite_id)
        satellite.constellation_id = constellation_id
        satellite.info_line1 = info1
        satellite.info_line2 = info2
        db.session.commit()
        return redirect(url_for('satellite.detail', id=id))

    return render_template('satellite/form.html',
                           satellite=satellite,
                           constellations=constellations)


@bp.route('/<int:id>/delete')
@login_required
def delete(id):
    """删除卫星：成功后更新对应星座的卫星数量"""
    satellite = SatelliteModel.query.get(id)
    if satellite and satellite.constellation.user_id == g.user.id:
        # 记录所属星座ID（用于后续更新数量）
        constellation_id = satellite.constellation_id

        # 删除关联和卫星
        LinkedSatelliteModel.query.filter(
            (LinkedSatelliteModel.satellite_id1 == id) |
            (LinkedSatelliteModel.satellite_id2 == id)
        ).delete()
        db.session.delete(satellite)

        # 关键：更新星座的卫星数量（-1）
        constellation = ConstellationModel.query.get(constellation_id)
        if constellation.satellite_count > 0:
            constellation.satellite_count -= 1  # 数量-1

        db.session.commit()
    return redirect(url_for('satellite.list'))


# 卫星关联管理（基于星座）
@bp.route('/links/add', methods=['GET', 'POST'])
@login_required
def add_link():
    """添加卫星关联：必须属于同一星座"""
    if request.method == 'POST':
        constellation_id = request.form['constellation_id']
        sat1_id = request.form['satellite_id1']
        sat2_id = request.form['satellite_id2']

        # 验证星座所有权
        constellation = ConstellationModel.query.filter_by(
            id=constellation_id,
            user_id=g.user.id
        ).first()
        if not constellation:
            satellites = SatelliteModel.query.filter_by(constellation_id=constellation_id).all()
            return render_template('satellite/link_form.html',
                                   constellations=ConstellationModel.query.filter_by(user_id=g.user.id).all(),
                                   error="星座不存在")

        # 验证卫星属于该星座
        sat1 = SatelliteModel.query.filter_by(id=sat1_id, constellation_id=constellation_id).first()
        sat2 = SatelliteModel.query.filter_by(id=sat2_id, constellation_id=constellation_id).first()
        if not sat1 or not sat2 or sat1_id == sat2_id:
            satellites = SatelliteModel.query.filter_by(constellation_id=constellation_id).all()
            return render_template('satellite/link_form.html',
                                   constellations=ConstellationModel.query.filter_by(user_id=g.user.id).all(),
                                   selected_constellation=constellation_id,
                                   error="请选择同一星座的不同卫星")

        # 检查关联是否已存在
        if LinkedSatelliteModel.query.filter(
                ((LinkedSatelliteModel.satellite_id1 == sat1_id) &
                 (LinkedSatelliteModel.satellite_id2 == sat2_id) &
                 (LinkedSatelliteModel.constellation_id == constellation_id)) |
                ((LinkedSatelliteModel.satellite_id1 == sat2_id) &
                 (LinkedSatelliteModel.satellite_id2 == sat1_id) &
                 (LinkedSatelliteModel.constellation_id == constellation_id))
        ).first():
            satellites = SatelliteModel.query.filter_by(constellation_id=constellation_id).all()
            return render_template('satellite/link_form.html',
                                   constellations=ConstellationModel.query.filter_by(user_id=g.user.id).all(),
                                   selected_constellation=constellation_id,
                                   error="该关联已存在")

        # 创建关联
        link = LinkedSatelliteModel(
            satellite_id1=sat1_id,
            satellite_id2=sat2_id,
            constellation_id=constellation_id
        )
        db.session.add(link)
        db.session.commit()
        return redirect(url_for('constellation.detail', id=constellation_id))

    # GET请求：展示表单
    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()
    return render_template('satellite/link_form.html', constellations=constellations)


@bp.route('/links/<int:id>/delete')
@login_required
def delete_link(id):
    """删除卫星关联"""
    link = LinkedSatelliteModel.query.get(id)
    # 验证权限（关联所属星座必须属于当前用户）
    if link and link.constellation.user_id == g.user.id:
        constellation_id = link.constellation_id  # 记录所属星座ID用于跳转
        db.session.delete(link)
        db.session.commit()
        return redirect(url_for('constellation.detail', id=constellation_id))
    return redirect(url_for('satellite.list'))


@bp.route('/by-constellation/<int:constellation_id>')
@login_required
def get_by_constellation(constellation_id):
    """根据星座ID获取卫星列表（用于前端异步加载）"""
    # 验证星座所有权
    constellation = ConstellationModel.query.filter_by(
        id=constellation_id,
        user_id=g.user.id
    ).first()
    if not constellation:
        return []

    satellites = SatelliteModel.query.filter_by(constellation_id=constellation_id).all()
    return [{
        'id': s.id,
        'satellite_id': s.satellite_id
    } for s in satellites]