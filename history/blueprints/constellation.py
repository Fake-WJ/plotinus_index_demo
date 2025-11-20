from flask import Blueprint, request, render_template, redirect, url_for, g, flash
from history.exts import db
from history.model import ConstellationModel, SatelliteModel, LinkedSatelliteModel
from history.decorators import login_required
import re
from sqlalchemy import select
import chardet
import io
from flask import make_response
from zipfile import ZipFile, ZIP_DEFLATED

bp = Blueprint("constellation", __name__, url_prefix="/constellations")

# 配置：每批提交的卫星数量（根据服务器性能调整，建议50-200）
BATCH_SIZE = 100


@bp.route("/import/<int:constellation_id>", methods=["GET", "POST"])
@login_required
def import_satellites(constellation_id):
    constellation = ConstellationModel.query.get_or_404(constellation_id)

    # 开启权限校验（仅所有者可导入）
    if constellation.user_id != g.user.id:
        flash("无权限操作该星座", "danger")
        return redirect(url_for("constellation.list"))

    if request.method == "POST":
        file = request.files.get("satellite_file")
        if not file or file.filename == "":
            flash("请选择文件", "danger")
            return redirect(request.url)

        # 自动检测文件编码
        raw_data = file.stream.read(1024)
        file.stream.seek(0)
        detected_encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        if detected_encoding.lower() in ["gb2312", "gbk"]:
            detected_encoding = "gbk"

        # 预查询已有卫星ID（避免重复）
        existing_satellite_ids = set()
        try:
            query = select(SatelliteModel.satellite_id).where(
                SatelliteModel.constellation_id == constellation_id
            )
            result = db.session.execute(query)
            existing_satellite_ids = set(result.scalars().all())
        except Exception as e:
            flash(f"数据库查询失败：{str(e)}", "danger")
            return redirect(request.url)

        success_count = 0
        fail_count = 0
        fail_reasons = []
        batch = []
        lines = []

        # 逐行读取并处理
        for line_num, line in enumerate(file.stream, 1):
            line_str = line.decode(detected_encoding, errors="replace").strip()
            if not line_str:
                continue
            lines.append((line_num, line_str))

            # 每3行解析一个卫星
            if len(lines) == 3:
                (num1, line1), (num2, line2), (num3, line3) = lines
                try:
                    match = re.search(r"\s+(\d+)$", line1)
                    if not match:
                        raise ValueError("未找到卫星ID（格式应为：星座名称 数字ID）")
                    satellite_id = int(match.group(1))  # 转换为整数

                    # 校验唯一性
                    if satellite_id in existing_satellite_ids:
                        raise ValueError(f"卫星ID {satellite_id} 已存在")

                    # 创建卫星对象（移除不存在的user_id字段）
                    new_satellite = SatelliteModel(
                        satellite_id=satellite_id,
                        constellation_id=constellation_id,
                        info_line1=line2,
                        info_line2=line3
                    )
                    batch.append(new_satellite)
                    existing_satellite_ids.add(satellite_id)
                    success_count += 1

                    # 批次提交
                    if len(batch) >= BATCH_SIZE:
                        db.session.add_all(batch)
                        db.session.commit()
                        batch = []
                        db.session.expire_all()

                except Exception as e:
                    fail_reasons.append(f"行{num1}-{num3}：{str(e)}")
                    fail_count += 1
                finally:
                    lines = []

        # 处理最后一批
        if batch:
            try:
                db.session.add_all(batch)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                fail_reasons.append(f"最后批次提交失败：{str(e)}")
                success_count -= len(batch)
                fail_count += len(batch)

        # 更新星座的卫星数量（直接计算当前实际数量）
        actual_count = SatelliteModel.query.filter_by(constellation_id=constellation_id).count()
        constellation.satellite_count = actual_count
        db.session.commit()

        # 显示结果
        flash(f"导入完成：成功{success_count}个，失败{fail_count}个", "success")
        for reason in fail_reasons[:5]:
            flash(reason, "warning")
        if len(fail_reasons) > 5:
            flash(f"...还有{len(fail_reasons) - 5}条失败原因", "warning")

        return redirect(url_for("constellation.detail", id=constellation_id))

    return render_template("constellation/import.html", constellation=constellation)




@bp.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    """导出选中星座的卫星数据和关联信息"""
    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()

    if request.method == 'POST':
        selected_ids = request.form.getlist('constellation_ids')
        if not selected_ids:
            flash("请至少选择一个星座", "warning")
            return render_template('constellation/export.html', constellations=constellations)

        selected_constellations = ConstellationModel.query.filter(
            ConstellationModel.id.in_(selected_ids),
            ConstellationModel.user_id == g.user.id
        ).all()

        # 生成TLE和ISL数据
        tles_content, isls_content, satellites_count = generate_export_data(selected_constellations)

        # 创建ZIP文件
        memory_file = io.BytesIO()
        with ZipFile(memory_file, 'w', ZIP_DEFLATED) as zipf:
            zipf.writestr('tles.txt', tles_content)
            zipf.writestr('isls.txt', isls_content)

        # 准备响应
        memory_file.seek(0)
        response = make_response(memory_file.read())
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = 'attachment; filename="constellation_data.zip"'

        return response

    return render_template('constellation/export.html', constellations=constellations)


def generate_export_data(constellations):
    """生成导出文件内容"""
    tles_lines = []
    isls_lines = []
    total_offset = 0  # 用于计算卫星ID偏移量
    constellation_sat_count = []  # 记录每个星座的卫星数量

    # 首先收集所有星座的卫星数量
    for constellation in constellations:
        count = SatelliteModel.query.filter_by(constellation_id=constellation.id).count()
        constellation_sat_count.append(count)

    # 生成TLE数据
    for idx, constellation in enumerate(constellations):
        satellites = SatelliteModel.query.filter_by(constellation_id=constellation.id).all()
        for sat in satellites:
            tles_lines.append(f"{constellation.constellation_name} {sat.satellite_id}")
            tles_lines.append(sat.info_line1)
            tles_lines.append(sat.info_line2)

    # 生成ISL数据
    for idx, constellation in enumerate(constellations):
        # 对于第二个及以后的星座，计算偏移量
        current_offset = sum(constellation_sat_count[:idx]) if idx > 0 else 0

        # 获取该星座的所有卫星关联
        links = LinkedSatelliteModel.query.filter_by(constellation_id=constellation.id).all()
        for link in links:
            # 应用偏移量
            sat1_id = link.satellite_id1 + current_offset
            sat2_id = link.satellite_id2 + current_offset
            isls_lines.append(f"{sat1_id} {sat2_id}")

    return '\n'.join(tles_lines), '\n'.join(isls_lines), constellation_sat_count


@bp.route('/')
@login_required
def list():
    """星座列表：展示当前用户的所有星座"""
    constellations = ConstellationModel.query.filter_by(user_id=g.user.id).all()
    return render_template('constellation/list.html', constellations=constellations)


@bp.route('/<int:id>')
@login_required
def detail(id):
    # 获取星座信息
    constellation = ConstellationModel.query.get_or_404(id)

    # 获取当前页码（默认第1页，确保为整数）
    page = request.args.get("page", 1, type=int)

    pagination = SatelliteModel.query.filter_by(
        constellation_id=id
    ).order_by(
        SatelliteModel.satellite_id  # 按卫星ID排序，确保分页顺序一致
    ).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    satellites = pagination.items

    return render_template(
        "constellation/detail.html",
        constellation=constellation,
        satellites=satellites,
        pagination=pagination
    )


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加星座：初始化卫星数量为0"""
    if request.method == 'POST':
        name = request.form['name']

        # 验证
        if not name:
            return render_template('constellation/form.html', error="请输入有效的星座名称")

        # 检查同名星座
        if ConstellationModel.query.filter_by(
                constellation_name=name,
                user_id=g.user.id
        ).first():
            return render_template('constellation/form.html', error="该星座名称已存在")

        # 创建星座：初始化 satellite_count 为 0（当前无卫星）
        constellation = ConstellationModel(
            constellation_name=name,
            satellite_count=0,  # 初始化为0
            user_id=g.user.id
        )
        db.session.add(constellation)
        db.session.commit()
        return redirect(url_for('constellation.list'))

    return render_template('constellation/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑星座：仅允许修改名称，卫星数量自动计算"""
    constellation = ConstellationModel.query.filter_by(id=id, user_id=g.user.id).first()
    if not constellation:
        return redirect(url_for('constellation.list'))

    if request.method == 'POST':
        name = request.form['name']

        if not name:
            return render_template('constellation/form.html',
                                   constellation=constellation,
                                   error="请输入有效的星座名称")

        # 检查同名（排除自身）
        if (ConstellationModel.query.filter_by(
                constellation_name=name,
                user_id=g.user.id
        ).first() and name != constellation.constellation_name):
            return render_template('constellation/form.html',
                                   constellation=constellation,
                                   error="该星座名称已存在")

        # 仅更新名称（卫星数量由系统自动维护）
        constellation.constellation_name = name
        db.session.commit()
        return redirect(url_for('constellation.detail', id=id))

    return render_template('constellation/form.html', constellation=constellation)

@bp.route('/<int:id>/delete')
@login_required
def delete(id):
    """删除星座（级联删除下属卫星）"""
    constellation = ConstellationModel.query.filter_by(id=id, user_id=g.user.id).first()
    if constellation:
        db.session.delete(constellation)
        db.session.commit()
    return redirect(url_for('constellation.list'))
