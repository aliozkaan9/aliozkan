from cable_mes.services import MESService
from cable_mes.database import init_db
from cable_mes.models import WorkOrder

# Initialize DB
init_db()

# Test Creation
print("Creating Work Order...")
try:
    wo = MESService.create_work_order('WO-1001', 'NYA-2.5', 'EXT-01', 5000)
    print(f"Work Order Created: {wo}")
except Exception as e:
    print(f"Error creating WO (might already exist): {e}")

# Test Start
print("Starting Work Order...")
MESService.start_work_order('WO-1001')

# Test Telemetry (Good data)
print("Processing Good Telemetry...")
res = MESService.process_telemetry('WO-1001', speed=100, temperature=150, diameter=3.41)
print(f"Result: {res}")

# Test Telemetry (Bad data - triggers alert)
print("Processing Bad Telemetry...")
res = MESService.process_telemetry('WO-1001', speed=100, temperature=150, diameter=3.6) # Target 3.4, Tol 0.1 -> 3.5 max
print(f"Result: {res}")

# Test OEE
print("Calculating OEE...")
oee = MESService.get_oee('EXT-01')
print(f"OEE: {oee}%")

# Test Stop
print("Stopping Work Order...")
MESService.stop_work_order('WO-1001')
