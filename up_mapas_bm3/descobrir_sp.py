import pyautogui
import time

print("Aponte o mouse para a BOLINHA DE SP e aguarde 5 segundos...")
time.sleep(5)
x, y = pyautogui.position()
pixel_color = pyautogui.pixel(x, y)
print(f"Coordenada: X={x}, Y={y}")
print(f"Cor (RGB): {pixel_color}")
