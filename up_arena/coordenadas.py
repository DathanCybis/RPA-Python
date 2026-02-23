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
print("2. Pressione 'HOME' para capturar a coordenada.")
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

# passo 1 = 483, 124 - dash1
# passo 2 = 0, 622   - dash1
# passo 3 = 409, 30  - dash1, 2, 1
# passo 4 = 0, 923   - dash1, 2
# passo 5 = 1485, 962 - dash1
# passo 6 = 0, 906    - dash1, 2, 1
# passo 7 = 1412, 847 - dash1
# passo 8 = 0, 767 - dash1, 2
# passo 9 = 0, 942 - dash2 (depois de qbrar o portão) portão
# passo 10 = 976, 1008 - dash1
# passo 11 = 461, 955 - dash2, 1, 2, 1, 2, 1
