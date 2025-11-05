from exts import db
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ConstellationModel(db.Model):
    __tablename__ = "constellation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    constellation_name = db.Column(db.String(100), nullable=False)
    satellite_count = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship(UserModel, backref="constellations")
    satellites = db.relationship('SatelliteModel', backref='constellation', cascade='all, delete-orphan')


class SatelliteModel(db.Model):
    __tablename__ = "satellite"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    satellite_id = db.Column(db.Integer, nullable=False, index=True)  # 业务ID（同一星座内唯一）
    constellation_id = db.Column(db.Integer, db.ForeignKey("constellation.id"), nullable=False)  # 所属星座
    info_line1 = db.Column(db.Text, nullable=False)
    info_line2 = db.Column(db.Text, nullable=False)

    # 关键：复合唯一约束（确保同一星座内业务ID不重复）
    __table_args__ = (
        db.UniqueConstraint(
            "satellite_id", "constellation_id",
            name="unique_satellite_in_constellation"  # 约束名
        ),
    )



class LinkedSatelliteModel(db.Model):
    __tablename__ = "linked_satellite"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键

    # 关联的两个卫星业务ID（基于同一星座）
    satellite_id1 = db.Column(db.Integer, nullable=False)
    satellite_id2 = db.Column(db.Integer, nullable=False)

    # 关联所属的星座（锁定星座，确保两个卫星属于同一星座）
    constellation_id = db.Column(
        db.Integer,
        db.ForeignKey("constellation.id", ondelete="CASCADE"),  # 星座删除时，关联也删除
        nullable=False
    )

    # 关键：复合外键约束（通过“业务ID+星座ID”关联到卫星表）
    __table_args__ = (
        # 卫星1的复合外键：(satellite_id1, constellation_id) → 卫星表的(satellite_id, constellation_id)
        db.ForeignKeyConstraint(
            ["satellite_id1", "constellation_id"],
            ["satellite.satellite_id", "satellite.constellation_id"],
            name="fk_linked_sat1",  # 外键名
            ondelete="CASCADE"  # 卫星删除时，关联也删除
        ),
        # 卫星2的复合外键：(satellite_id2, constellation_id) → 卫星表的(satellite_id, constellation_id)
        db.ForeignKeyConstraint(
            ["satellite_id2", "constellation_id"],
            ["satellite.satellite_id", "satellite.constellation_id"],
            name="fk_linked_sat2",
            ondelete="CASCADE"
        ),
        # 联合唯一约束：避免同一对卫星在同一星座重复关联（双向）
        db.UniqueConstraint(
            "constellation_id", "satellite_id1", "satellite_id2",
            name="unique_link_forward"
        ),
        db.UniqueConstraint(
            "constellation_id", "satellite_id2", "satellite_id1",
            name="unique_link_backward"
        ),
    )
    # 新增：关联到具体的卫星对象（用于模板中访问卫星信息）
    # 关联卫星1（通过复合外键关联）
    satellite1 = db.relationship(
        "SatelliteModel",
        foreign_keys=[satellite_id1, constellation_id],
        backref="links_from"  # 卫星的“从关联”（作为satellite_id1的关联）
    )
    # 关联卫星2（通过复合外键关联）
    satellite2 = db.relationship(
        "SatelliteModel",
        foreign_keys=[satellite_id2, constellation_id],
        backref="links_to"  # 卫星的“到关联”（作为satellite_id2的关联）
    )

    # 关联到星座（一个星座包含多个卫星关联）
    constellation = db.relationship("ConstellationModel", backref="linked_satellites")


class BaseModel(db.Model):
    __tablename__ = "base"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_name = db.Column(db.String(100), nullable=False)
    info = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship(UserModel, backref="bases")