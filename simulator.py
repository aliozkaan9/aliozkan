import time
import random
from cable_mes.services import MESService
from cable_mes.database import init_db

def run_simulation(machine_name='EXT-01', product_code='NYA-2.5', duration_seconds=60):
    print(f"--- Starting Simulation for {machine_name} producing {product_code} ---")

    # 1. Setup Work Order
    wo_number = f"WO-{random.randint(1000, 9999)}"
    print(f"Creating Work Order: {wo_number}")
    try:
        MESService.create_work_order(wo_number, product_code, machine_name, 10000)
    except Exception as e:
        print(f"Could not create WO: {e}")
        return

    MESService.start_work_order(wo_number)
    print("Work Order Started.")

    # 2. Simulation Loop
    target_diam = 3.4
    current_speed = 0
    target_speed = 100

    try:
        for i in range(duration_seconds):
            # Ramp up speed
            if current_speed < target_speed:
                current_speed += 10

            # Simulate Diameter (Random fluctuation)
            # 10% chance of anomaly
            if random.random() < 0.1:
                variation = random.uniform(0.15, 0.3) * random.choice([-1, 1])
            else:
                variation = random.uniform(0.0, 0.05) * random.choice([-1, 1])

            measured_diam = round(target_diam + variation, 3)

            # Simulate Temperature
            temperature = round(150 + random.uniform(-2, 2), 1)

            # Send Data
            print(f"[{i+1}/{duration_seconds}] Speed: {current_speed}m/min | Temp: {temperature}C | Diam: {measured_diam}mm", end="")

            result = MESService.process_telemetry(wo_number, current_speed, temperature, measured_diam)

            if abs(measured_diam - target_diam) > 0.1: # calculated based on seeded product tolerance
                 print(" [ALERT!]", end="")

            print(f" | Produced: {round(result['produced_length'], 2)}m")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        MESService.stop_work_order(wo_number)
        print("Work Order Stopped.")

if __name__ == '__main__':
    # Ensure DB is ready
    init_db()
    run_simulation()
