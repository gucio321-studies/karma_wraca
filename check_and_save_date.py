import sys
import json
import os
from datetime import datetime, time
from threading import Thread, Event
import time as time_module

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QListWidget, QComboBox, QMessageBox, QGroupBox,
                               QListWidgetItem, QFrame)
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QFont
import serial
import serial.tools.list_ports
import passvalues2arduino


#transmitter = passvalues2arduino.ScaleToArduino(
#        scale_port='COM1',    # Port konwertera wagi
#        arduino_port='COM14'   # Port Arduino
#    )


class SerialWorker(QObject):
    message_received = Signal(str)
    connection_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.is_connected = False
        self._stop_event = Event()
        
    def connect_serial(self, port):
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1
            )
            self.is_connected = True
            self.connection_changed.emit(True)
            self.message_received.emit(f"Połączono z Arduino na porcie {port}")
        except Exception as e:
            self.message_received.emit(f"Błąd połączenia: {str(e)}")
            self.connection_changed.emit(False)
            
    def disconnect_serial(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            self.is_connected = False
            self.connection_changed.emit(False)
            self.message_received.emit("Rozłączono z Arduino")
        except Exception as e:
            self.message_received.emit(f"Błąd przy rozłączaniu: {str(e)}")
            
    def send_message(self, message):
        if self.is_connected and self.serial_connection:
            try:
                self.serial_connection.write(f"{message}\n".encode())
                self.message_received.emit(f"Wysłano: {message}")
            except Exception as e:
                self.message_received.emit(f"Błąd wysyłania: {str(e)}")
                self.connection_changed.emit(False)


class ArduinoSchedulerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scheduled_times = []
        self.serial_worker = SerialWorker()
        self.monitoring_active = True
        
        self.setup_ui()
        self.setup_timers()
        self.load_saved_times()
        self.setup_serial_thread()
        
    def setup_ui(self):
        self.setWindowTitle("Arduino Scheduler - PySide6")
        self.setGeometry(100, 100, 600, 600)
        
        # Główny widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Sekcja połączenia z Arduino
        connection_group = QGroupBox("Połączenie z Arduino")
        connection_layout = QVBoxLayout(connection_group)
        
        # Wybór portu
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port COM:"))
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        
        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn)
        
        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.toggle_connection)
        port_layout.addWidget(self.connect_btn)
        
        connection_layout.addLayout(port_layout)
        
        # Status połączenia
        self.status_label = QLabel("Status: Niepołączono")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        connection_layout.addWidget(self.status_label)
        
        # Wiadomości
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: blue;")
        connection_layout.addWidget(self.message_label)
        
        layout.addWidget(connection_group)
        
        # Sekcja dodawania godzin
        schedule_group = QGroupBox("Dodaj godzinę")
        schedule_layout = QHBoxLayout(schedule_group)
        
        schedule_layout.addWidget(QLabel("Godzina (HH:MM):"))
        
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("np. 14:30")
        schedule_layout.addWidget(self.time_edit)
        
        self.add_btn = QPushButton("Dodaj")
        self.add_btn.clicked.connect(self.add_time)
        schedule_layout.addWidget(self.add_btn)
        
        layout.addWidget(schedule_group)
        
        # Lista zaplanowanych godzin
        times_group = QGroupBox("Zaplanowane godziny")
        times_layout = QVBoxLayout(times_group)
        
        self.times_list = QListWidget()
        times_layout.addWidget(self.times_list)
        
        # Przyciski zarządzania listą
        buttons_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.remove_btn.clicked.connect(self.remove_selected_time)
        buttons_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Wyczyść listę")
        self.clear_btn.clicked.connect(self.clear_times)
        buttons_layout.addWidget(self.clear_btn)
        
        self.test_btn = QPushButton("Testuj Arduino")
        self.test_btn.clicked.connect(self.test_arduino)
        buttons_layout.addWidget(self.test_btn)
        
        times_layout.addLayout(buttons_layout)
        
        layout.addWidget(times_group)
        
        # Aktualny czas
        time_group = QGroupBox("Aktualny czas")
        time_layout = QVBoxLayout(time_group)
        
        self.current_time_label = QLabel()
        self.current_time_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.current_time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.current_time_label)
        
        layout.addWidget(time_group)
        
    def setup_timers(self):
        # Timer do aktualizacji czasu
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_current_time)
        self.time_timer.start(1000)  # co 1 sekundę
        self.update_current_time()
        
        # Timer do sprawdzania zaplanowanych godzin
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_scheduled_times)
        self.check_timer.start(1000)  # co 1 sekundę
        
    def setup_serial_thread(self):
        # Przenosimy worker do głównego wątku dla prostoty
        # W prawdziwej aplikacji można użyć QThread
        self.serial_worker.message_received.connect(self.on_serial_message)
        self.serial_worker.connection_changed.connect(self.on_connection_changed)
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device, port.description)
        
    def toggle_connection(self):
        if self.serial_worker.is_connected:
            self.serial_worker.disconnect_serial()
        else:
            port = self.port_combo.currentText()
            if port:
                self.serial_worker.connect_serial(port)
            else:
                QMessageBox.warning(self, "Błąd", "Wybierz port COM!")
                
    def on_connection_changed(self, connected):
        if connected:
            self.status_label.setText("Status: Połączono")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Rozłącz")
        else:
            self.status_label.setText("Status: Niepołączono")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Połącz")
            
    def on_serial_message(self, message):
        self.message_label.setText(message)
        
    def add_time(self):
        time_str = self.time_edit.text().strip()
        
        if not self.validate_time(time_str):
            QMessageBox.warning(self, "Błąd", "Podaj poprawną godzinę w formacie HH:MM (00:00 - 23:59)")
            return
            
        if time_str in self.scheduled_times:
            QMessageBox.warning(self, "Błąd", "Ta godzina jest już na liście!")
            return
            
        self.scheduled_times.append(time_str)
        self.update_times_list()
        self.save_times()
        self.time_edit.clear()
        
    def validate_time(self, time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except:
            return False
            
    def remove_selected_time(self):
        selected_items = self.times_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Błąd", "Wybierz godzinę do usunięcia!")
            return
            
        for item in selected_items:
            time_str = item.text().split(' - ')[0]
            if time_str in self.scheduled_times:
                self.scheduled_times.remove(time_str)
                
        self.update_times_list()
        self.save_times()
        
    def clear_times(self):
        if self.scheduled_times:
            reply = QMessageBox.question(self, "Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić całą listę?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.scheduled_times.clear()
                self.update_times_list()
                self.save_times()
                
    def update_times_list(self):
        self.times_list.clear()
        current_time = datetime.now().strftime("%H:%M")
        
        for time_str in sorted(self.scheduled_times):
            if time_str == current_time:
                item = QListWidgetItem(f"{time_str} - AKTYWNE TERAZ")
                
                #transmitter = passvalues2arduino.ScaleToArduino(
                #        scale_port='COM1',    # Port konwertera wagi
                #        arduino_port='COM14'   # Port Arduino
                #    )

                #transmitter.run()
                item.setBackground(Qt.green)
            else:
                item = QListWidgetItem(f"{time_str} - Oczekuje")
            self.times_list.addItem(item)
            
    def update_current_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.setText(f"Aktualny czas: {current_time}")

        
        
    def check_scheduled_times(self):
        if not self.scheduled_times or not self.serial_worker.is_connected:
            return
                    
        for scheduled_time in self.scheduled_times:
            time_diff = datetime.strptime(scheduled_time, "%H:%M").time() - datetime.now().hour - datetime.now().minute
            print(time_diff)
            if int(time_diff) < 1:
                self.trigger_arduino(scheduled_time)
                # Aktualizacja listy
                self.update_times_list()
                
                
                
    def trigger_arduino(self, time_str):
        """Wysyła sygnał do Arduino gdy godzina zostanie osiągnięta"""
        message = f"TRIGGER:{time_str}"
        self.serial_worker.send_message(message)
        
        # Możesz dodać różne komendy w zależności od godziny
        # self.serial_worker.send_message("LED_ON")
        # self.serial_worker.send_message("BUZZER")
        
    def test_arduino(self):
        """Testowe wysłanie komendy do Arduino"""
        if self.serial_worker.is_connected:
            self.serial_worker.send_message("TEST")
        else:
            QMessageBox.warning(self, "Błąd", "Najpierw połącz się z Arduino!")
            
    def load_saved_times(self):
        """Ładuje zapisane godziny z pliku"""
        try:
            if os.path.exists("scheduled_times.json"):
                with open("scheduled_times.json", "r") as f:
                    self.scheduled_times = json.load(f)
                self.update_times_list()
        except Exception as e:
            print(f"Błąd przy ładowaniu zapisanych godzin: {e}")
            
    def save_times(self):
        """Zapisuje godziny do pliku"""
        try:
            with open("scheduled_times.json", "w") as f:
                json.dump(self.scheduled_times, f)
        except Exception as e:
            print(f"Błąd przy zapisywaniu godzin: {e}")
            
    def closeEvent(self, event):
        """Zamykanie aplikacji"""
        if self.serial_worker.is_connected:
            self.serial_worker.disconnect_serial()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    window = ArduinoSchedulerApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()