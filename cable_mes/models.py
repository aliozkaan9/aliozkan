from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from cable_mes.database import Base
from datetime import datetime
from flask_login import UserMixin
import enum

class UserRole(enum.Enum):
    ADMIN = 'admin'
    OPERATOR = 'operator'

class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    full_name = Column(String(100))

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    type = Column(String(50))
    status = Column(String(20), default='IDLE')

    # PLC Configuration
    plc_ip = Column(String(15))
    plc_port = Column(Integer, default=502)
    plc_slave_id = Column(Integer, default=1)

    # Register Addresses (Mapping)
    reg_speed = Column(Integer, default=0)
    reg_temp = Column(Integer, default=1)
    reg_diameter = Column(Integer, default=2)

    def __repr__(self):
        return f'<Machine {self.name}>'

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    target_diameter_mm = Column(Float, nullable=False)
    tolerance_mm = Column(Float, nullable=False)
    target_speed_m_min = Column(Float, default=100.0)

class WorkOrder(Base):
    __tablename__ = 'work_orders'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=False)
    target_length_m = Column(Float, nullable=False)
    produced_length_m = Column(Float, default=0.0)
    status = Column(String(20), default='PLANNED')
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    product = relationship('Product')
    machine = relationship('Machine')

class Telemetry(Base):
    __tablename__ = 'telemetry'
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey('work_orders.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    line_speed_m_min = Column(Float)
    temperature_c = Column(Float)
    diameter_mm = Column(Float)

    work_order = relationship('WorkOrder')

class QualityAlert(Base):
    __tablename__ = 'quality_alerts'
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey('work_orders.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50))
    measured_value = Column(Float)
    description = Column(String(200))

    work_order = relationship('WorkOrder')

class DowntimeLog(Base):
    __tablename__ = 'downtime_logs'
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    reason_code = Column(String(50)) # e.g., 'BREAKDOWN', 'NO_MATERIAL'
    description = Column(String(200))

    machine = relationship('Machine')
