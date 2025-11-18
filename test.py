import matplotlib.pyplot as plt
import time
import numpy as np

# Włącz tryb interaktywny: pozwala na ciągłe odświeżanie
plt.ion() 
fig, ax = plt.subplots()
x_data, y_data = [], []
line, = ax.plot(x_data, y_data) # Pobieramy referencję do obiektu linii

# Pętla symulująca napływ danych
for i in range(1, 100):
    # Generowanie nowych danych
    x_data.append(i)
    y_data.append(np.sin(i / 10.0))

    # Wystarczy zaktualizować dane istniejącej linii!
    line.set_xdata(x_data)
    line.set_ydata(y_data)

    # Automatycznie dostosowujemy osie do nowych danych
    ax.relim()
    ax.autoscale_view()

    # Rysujemy nową klatkę i wymuszamy odświeżenie
    fig.canvas.draw()
    fig.canvas.flush_events() 
    
    time.sleep(0.05) # Krótka pauza (50 ms)
    
plt.ioff()
# plt.show() # Opcjonalnie, by okno zostało otwarte po zakończeniu pętli