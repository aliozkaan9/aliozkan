from datetime import datetime
from cable_mes.database import db_session
from cable_mes.models import WorkOrder, Telemetry, QualityAlert, Machine, Product

class MESService:
    @staticmethod
    def create_work_order(order_number, product_code, machine_name, target_length):
        product = Product.query.filter_by(code=product_code).first()
        machine = Machine.query.filter_by(name=machine_name).first()

        if not product or not machine:
            raise ValueError("Product or Machine not found")

        wo = WorkOrder(
            order_number=order_number,
            product=product,
            machine=machine,
            target_length_m=target_length,
            status='PLANNED'
        )
        db_session.add(wo)
        db_session.commit()
        return wo

    @staticmethod
    def start_work_order(order_number):
        wo = WorkOrder.query.filter_by(order_number=order_number).first()
        if wo and wo.status == 'PLANNED':
            wo.status = 'IN_PROGRESS'
            wo.start_time = datetime.utcnow()
            wo.machine.status = 'RUNNING'
            db_session.commit()
            return True
        return False

    @staticmethod
    def stop_work_order(order_number):
        wo = WorkOrder.query.filter_by(order_number=order_number).first()
        if wo and wo.status == 'IN_PROGRESS':
            wo.status = 'COMPLETED'
            wo.end_time = datetime.utcnow()
            wo.machine.status = 'IDLE'
            db_session.commit()
            return True
        return False

    @staticmethod
    def process_telemetry(order_number, speed, temperature, diameter):
        """
        Receives real-time data from the machine.
        1. Saves telemetry.
        2. Updates produced length.
        3. Checks quality constraints.
        """
        wo = WorkOrder.query.filter_by(order_number=order_number).first()
        if not wo or wo.status != 'IN_PROGRESS':
            return None

        # 1. Save Telemetry
        telemetry = Telemetry(
            work_order=wo,
            line_speed_m_min=speed,
            temperature_c=temperature,
            diameter_mm=diameter
        )
        db_session.add(telemetry)

        # 2. Update Produced Length (Simplified logic: assuming 1 sec interval calling)
        # speed is in m/min, so m/sec = speed / 60
        produced_this_tick = speed / 60.0
        wo.produced_length_m += produced_this_tick

        # 3. Quality Check
        target_diam = wo.product.target_diameter_mm
        tolerance = wo.product.tolerance_mm

        if abs(diameter - target_diam) > tolerance:
            alert = QualityAlert(
                work_order=wo,
                alert_type='DIAMETER_OUT_OF_SPEC',
                measured_value=diameter,
                description=f"Diameter {diameter}mm is out of tolerance ({target_diam} ± {tolerance})"
            )
            db_session.add(alert)
            print(f"ALARM: {alert.description}")

        db_session.commit()
        return {
            "produced_length": wo.produced_length_m,
            "status": wo.status
        }

    @staticmethod
    def get_oee(machine_name):
        # Simplified OEE calculation
        # Availability: (Planned Time - Down Time) / Planned Time
        # Performance: (Actual Speed / Target Speed)
        # Quality: (Good Product / Total Product)
        # For this demo, we will just return a mock or simple calculation based on current WO

        machine = Machine.query.filter_by(name=machine_name).first()
        if not machine:
            return 0.0

        current_wo = WorkOrder.query.filter_by(machine_id=machine.id, status='IN_PROGRESS').first()
        if not current_wo:
            return 0.0

        # Simple Performance Ratio
        # Average speed of last 10 telemetry points
        last_telemetry = Telemetry.query.filter_by(work_order_id=current_wo.id)\
            .order_by(Telemetry.timestamp.desc()).limit(10).all()

        if not last_telemetry:
            return 0.0

        avg_speed = sum(t.line_speed_m_min for t in last_telemetry) / len(last_telemetry)
        target_speed = current_wo.product.target_speed_m_min

        performance = avg_speed / target_speed if target_speed > 0 else 0

        # Cap at 100% for simple demo
        return min(performance * 100, 100.0)
