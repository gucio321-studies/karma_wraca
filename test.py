#!/usr/bin/env python3
import serial
import time
import matplotlib.pyplot as plt
import numpy as np

# Ustawienia portu szeregowego - ZMIEŃ PORT NA TEN UŻYWANY PRZEZ KONWERTER RS-232/USB
# Przykład: 'COM5' (Windows) lub '/dev/ttyUSB1' (Linux/macOS)
PORT_SCALE = 'COM3'  
BAUD_RATE = 9600  # Upewnij się, że to pasuje do ustawień Twojej wagi BS600M!

def parse_weight(raw_line):
    """
    Parsuje surowy ciąg znaków z wagi (np. 'WTST+   0.00  g')
    i zwraca wartość masy jako liczbę float.
    """
    # 1. Usuń białe znaki z początku i końca.
    cleaned = raw_line.strip()
   
    # Przykładowy format BS600M: 'WTST+ 0.00 g'
    # 2. Rozdziel ciąg na słowa (elementy)
    parts = cleaned.split()
   
    # 3. Sprawdź, czy mamy oczekiwaną liczbę elementów (np. 3 lub 4)
    if len(parts) >= 2:
        try:
            # 4. Spróbuj przekształcić elementy na float.
            # Znajdź element, który jest liczbą (z kropką dziesiętną)
            for part in parts:
                # Usuń ewentualne jednostki (g, kg) z końca
                part_clean = part.replace('g', '').replace('kg', '').strip()
                try:
                    weight_value = float(part_clean)
                    return weight_value
                except ValueError:
                    continue  # To nie była liczba, idziemy dalej
        except Exception as e:
            print(f"Błąd parsowania: {e} dla linii: {raw_line}")
            return None
    
    return None



ser = serial.Serial(PORT_SCALE, BAUD_RATE, timeout=1)
print(f"Połączono z {PORT_SCALE} przy {BAUD_RATE} baud")
x_data, y_data = [], []
start_time = time.time()  

while True:    
        current_time = time.time()
        
        # Sprawdź czy są dane do odczytu
        if ser.in_waiting > 0:
            try:
                # Odczytaj linię (zakładając, że waga wysyła dane zakończone znakiem nowej linii)
                print("czeka")
                raw_bytes = ser.readline()
                print("aha")
                raw_line = raw_bytes.decode('utf-8', errors='ignore').strip()
                
                if raw_line:  # Sprawdź czy linia nie jest pusta
                    # Wypisanie odebranego sygnału
                    print(f"Odebrano: {repr(raw_line)}")
                    
                    # Parsowanie wagi
                    weight = parse_weight(raw_line)
                    
                    if weight is not None:
                        # Dodanie nowych danych
                        elapsed_time = current_time - start_time
                        x_data.append(elapsed_time)
                        y_data.append(weight)
                        
                        print(f"Czas: {elapsed_time:.2f}s, Masa: {weight:.2f}g")
                    else:
                        print(f"Nie udało się sparsować linii: {raw_line}")
            except Exception as e:
                print(f"Błąd odczytu: {e}")
