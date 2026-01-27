from flask import Flask, render_template, jsonify, request
from cable_mes.database import db_session
from cable_mes.models import WorkOrder, Machine, Telemetry, QualityAlert, Product
from cable_mes.services import MESService
from datetime import datetime

app = Flask(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def index():
    machines = Machine.query.all()
    products = Product.query.all()
    return render_template('index.html', machines=machines, products=products)

@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{'code': p.code, 'name': p.name} for p in products])

@app.route('/api/work-order', methods=['POST'])
def create_work_order():
    data = request.json
    try:
        # Basic validation
        if not all(k in data for k in ('order_number', 'product_code', 'machine_id', 'target_length')):
            return jsonify({'error': 'Missing fields'}), 400

        machine = Machine.query.get(data['machine_id'])
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404

        wo = MESService.create_work_order(
            order_number=data['order_number'],
            product_code=data['product_code'],
            machine_name=machine.name,
            target_length=float(data['target_length'])
        )
        return jsonify({'message': 'Work Order Created', 'id': wo.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/work-order/<int:wo_id>/start', methods=['POST'])
def start_work_order_api(wo_id):
    wo = WorkOrder.query.get(wo_id)
    if not wo:
        return jsonify({'error': 'Work Order not found'}), 404

    if MESService.start_work_order(wo.order_number):
        return jsonify({'message': 'Started'})
    return jsonify({'error': 'Could not start'}), 400

@app.route('/api/work-order/<int:wo_id>/stop', methods=['POST'])
def stop_work_order_api(wo_id):
    wo = WorkOrder.query.get(wo_id)
    if not wo:
        return jsonify({'error': 'Work Order not found'}), 404

    if MESService.stop_work_order(wo.order_number):
        return jsonify({'message': 'Stopped'})
    return jsonify({'error': 'Could not stop'}), 400

@app.route('/api/machine/<int:machine_id>')
def machine_status(machine_id):
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404

    # Get active work order
    wo = WorkOrder.query.filter_by(machine_id=machine_id, status='IN_PROGRESS').first()

    # If no active WO, check for planned WO
    planned_wo = None
    if not wo:
        planned_wo = WorkOrder.query.filter_by(machine_id=machine_id, status='PLANNED').first()

    data = {
        'name': machine.name,
        'status': machine.status,
        'wo_id': None,
        'wo_number': '-',
        'product': '-',
        'target_length': 0,
        'produced_length': 0,
        'speed': 0,
        'temperature': 0,
        'diameter': 0,
        'oee': 0,
        'alerts': []
    }

    # Fill data for Planned WO (if no active WO)
    if planned_wo and not wo:
        data['wo_id'] = planned_wo.id
        data['wo_number'] = planned_wo.order_number
        data['product'] = planned_wo.product.code
        data['target_length'] = planned_wo.target_length_m
        data['status'] = 'READY' # Custom status for UI

    if wo:
        data['wo_id'] = wo.id
        data['wo_number'] = wo.order_number
        data['product'] = wo.product.code
        data['target_length'] = wo.target_length_m
        data['produced_length'] = round(wo.produced_length_m, 1)

        # Get latest telemetry
        last_tel = Telemetry.query.filter_by(work_order_id=wo.id)\
            .order_by(Telemetry.timestamp.desc()).first()

        if last_tel:
            data['speed'] = last_tel.line_speed_m_min
            data['temperature'] = last_tel.temperature_c
            data['diameter'] = last_tel.diameter_mm

        # Get active alerts (last 5)
        alerts = QualityAlert.query.filter_by(work_order_id=wo.id)\
            .order_by(QualityAlert.timestamp.desc()).limit(5).all()

        data['alerts'] = [{'time': a.timestamp.strftime('%H:%M:%S'), 'msg': a.description} for a in alerts]

        # Calculate OEE
        data['oee'] = round(MESService.get_oee(machine.name), 1)

    return jsonify(data)

@app.route('/api/machine/<int:machine_id>/history')
def machine_history(machine_id):
    # Returns last 60 seconds of telemetry for charts
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404

    wo = WorkOrder.query.filter_by(machine_id=machine_id, status='IN_PROGRESS').first()
    if not wo:
        return jsonify([])

    telemetry = Telemetry.query.filter_by(work_order_id=wo.id)\
        .order_by(Telemetry.timestamp.desc()).limit(30).all()

    # Reverse to show oldest first in chart
    data = []
    for t in reversed(telemetry):
        data.append({
            'time': t.timestamp.strftime('%H:%M:%S'),
            'speed': t.line_speed_m_min,
            'temp': t.temperature_c,
            'diam': t.diameter_mm
        })

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
