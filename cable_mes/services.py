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
        bd = MESService.get_oee_breakdown(machine_name)
        return bd['oee']

    @staticmethod
    def get_oee_breakdown(machine_name):
        machine = Machine.query.filter_by(name=machine_name).first()
        if not machine:
            return {'availability': 0, 'performance': 0, 'quality': 0, 'oee': 0}

        # Simplified Logic for Demo
        # 1. Availability (Mocked based on status)
        availability = 1.0 if machine.status == 'RUNNING' else 0.95

        # 2. Performance
        performance = 0.0
        current_wo = WorkOrder.query.filter_by(machine_id=machine.id, status='IN_PROGRESS').first()
        if current_wo:
            last_telemetry = Telemetry.query.filter_by(work_order_id=current_wo.id)\
                .order_by(Telemetry.timestamp.desc()).limit(20).all()
            if last_telemetry:
                avg_speed = sum(t.line_speed_m_min for t in last_telemetry) / len(last_telemetry)
                target_speed = current_wo.product.target_speed_m_min
                performance = avg_speed / target_speed if target_speed > 0 else 0

        # 3. Quality
        # Check alerts count vs total produced length (Rough approximation)
        quality = 1.0
        if current_wo and current_wo.produced_length_m > 0:
            alerts_count = QualityAlert.query.filter_by(work_order_id=current_wo.id).count()
            # Assume each alert ruins 100m of cable
            bad_product = alerts_count * 100
            total_product = current_wo.produced_length_m
            if total_product > 0:
                quality = max(0, (total_product - bad_product) / total_product)

        # Cap values
        availability = min(availability, 1.0)
        performance = min(performance, 1.0)
        quality = min(quality, 1.0)

        oee = availability * performance * quality

        return {
            'availability': round(availability * 100, 1),
            'performance': round(performance * 100, 1),
            'quality': round(quality * 100, 1),
            'oee': round(oee * 100, 1)
        }
