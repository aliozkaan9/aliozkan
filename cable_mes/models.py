from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from cable_mes.database import Base
from datetime import datetime

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    type = Column(String(50)) # e.g., 'Extruder', 'Buncher'
    status = Column(String(20), default='IDLE') # IDLE, RUNNING, STOPPED, MAINTENANCE

    def __repr__(self):
        return f'<Machine {self.name}>'

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False) # e.g., 'NYA-2.5'
    name = Column(String(100), nullable=False)
    target_diameter_mm = Column(Float, nullable=False)
    tolerance_mm = Column(Float, nullable=False) # e.g., 0.05
    target_speed_m_min = Column(Float, default=100.0)

    def __repr__(self):
        return f'<Product {self.code}>'

class WorkOrder(Base):
    __tablename__ = 'work_orders'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=False)
    target_length_m = Column(Float, nullable=False)
    produced_length_m = Column(Float, default=0.0)
    status = Column(String(20), default='PLANNED') # PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    product = relationship('Product')
    machine = relationship('Machine')

    def __repr__(self):
        return f'<WorkOrder {self.order_number}>'

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
    alert_type = Column(String(50)) # e.g., 'DIAMETER_OUT_OF_SPEC'
    measured_value = Column(Float)
    description = Column(String(200))

    work_order = relationship('WorkOrder')
