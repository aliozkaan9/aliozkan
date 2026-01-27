from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from cable_mes.database import db_session
from cable_mes.models import WorkOrder, Machine, Telemetry, QualityAlert, Product, User, UserRole
from cable_mes.services import MESService
from cable_mes.plc import plc_collector # Import PLC module
from flask_bcrypt import Bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_enterprise_key'

# Auth Setup
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('operator_dashboard'))
        else:
            flash('Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Admin Routes ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != UserRole.ADMIN:
        return "Access Denied", 403

    machines = Machine.query.all()
    # Get active WO for each machine for display
    active_wos = {}
    for m in machines:
        wo = WorkOrder.query.filter_by(machine_id=m.id, status='IN_PROGRESS').first()
        if wo: active_wos[m.id] = wo

    return render_template('admin_dashboard.html',
                           machines=machines,
                           work_orders=active_wos,
                           active_wo_count=len(active_wos))

# --- Operator Routes ---
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/operator')
@login_required
def operator_dashboard():
    machines = Machine.query.all()
    products = Product.query.all()
    return render_template('index.html', machines=machines, products=products) # Re-using the nice dashboard

# --- API Routes (Updated for PLC) ---

@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{'code': p.code, 'name': p.name} for p in products])

@app.route('/api/work-order', methods=['POST'])
def create_work_order():
    data = request.json
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/work-order/<int:wo_id>/start', methods=['POST'])
def start_work_order_api(wo_id):
    wo = WorkOrder.query.get(wo_id)
    if wo and MESService.start_work_order(wo.order_number):
        return jsonify({'message': 'Started'})
    return jsonify({'error': 'Could not start'}), 400

@app.route('/api/work-order/<int:wo_id>/stop', methods=['POST'])
def stop_work_order_api(wo_id):
    wo = WorkOrder.query.get(wo_id)
    if wo and MESService.stop_work_order(wo.order_number):
        return jsonify({'message': 'Stopped'})
    return jsonify({'error': 'Could not stop'}), 400

@app.route('/api/machine/<int:machine_id>')
def machine_status(machine_id):
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404

    # 1. Get Live Data from PLC Module
    # This now attempts real Modbus connection!
    plc_data = plc_collector.read_machine_data(machine)

    # ... (Rest of the logic similar to before, but using plc_data)

    wo = WorkOrder.query.filter_by(machine_id=machine_id, status='IN_PROGRESS').first()
    planned_wo = WorkOrder.query.filter_by(machine_id=machine_id, status='PLANNED').first() if not wo else None

    data = {
        'name': machine.name,
        'status': machine.status,
        'wo_id': None,
        'wo_number': '-',
        'product': '-',
        'target_length': 0,
        'produced_length': 0,
        'speed': plc_data['speed'],       # From PLC
        'temperature': plc_data['temp'],  # From PLC
        'diameter': plc_data['diam'],     # From PLC
        'oee': 0,
        'alerts': []
    }

    if planned_wo and not wo:
        data['wo_id'] = planned_wo.id
        data['wo_number'] = planned_wo.order_number
        data['product'] = planned_wo.product.code
        data['target_length'] = planned_wo.target_length_m
        data['status'] = 'READY'

    if wo:
        data['wo_id'] = wo.id
        data['wo_number'] = wo.order_number
        data['product'] = wo.product.code
        data['target_length'] = wo.target_length_m

        # In a real loop, we would save PLC data to DB here or in a background task.
        # For this request-response cycle, we'll just save it now to keep history updated
        # ONLY if machine is running
        if machine.status == 'RUNNING':
             MESService.process_telemetry(wo.order_number, plc_data['speed'], plc_data['temp'], plc_data['diam'])
             # Refresh from DB to get updated produced length
             db_session.refresh(wo)

        data['produced_length'] = round(wo.produced_length_m, 1)
        data['oee'] = round(MESService.get_oee(machine.name), 1)

        # Alerts
        alerts = QualityAlert.query.filter_by(work_order_id=wo.id)\
            .order_by(QualityAlert.timestamp.desc()).limit(5).all()
        data['alerts'] = [{'time': a.timestamp.strftime('%H:%M:%S'), 'msg': a.description} for a in alerts]

    return jsonify(data)

@app.route('/api/machine/<int:machine_id>/history')
def machine_history(machine_id):
    machine = Machine.query.get(machine_id)
    if not machine: return jsonify([]), 404

    wo = WorkOrder.query.filter_by(machine_id=machine_id, status='IN_PROGRESS').first()
    if not wo: return jsonify([])

    telemetry = Telemetry.query.filter_by(work_order_id=wo.id)\
        .order_by(Telemetry.timestamp.desc()).limit(30).all()

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
