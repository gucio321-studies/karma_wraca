import serial
import time

import matplotlib.pyplot as plt
import time
import numpy as np

# Ustawienia portu szeregowego - ZMIEŃ PORT NA TEN UŻYWANY PRZEZ KONWERTER RS-232/USB
# Przykład: 'COM5' (Windows) lub '/dev/ttyUSB1' (Linux/macOS)
PORT_SCALE = 'COM3'  
BAUD_RATE = 9600 # Upewnij się, że to pasuje do ustawień Twojej wagi BS600M!


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
    if len(parts) >= 2 and ('g' in parts or 'kg' in parts):
        try:
            # 4. Spróbuj przekształcić drugi element (lub ten, który jest masą) na float.
            # Musimy znaleźć element, który jest masą. W tym formacie to prawdopodobnie trzeci element
            # po "WTST" i fladze (+/-). Spróbujmy znaleźć wartość, która jest liczbą:
            for part in parts:
                try:
                    weight_value = float(part)
                    return weight_value
                except ValueError:
                    continue # To nie była liczba, idziemy dalej
        except Exception as e:
            print(f"Błąd parsowania: {e} dla linii: {raw_line}")
            return None # W przypadku błędu zwracamy None
            
    return None # Zwróć None, jeśli format się nie zgadza        


def send_command(ser_connection, command_string):
    """Wysyła komendę do wagi przez port szeregowy."""
    # Polecenie musi być zakodowane na bajty (bytes) przed wysłaniem!
    # Używamy .encode('ascii') dla komend szeregowych
    command_bytes = command_string.encode('ascii')
    
    # Wysyłanie
    ser_connection.write(command_bytes)
    print(f"\n--- Wysłano komendę: {repr(command_string)} ---")
    
# Funkcja tarująca (zerująca)
def tare_scale(ser_connection):
    """Wysyła typową komendę Tarowania (np. 'T' z końcem linii)."""
    # Zastąp 'T\r\n' poprawnym poleceniem z manuala BS600M
    TARE_COMMAND = "T\r\n" 
    send_command(ser_connection, TARE_COMMAND)

try:
    # Inicjalizacja połączenia szeregowego
    # Timeout=1 oznacza, że skrypt poczeka sekundę na dane, zanim przejdzie dalej
    ser = serial.Serial(PORT_SCALE, BAUD_RATE, timeout=1) 
    print(f"Pomyślnie połączono z wagą przez port {PORT_SCALE} przy {BAUD_RATE} bps.")
    time.sleep(2) # Czekamy, aż port się ustabilizuje

    print("\n--- Rozpoczynanie nasłuchiwania danych bezpośrednio z wagi ---\n")

    
    plt.ion() 
    fig, ax = plt.subplots()
    x_data, y_data = [], []
    line, = ax.plot(x_data, y_data) # Pobieramy referencję do obiektu linii
    
    dt = 0
    while True:
        start = time.time()
        # Odczyt linii danych (aż do znaku końca linii \n),
        # dekodowanie na tekst i usunięcie białych znaków (m.in. \r)
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8').strip()
            
            # Wypisanie odebranego sygnału
            print(f"Surowy pakiet z wagi: {raw_line}")
            
            # Możesz tutaj dodać kod do parsowania (wyciągania) wartości masy,
            # tak jak robiliśmy to na Arduino
            

            # Generowanie nowych danych
            x_data.append(dt)
            weight = parse_weight(raw_line)
            print(weight)
            y_data.append(weight)

            # Wystarczy zaktualizować dane istniejącej linii!
            line.set_xdata(x_data)
            line.set_ydata(y_data)

            # Automatycznie dostosowujemy osie do nowych danych
            ax.relim()
            ax.autoscale_view()

            # Rysujemy nową klatkę i wymuszamy odświeżenie
            fig.canvas.draw()
            fig.canvas.flush_events() 
            end = time.time()
             
            dt += 1/BAUD_RATE+end-start
            time.sleep(1/BAUD_RATE+end-start)
            

            
except serial.SerialException as e:
    print(f"Błąd połączenia szeregowego: {e}")
    print("Sprawdź numer portu, baud rate oraz czy konwerter jest poprawnie podłączony i ma sterowniki.")

except KeyboardInterrupt:
    print("\nZatrzymanie skryptu przez użytkownika.")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        plt.ioff()
        print("Połączenie szeregowe zostało zamknięte.")
        

    
