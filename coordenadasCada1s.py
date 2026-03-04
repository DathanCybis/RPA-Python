import pyautogui
import time
import os
import ctypes

# ===== AJUSTE DE PRECISÃO DO MOUSE (DPI AWARE) =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

def monitor_coordenadas_continuo():
    print("--- MONITOR DE COORDENADAS (HISTÓRICO ATIVO) ---")
    print("O terminal irá registrar cada posição em uma nova linha.")
    print("Pressione CTRL+C para encerrar e copiar os dados.\n")
    print("Contagem |   X   |   Y   | Cor RGB")
    print("-" * 40)
    
    contador = 1
    try:
        while True:
            # Captura posição e cor
            x, y = pyautogui.position()
            
            try:
                # O pixel() ajuda a identificar se você está sobre o HP, SP ou Botões
                cor = pyautogui.pixel(x, y)
            except:
                cor = "Erro ao ler cor"

            # Imprime em uma nova linha a cada segundo
            print(f"Ponto {contador:03} | X: {x:>4} | Y: {y:>4} | Cor: {cor}")
            
            contador += 1
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n\n[OFF] Monitoramento encerrado. O histórico está acima.")

if __name__ == "__main__":
    monitor_coordenadas_continuo()
    