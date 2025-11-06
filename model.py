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

    # 确保同一星座内业务ID不重复
    __table_args__ = (
        db.UniqueConstraint(
            "satellite_id", "constellation_id",
            name="unique_satellite_in_constellation"  # 约束名
        ),
    )



class LinkedSatelliteModel(db.Model):
    __tablename__ = "linked_satellite"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    satellite_id1 = db.Column(db.Integer, nullable=False)
    satellite_id2 = db.Column(db.Integer, nullable=False)

    # 关联所属的星座（锁定星座，确保两个卫星属于同一星座）
    constellation_id = db.Column(
        db.Integer,
        db.ForeignKey("constellation.id", ondelete="CASCADE"),  # 星座删除时，关联也删除
        nullable=False
    )

    # 复合外键约束（业务ID+星座ID关联到卫星表）
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["satellite_id1", "constellation_id"],
            ["satellite.satellite_id", "satellite.constellation_id"],
            name="fk_linked_sat1",
            ondelete="CASCADE"
        ),
        db.ForeignKeyConstraint(
            ["satellite_id2", "constellation_id"],
            ["satellite.satellite_id", "satellite.constellation_id"],
            name="fk_linked_sat2",
            ondelete="CASCADE"
        ),
        # 避免同一对卫星在同一星座重复关联（双向）
        db.UniqueConstraint(
            "constellation_id", "satellite_id1", "satellite_id2",
            name="unique_link_forward"
        ),
        db.UniqueConstraint(
            "constellation_id", "satellite_id2", "satellite_id1",
            name="unique_link_backward"
        ),
    )

    satellite1 = db.relationship(
        "SatelliteModel",
        foreign_keys=[satellite_id1, constellation_id],
        backref="links_from"
    )

    satellite2 = db.relationship(
        "SatelliteModel",
        foreign_keys=[satellite_id2, constellation_id],
        backref="links_to"
    )

    constellation = db.relationship("ConstellationModel", backref="linked_satellites")


class BaseModel(db.Model):
    __tablename__ = "base"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_name = db.Column(db.String(100), nullable=False)
    info = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship(UserModel, backref="bases")