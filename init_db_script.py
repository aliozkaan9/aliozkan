from cable_mes.database import init_db, db_session
from cable_mes.models import Machine, Product

def seed_data():
    init_db()

    # Check if data exists
    if Machine.query.first():
        print("Data already exists.")
        return

    # Create Machines
    extruder1 = Machine(name='EXT-01', type='Extruder')
    extruder2 = Machine(name='EXT-02', type='Extruder')
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
    print("Database initialized and seeded.")

if __name__ == '__main__':
    seed_data()
