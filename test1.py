import sys
import json
import os
import serial
import serial.tools.list_ports
import time as time_module
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QListWidget, QComboBox, QMessageBox, QGroupBox,
                               QListWidgetItem)
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# import passvalues2arduino # Odkomentuj w produkcji

path = Path(__file__).parent
PORT_SCALE = 'COM1'  
BAUD_RATE_SCALE = 9600 

def parse_weight(raw_line):
    return np.random.randint(1, 100) #TODO Test żeby sprawdzić czy będzie działać
    """
    Parsuje surowy ciąg znaków z wagi (np. 'WTST+   0.00  g')
    i zwraca wartość masy jako liczbę float.
    """
    cleaned = raw_line.strip()
    parts = cleaned.split()
    if len(parts) >= 2:
        try:
            for part in parts:
                part_clean = part.replace('g', '').replace('kg', '').strip()
                try:
                    weight_value = float(part_clean)
                    return weight_value
                except ValueError:
                    continue
        except Exception as e:
            print(f"Błąd parsowania: {e} dla linii: {raw_line}")
            return None
    return None

class SerialWorker(QObject):
    message_received = Signal(str)
    connection_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.is_connected = False
        
    def connect_serial(self, port):
        try:
            self.serial_connection = serial.Serial(port=port, baudrate=9600, timeout=1)
            self.is_connected = True
            self.connection_changed.emit(True)
            self.message_received.emit(f"Połączono z Arduino na porcie {port}")
        except Exception as e:
            self.message_received.emit(f"Błąd połączenia: {str(e)}")
            self.connection_changed.emit(False)
            
    def disconnect_serial(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        self.connection_changed.emit(False)
        self.message_received.emit("Rozłączono z Arduino")
            
    def send_message(self, message):
        if self.is_connected and self.serial_connection:
            try:
                self.serial_connection.write(f"{message}\n".encode())
                self.message_received.emit(f"Wysłano: {message}")
            except Exception as e:
                self.message_received.emit(f"Błąd wysyłania: {str(e)}")

class ArduinoSchedulerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x_data, self.y_data = [], []
        self.seconds_data = []
        self.start_time = time_module.time()
        self.start_date = datetime.datetime.now()
        self.last_triggered_time = ""

        self.scheduled_times = []
        self.serial_worker = SerialWorker()
        
        self.setup_ui()
        self.setup_timers()
        self.load_saved_times()
        self.setup_serial_thread()
        
    def setup_ui(self):
        self.setWindowTitle("Arduino Scheduler & Scale Monitor")
        self.setGeometry(100, 100, 900, 850)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # --- GÓRA: KONFIGURACJA ---
        top_layout = QHBoxLayout()
        
        # Połączenie
        left_col = QVBoxLayout()
        connection_group = QGroupBox("Połączenie z Arduino")
        conn_l = QVBoxLayout(connection_group)
        port_l = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_l.addWidget(self.port_combo)
        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.toggle_connection)
        port_l.addWidget(self.connect_btn)
        conn_l.addLayout(port_l)
        self.status_label = QLabel("Status: Niepołączono")
        conn_l.addWidget(self.status_label)
        self.message_label = QLabel("")
        conn_l.addWidget(self.message_label)
        left_col.addWidget(connection_group)

        time_group = QGroupBox("Aktualny czas")
        time_l = QVBoxLayout(time_group)
        self.current_time_label = QLabel()
        self.current_time_label.setFont(QFont("Arial", 14, QFont.Bold))
        time_l.addWidget(self.current_time_label)
        left_col.addWidget(time_group)
        top_layout.addLayout(left_col)

        # Harmonogram
        right_col = QVBoxLayout()
        sched_group = QGroupBox("Dodaj Karmienie")
        sched_l = QVBoxLayout(sched_group)
        
        input_l = QHBoxLayout()
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("HH:MM")
        self.time_edit.setFixedWidth(50)
        input_l.addWidget(self.time_edit)
        
        self.weight_edit = QLineEdit()
        self.weight_edit.setPlaceholderText("Masa")
        self.weight_edit.setFixedWidth(60)
        input_l.addWidget(self.weight_edit)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["g", "kg"])
        self.unit_combo.setFixedWidth(50)
        input_l.addWidget(self.unit_combo)
        
        add_btn = QPushButton("Dodaj")
        add_btn.clicked.connect(self.add_time)
        input_l.addWidget(add_btn)
        sched_l.addLayout(input_l)

        self.times_list = QListWidget()
        sched_l.addWidget(self.times_list)
        
        btn_l = QHBoxLayout()
        rem_btn = QPushButton("Usuń Zaznaczone")
        rem_btn.clicked.connect(self.remove_selected_time)
        btn_l.addWidget(rem_btn)
        test_btn = QPushButton("Testuj Arduino")
        test_btn.clicked.connect(self.test_arduino)
        btn_l.addWidget(test_btn)
        sched_l.addLayout(btn_l)
        
        right_col.addWidget(sched_group)
        top_layout.addLayout(right_col)
        main_layout.addLayout(top_layout)

        # --- DÓŁ: WYKRES ---
        graph_group = QGroupBox("Wykres Masy")
        graph_l = QVBoxLayout(graph_group)
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        graph_l.addWidget(self.canvas)
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self._setup_ax()
        main_layout.addWidget(graph_group)

    def _setup_ax(self):
        self.ax.set_xlim(self.start_date, self.start_date + datetime.timedelta(seconds=30))
        self.ax.set_ylim(-0.1, 1.0)
        self.ax.set_xlabel("Czas")
        self.ax.set_ylabel("Masa [g]")
        self.ax.grid(True, alpha=0.3)

    def setup_timers(self):
        self.master_timer = QTimer()
        self.master_timer.timeout.connect(self.tick)
        self.master_timer.start(1000)

        self.weight_timer = QTimer()
        self.weight_timer.timeout.connect(self.update_weight_data)
        self.weight_timer.start(50)

        self.draw_timer = QTimer()
        self.draw_timer.timeout.connect(self.refresh_plot)
        self.draw_timer.start(3000)

    def tick(self):
        curr_dt = datetime.datetime.now()
        self.current_time_label.setText(f"Aktualny czas: {curr_dt.strftime('%H:%M:%S')}")
        self.check_scheduled_times(curr_dt)

    def update_weight_data(self):
        current_time = time_module.time()
        # if self.ser_scale.in_waiting > 0: # TODO
        if 1:
            raw_line = "WTST+ 0.00 g" # TODO zastąpić
            weight = parse_weight(raw_line)
            if weight is not None:
                elapsed = current_time - self.start_time
                self.x_data.append(self.start_date + datetime.timedelta(seconds=elapsed))
                self.y_data.append(weight)
                self.seconds_data.append(elapsed)

    def refresh_plot(self):
        if self.seconds_data:
            self.line.set_xdata(self.x_data)
            self.line.set_ydata(self.y_data)
            if self.seconds_data[-1] > 30:
                self.ax.set_xlim(self.x_data[-1] - datetime.timedelta(seconds=30), self.x_data[-1])
            y_min, y_max = min(self.y_data), max(self.y_data)
            margin = (y_max - y_min) * 0.1 if y_max != y_min else 0.5
            self.ax.set_ylim(min(0, y_min) - margin, y_max + margin)
            self.canvas.draw()

    def check_scheduled_times(self, now):
        current_hm = now.strftime("%H:%M")
        if current_hm == self.last_triggered_time: return
        for entry in self.scheduled_times:
            if entry['time'] == current_hm:
                self.trigger_arduino(entry)
                self.last_triggered_time = current_hm
                self.update_times_list()
                break

    def trigger_arduino(self, entry):
        """Wysyła sygnał i uruchamia transmiter z wybraną przez użytkownika jednostką"""
        time_str = entry['time']
        target_val = entry['target']
        unit = entry['unit']
        
        # Log do konsoli GUI
        message = f"TRIGGER:{time_str} | CEL: {target_val}{unit}"
        self.serial_worker.send_message(message)
        
        # ODKOMENTUJ W PRODUKCJI:
        # transmitter = passvalues2arduino.ScaleToArduino(
        #     scale_port='COM1',
        #     arduino_port='COM14',
        #     target_weight=float(target_val),
        #     weight_unit=unit   
        # )
        # transmitter.run()

    def add_time(self):
        t = self.time_edit.text().strip()
        w = self.weight_edit.text().strip().replace(',', '.')
        u = self.unit_combo.currentText()
        
        try:
            val = float(w)
            if self.validate_time(t) and not any(i['time'] == t for i in self.scheduled_times):
                self.scheduled_times.append({'time': t, 'target': val, 'unit': u})
                self.update_times_list()
                self.save_times()
                self.time_edit.clear()
                self.weight_edit.clear()
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Podaj poprawną wagę!")

    def validate_time(self, t):
        try:
            h, m = map(int, t.split(':'))
            return 0 <= h <= 23 and 0 <= m <= 59
        except: return False

    def update_times_list(self):
        self.times_list.clear()
        now_hm = datetime.datetime.now().strftime("%H:%M")
        self.scheduled_times.sort(key=lambda x: x['time'])
        for e in self.scheduled_times:
            status = 'AKTYWNE' if e['time'] == now_hm else 'Oczekuje'
            item = QListWidgetItem(f"{e['time']} -> {e['target']}{e['unit']} ({status})")
            if e['time'] == now_hm: item.setBackground(Qt.green)
            self.times_list.addItem(item)

    def remove_selected_time(self):
        for item in self.times_list.selectedItems():
            t = item.text().split(' -> ')[0]
            self.scheduled_times = [i for i in self.scheduled_times if i['time'] != t]
        self.update_times_list()
        self.save_times()

    def setup_serial_thread(self):
        self.serial_worker.message_received.connect(self.on_serial_message)
        self.serial_worker.connection_changed.connect(self.on_connection_changed)

    def refresh_ports(self):
        self.port_combo.clear()
        for p in serial.tools.list_ports.comports(): self.port_combo.addItem(p.device)

    def toggle_connection(self):
        if self.serial_worker.is_connected: self.serial_worker.disconnect_serial()
        else: self.serial_worker.connect_serial(self.port_combo.currentText())

    def on_connection_changed(self, connected):
        self.status_label.setText(f"Status: {'Połączono' if connected else 'Niepołączono'}")
        self.status_label.setStyleSheet(f"color: {'green' if connected else 'red'}; font-weight: bold;")
        self.connect_btn.setText("Rozłącz" if connected else "Połącz")

    def on_serial_message(self, message): self.message_label.setText(message)

    def test_arduino(self):
        if self.serial_worker.is_connected: self.serial_worker.send_message("TEST")

    def load_saved_times(self):
        if os.path.exists("scheduled_times.json"):
            with open("scheduled_times.json", "r") as f: self.scheduled_times = json.load(f)
            self.update_times_list()

    def save_times(self):
        with open("scheduled_times.json", "w") as f: json.dump(self.scheduled_times, f)

    def closeEvent(self, event):
        if len(self.x_data) > 0:
            save_path = path / "pomiary"
            save_path.mkdir(exist_ok=True)
            filename = save_path / f"pomiary_wagi_{time_module.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write("Czas\tMasa[g]\n")
                for x, y in zip(self.x_data, self.y_data): f.write(f"{x}\t{y:.3f}\n")
        if self.serial_worker.is_connected: self.serial_worker.disconnect_serial()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoSchedulerApp()
    window.show()
    sys.exit(app.exec())