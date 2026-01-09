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




def send_command(ser_connection, command_string):
    """Wysyła komendę do wagi przez port szeregowy."""
    command_bytes = command_string.encode('ascii')
    ser_connection.write(command_bytes)
    print(f"\n--- Wysłano komendę: {repr(command_string)} ---")

def tare_scale(ser_connection):
    """Wysyła typową komendę Tarowania (np. 'T' z końcem linii)."""
    # Zastąp 'T\r\n' poprawnym poleceniem z manuala BS600M
    TARE_COMMAND = "T\r\n"
    send_command(ser_connection, TARE_COMMAND)

try:
    # Inicjalizacja połączenia szeregowego
    ser = serial.Serial(PORT_SCALE, BAUD_RATE, timeout=1)
    print(f"Połączono z {PORT_SCALE} przy {BAUD_RATE} baud")
    
    # Inicjalizacja wykresu
    plt.ion() 
    fig, ax = plt.subplots(figsize=(10, 6))
    x_data, y_data = [], []
    line, = ax.plot(x_data, y_data, 'b-', linewidth=2) 
    
    # Ustawienia osi
    ax.set_xlim(0, 30)
    ax.set_ylim(-0.1, 1.0)
    ax.set_xlabel("Czas [s]", fontsize=12)
    ax.set_ylabel("Masa [g]", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_title("Pomiar masy w czasie rzeczywistym", fontsize=14)
    
    start_time = time.time()
    last_draw_time = start_time
    DRAW_INTERVAL = 3  # Rysuj wykres co 100 ms
    
    print("Rozpoczynam odczyt danych...")
    print("Naciśnij Ctrl+C aby zatrzymać")

    while True:    
        current_time = time.time()
        
        # Sprawdź czy są dane do odczytu
        if ser.in_waiting > 0:
            try:
                # Odczytaj linię (zakładając, że waga wysyła dane zakończone znakiem nowej linii)
                raw_bytes = ser.readline()
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
        
        # Aktualizacja wykresu co określony interwał
        if current_time - last_draw_time > DRAW_INTERVAL:
            if len(x_data) > 0:
                # Aktualizacja danych na wykresie
                line.set_xdata(x_data)
                line.set_ydata(y_data)
                
                # Dynamiczne ustawienie zakresu osi X (ostatnie 30 sekund)
                if x_data[-1] > 30:
                    min_x = x_data[-1] - 30
                    ax.set_xlim(min_x, x_data[-1] + 0.5)
                else:
                    ax.set_xlim(0, 30)
                
                # Dynamiczne ustawienie zakresu osi Y z marginesem
                if len(y_data) > 0:
                    y_min = min(y_data) if min(y_data) < 0 else 0
                    y_max = max(y_data) if max(y_data) > 0 else 1.0
                    margin = (y_max - y_min) * 0.1
                    ax.set_ylim(y_min - margin, y_max + margin)
                
                # Rysowanie i odświeżanie
                fig.canvas.draw()
                fig.canvas.flush_events()
                
                last_draw_time = current_time
        
        # Krótka pauza aby nie przeciążyć CPU
        time.sleep(0.01)

except serial.SerialException as e:
    print(f"Błąd połączenia szeregowego: {e}")
    print("Sprawdź numer portu, baud rate oraz czy konwerter jest poprawnie podłączony i ma sterowniki.")

except KeyboardInterrupt:
    print("\nZatrzymanie skryptu przez użytkownika.")

except Exception as e:
    print(f"Nieoczekiwany błąd: {e}")

finally:
    # Zamknięcie połączenia i wykresu
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Połączenie szeregowe zostało zamknięte.")
    
    plt.ioff()
    
    # Zapisz dane do pliku przed zamknięciem
    if len(x_data) > 0:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"pomiary_wagi_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("Czas[s]\tMasa[g]\n")
            for x, y in zip(x_data, y_data):
                f.write(f"{x:.3f}\t{y:.3f}\n")
        print(f"Dane zapisane do {filename}")
    
    # Pokaż końcowy wykres
    if len(x_data) > 0:
        plt.show(block=True)