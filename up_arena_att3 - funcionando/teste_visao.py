import pyautogui
import os
import time
import ctypes
# Força o Windows a não aplicar nenhuma correção de escala no script
ctypes.windll.user32.SetProcessDPIAware()

# Força o Python a olhar para a pasta onde este script está
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

def testar_visao(nome_imagem):
    # Constrói o caminho completo
    caminho = os.path.join(PASTA_DO_SCRIPT, f"{nome_imagem}.png")
    
    print(f"--- DIAGNÓSTICO ---")
    print(f"Buscando arquivo em: {caminho}")
    
    # Verifica se o arquivo existe fisicamente na pasta
    if not os.path.exists(caminho):
        print(f"ERRO: O arquivo '{nome_imagem}.png' NÃO foi encontrado na pasta!")
        return

    print("Arquivo encontrado! Agora procurando na tela do jogo...")
    print("Você tem 5 segundos para dar ALT+TAB para o jogo.")
    time.sleep(5)

    try:
        # Procura a imagem na tela
        posicao = pyautogui.locateOnScreen(caminho, confidence=0.9)
        
        if posicao:
            print(f"SUCESSO! Encontrado na coordenada: {posicao}")
            centro = pyautogui.center(posicao)
            # Move o mouse para provar que achou
            pyautogui.moveTo(centro, duration=1.5)
            print("O mouse se moveu para o botão?")
        else:
            print("FALHA: A imagem existe na pasta, mas não aparece na tela do jogo.")
            print("Dica: Verifique se o jogo está em modo janela e sem nada na frente.")
            
    except Exception as e:
        print(f"ERRO TÉCNICO DURANTE A BUSCA: {e}")

# EXECUTA O TESTE
testar_visao("botao_entrar")
