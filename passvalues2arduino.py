import serial
import time
import sys

class ScaleToArduino:
    def __init__(self, scale_port='COM3', arduino_port='COM7'):
        """Inicjalizacja połączeń z wagą i Arduino"""
        self.scale_port = scale_port
        self.arduino_port = arduino_port
        
        try:
            # Połącz się z wagą
            self.scale_ser = serial.Serial(
                scale_port, 
                9600, 
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            print(f"Połączono z wagą na {scale_port}")
            
            # Połącz się z Arduino
            self.arduino_ser = serial.Serial(
                arduino_port,
                9600,
                timeout=1
            )
            time.sleep(2)  # Czekaj na inicjalizację Arduino
            print(f"Połączono z Arduino na {arduino_port}")
            
        except serial.SerialException as e:
            print(f"Błąd połączenia: {e}")
            sys.exit(1)
    
    def parse_scale_data(self, raw_data):
        """Parsuj dane z wagi"""
        try:
            # Przykład formatu: "ST,+ 0080.5 g"
            data_str = raw_data.decode('utf-8', errors='ignore').strip()
            
            # Znajdź liczbę
            parts = data_str.split()
            for part in parts:
                try:
                    # Usuń znaki niebędące cyframi/kropką/plusem/minusem
                    clean = part.replace('g', '').replace('kg', '').strip()
                    weight = float(clean)
                    return weight, data_str
                except ValueError:
                    continue
        except Exception as e:
            print(f"Błąd parsowania: {e}")
        
        return None, raw_data
    
    def send_to_arduino(self, weight):
        """Wyślij wagę do Arduino"""
        if weight is not None:
            # Format: "WEIGHT:80.5\n"
            command = f"WEIGHT:{weight:.2f}\n"
            self.arduino_ser.write(command.encode('utf-8'))
            print(f"Wysłano do Arduino: {command.strip()}")
            
            
            
            # Odczytaj odpowiedź z Arduino
            if self.arduino_ser.in_waiting:
                response = self.arduino_ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    print(f"Arduino: {response}")
    
    def run(self):
        """Główna pętla programu"""
        print("\nRozpoczynam transmisję danych...")
        print("Naciśnij Ctrl+C aby zatrzymać")
        
        try:
            while True:
                print("czeka")
                # 1. Odczytaj dane z wagi
                if self.scale_ser.in_waiting:
                    print("na co czekasz")
                    raw_data = self.scale_ser.readline()
                    print("nato?")
                    weight, raw_str = self.parse_scale_data(raw_data)
                    print("aha")
                    
                    if weight is not None:
                        print(f"Waga: {weight:.2f} g (raw: {raw_str})")
                        
                        # 2. Wyślij do Arduino
                        self.send_to_arduino(weight)
                
                # 3. Sprawdź komendy użytkownika
                print("wtf")
                self.scale_ser.write(b'T\r\n')
                    
                
        except KeyboardInterrupt:
            print("\nPrzerwano przez użytkownika")
    
    def close(self):
        """Zamknij połączenia"""
        if hasattr(self, 'scale_ser'):
            self.scale_ser.close()
        if hasattr(self, 'arduino_ser'):
            self.arduino_ser.close()
        print("Połączenia zamknięte")

# Użycie
if __name__ == "__main__":
    # Ustaw swoje porty!
    transmitter = ScaleToArduino(
        scale_port='COM3',    # Port konwertera wagi
        arduino_port='COM7'   # Port Arduino
    )
    transmitter.run()