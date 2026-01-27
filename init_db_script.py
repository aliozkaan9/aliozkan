from cable_mes.database import init_db, db_session
from cable_mes.models import Machine, Product, User, UserRole
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def seed_data():
    init_db()

    # Check if data exists
    if User.query.first():
        print("Data already exists.")
        return

    # Create Users
    admin = User(
        username='admin',
        password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
        role=UserRole.ADMIN,
        full_name='System Administrator'
    )
    operator = User(
        username='operator',
        password_hash=bcrypt.generate_password_hash('op123').decode('utf-8'),
        role=UserRole.OPERATOR,
        full_name='John Doe'
    )
    db_session.add(admin)
    db_session.add(operator)

    # Create Machines with PLC Config
    extruder1 = Machine(
        name='EXT-01',
        type='Extruder',
        plc_ip='192.168.1.101', # Example PLC IP
        reg_speed=40001,
        reg_temp=40002,
        reg_diameter=40003
    )
    extruder2 = Machine(
        name='EXT-02',
        type='Extruder',
        plc_ip='192.168.1.102'
    )
    coiler1 = Machine(name='COIL-01', type='Coiler')

    # Create Products
    p1 = Product(code='NYA-2.5', name='NYA 2.5mm Power Cable', target_diameter_mm=3.4, tolerance_mm=0.1)
    p2 = Product(code='CAT6-UTP', name='Cat6 UTP Ethernet Cable', target_diameter_mm=0.57, tolerance_mm=0.02)

    db_session.add(extruder1)
    db_session.add(extruder2)
    db_session.add(coiler1)
    db_session.add(p1)
    db_session.add(p2)

    db_session.commit()
    print("Database initialized with Enterprise data (Users, PLCs).")

if __name__ == '__main__':
    seed_data()
