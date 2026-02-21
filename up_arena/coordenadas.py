import pyautogui
import keyboard
import time

def mostrar_posicao():
    # Pega a posição atual do mouse
    x, y = pyautogui.position()
    
    # Pega a cor do pixel sob o mouse (útil para SP/HP)
    cor = pyautogui.pixel(x, y)
    
    print(f"Coordenada: ({x}, {y}) | Cor RGB: {cor}")
    print(f"Copie assim: {x}, {y}")
    print("-" * 30)

print("--- LOCALIZADOR DE COORDENADAS ---")
print("1. Coloque o mouse sobre o botão ou local desejado.")
print("2. Pressione 'ESPACÃO' para capturar a coordenada.")
print("3. Pressione 'ESC' para fechar este localizador.")
print("-" * 30)

# Loop para ficar capturando
while True:
    if keyboard.is_pressed('home'):
        mostrar_posicao()
        time.sleep(0.3) # Evita múltiplos prints com um só toque
        
    if keyboard.is_pressed('esc'):
        print("Localizador encerrado.")
        break






