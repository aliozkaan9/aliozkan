from flask import Flask, render_template, jsonify
from cable_mes.database import db_session
from cable_mes.models import WorkOrder, Machine, Telemetry, QualityAlert
from cable_mes.services import MESService

app = Flask(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def index():
    machines = Machine.query.all()
    return render_template('index.html', machines=machines)

@app.route('/api/machine/<int:machine_id>')
def machine_status(machine_id):
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404

    # Get active work order
    wo = WorkOrder.query.filter_by(machine_id=machine_id, status='IN_PROGRESS').first()

    data = {
        'name': machine.name,
        'status': machine.status,
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

    if wo:
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
