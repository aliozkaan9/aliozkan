import random
import time
from pymodbus.client import ModbusTcpClient
from cable_mes.models import Machine

class PLCCollector:
    """
    Connects to physical PLCs using Modbus TCP.
    Falls back to simulation mode if connection fails.
    """

    def __init__(self):
        self.clients = {} # Cache clients

    def read_machine_data(self, machine: Machine):
        """
        Reads Speed, Temp, Diameter from PLC.
        Returns dict: {'speed': float, 'temp': float, 'diam': float}
        """

        # 1. Try connecting to Real PLC
        client = self._get_client(machine.plc_ip, machine.plc_port)

        data = None
        if client:
            try:
                # Read Holding Registers
                # Assuming 3 registers starting from reg_speed
                # Note: pymodbus uses 0-based addressing usually, but reg might be 40001
                # Adjust address logic based on PLC type
                start_addr = machine.reg_speed if machine.reg_speed < 10000 else machine.reg_speed - 40001

                rr = client.read_holding_registers(start_addr, count=3, slave=machine.plc_slave_id)
                if not rr.isError():
                    # Simple scaling (e.g. PLC sends integer 345 for 3.45)
                    # This is highly dependent on PLC programming
                    regs = rr.registers
                    data = {
                        'speed': regs[0] / 1.0,
                        'temp': regs[1] / 10.0,
                        'diam': regs[2] / 100.0
                    }
            except Exception as e:
                print(f"PLC Read Error ({machine.name}): {e}")
                client.close()
                del self.clients[f"{machine.plc_ip}:{machine.plc_port}"]

        # 2. Fallback to Simulation if no data
        if data is None:
            data = self._simulate_data(machine)

        return data

    def _get_client(self, ip, port):
        if not ip: return None
        key = f"{ip}:{port}"

        if key not in self.clients:
            client = ModbusTcpClient(ip, port=port, timeout=1)
            if client.connect():
                self.clients[key] = client
            else:
                return None
        return self.clients[key]

    def _simulate_data(self, machine):
        """Generates realistic dummy data based on machine status"""
        if machine.status != 'RUNNING':
            return {'speed': 0, 'temp': 20, 'diam': 0}

        # Fluctuate around targets (Simplified)
        #Ideally this should check the active WO for targets
        base_speed = 100
        base_temp = 150
        base_diam = 3.4

        return {
            'speed': base_speed + random.randint(-2, 2),
            'temp': round(base_temp + random.uniform(-1, 1), 1),
            'diam': round(base_diam + random.uniform(-0.05, 0.05), 3)
        }

# Singleton instance
plc_collector = PLCCollector()
