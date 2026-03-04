import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw
import os
import ctypes

# ===== CONFIGURAÇÃO DE USUÁRIO - INTERVALO DE ARENAS =====
ARENA_INICIO = 1  
ARENA_FIM = 7     
# =========================================================

# AJUSTE DE PRECISÃO DO MOUSE (DPI AWARE)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

def caminho_img(nome):
    if not nome.endswith('.png'):
        nome += '.png'
    return os.path.join(PASTA_DO_SCRIPT, nome)

# CONFIGURAÇÕES DE INTERFACE
NOME_JANELA = "CABAL"
ABA_COMBATE, ABA_MOVIMENTO = "f2", "f3"
SELECT_MOB_KEY, LOOT_KEY = "z", "space"
BM_KEY, AURA_KEY = "5", "6"
NORMAL_SKILLS = ["1", "2", "3", "4"]

# Estados
rodando = False
modo_critico = False

# --- FUNÇÕES DE VISÃO ROBUSTAS (MISSÕES OBRIGATÓRIAS) ---

def verificar_imagem(img, conf=0.50):
    try:
        return pyautogui.locateOnScreen(caminho_img(img), confidence=conf) is not None
    except: return False

def esperar_e_clicar(img, botao='left', conf=0.50, timeout=None, msg=""):
    """ Trava o bot até que a imagem apareça e seja clicada. """
    if msg: print(f"[BUSCANDO] {msg}...")
    inicio_busca = time.time()
    while rodando:
        try:
            pos = pyautogui.locateCenterOnScreen(caminho_img(img), confidence=conf)
            if pos:
                pyautogui.click(pos, button=botao)
                time.sleep(1.0)
                return True
        except: pass
        
        if timeout and (time.time() - inicio_busca > timeout):
            return False
        time.sleep(0.5)
    return False

# --- LÓGICA DE COMBATE ---

def usar_skills_normais():
    keyboard.press_and_release(SELECT_MOB_KEY)
    for sk in NORMAL_SKILLS:
        if not rodando: break
        keyboard.press_and_release(sk)
        time.sleep(0.35)

def usar_bm_boss():
    print("[BOSS] Ativando Battle Mode...")
    keyboard.press_and_release("esc"); time.sleep(0.1)
    for _ in range(6): 
        keyboard.press_and_release(BM_KEY)
        time.sleep(0.08)
    time.sleep(2.0)

# --- CICLO DA ARENA (PERSISTENTE) ---

def ciclo_arena(lvl):
    print(f"\n=== INICIANDO ARENA LVL {lvl} ===")
    
    # 1. Missão: Achar o Portal no cenário (0.50)
    esperar_e_clicar('portal', conf=0.50, msg="Portal no Lobby")

    # 2. Missão: Selecionar Arena no Menu (0.90)
    # Se em 5s não achar, assume que as entradas acabaram
    if not esperar_e_clicar(f'arena_lvl{lvl}', conf=0.90, timeout=5, msg=f"Texto Arena Lvl {lvl}"):
        print(f"[INFO] Entradas esgotadas para Arena {lvl}.")
        keyboard.press_and_release("esc") # Fecha o menu
        return "PROXIMA_ARENA"

    # 3. Missão: Entrar e Confirmar (0.50)
    esperar_e_clicar('botao_entrar', conf=0.50, msg="Botão Entrar")
    esperar_e_clicar('botao_confirmar', conf=0.50, msg="Botão Confirmar")
    
    print("[INFO] Carregando mapa... aguardando 15s.")
    time.sleep(15)

    # 4. Missão: Percurso de Dash (dash1 ao dash7)
    keyboard.press_and_release(ABA_MOVIMENTO)
    time.sleep(0.5)
    for i in range(1, 8):
        esperar_e_clicar(f'dash{i}', botao='right', conf=0.50, msg=f"Local do Dash {i}")
        time.sleep(1.0)

    # 5. Missão: Derrubar o Portão (Trava de HP)
    print("[PORTÃO] Atacando até quebrar...")
    keyboard.press_and_release(ABA_COMBATE)
    time.sleep(0.5)
    
    confirmacao_vazio = 0
    while rodando:
        keyboard.press_and_release(SELECT_MOB_KEY)
        # Se a imagem 'portao' (HP/Alvo) NÃO estiver na tela...
        if not verificar_imagem('portao', conf=0.80):
            confirmacao_vazio += 1
            if confirmacao_vazio >= 6: # Exige 6 verificações negativas
                print("[OK] Portão derrubado!")
                break
        else:
            confirmacao_vazio = 0
        
        usar_skills_normais()
        time.sleep(0.1)

    # 6. Missão: Farm de 6 Minutos (ou Warning)
    print("[FARM] Iniciando cronômetro de 6 minutos de mobs...")
    inicio_farm = time.time()
    while rodando and (time.time() - inicio_farm < 360):
        if verificar_imagem('warning', conf=0.50):
            print("[SISTEMA] Warning detectado! Encerrando farm cedo.")
            break
        usar_skills_normais()
        keyboard.press_and_release(LOOT_KEY)

    # 7. Missão: Dash Final (dash8 e dash9)
    keyboard.press_and_release(ABA_MOVIMENTO)
    for i in [8, 9]:
        esperar_e_clicar(f'dash{i}', botao='right', conf=0.50, msg=f"Local do Dash {i}")
        time.sleep(1.2)

    # 8. Missão: Eliminar Boss e Abrir Baú
    print("[BOSS] Atacando Boss final...")
    keyboard.press_and_release(ABA_COMBATE)
    usar_bm_boss()
    
    # Fica batendo até o 'botao_ok' (do baú) aparecer
    while rodando:
        if verificar_imagem('botao_ok', conf=0.50):
            print("[OK] Recompensa detectada.")
            break
        usar_skills_normais()
        keyboard.press_and_release(LOOT_KEY)

    # 9. Missão: Sair
    print("[INFO] Coletando e Saindo...")
    for _ in range(15): 
        keyboard.press_and_release(LOOT_KEY)
        time.sleep(0.2)
        
    esperar_e_clicar('botao_ok', conf=0.50, msg="Botão OK da Vitória")
    esperar_e_clicar('botao_sair', conf=0.50, msg="Botão Sair da Arena")
    
    print("[INFO] Retornando ao lobby...")
    time.sleep(10)
    return True

# --- FLUXO PRINCIPAL ---

def fluxo_principal():
    global rodando
    while rodando:
        for n in range(ARENA_INICIO, ARENA_FIM + 1):
            if not rodando: break
            
            arena_ativa = True
            while arena_ativa and rodando:
                resultado = ciclo_arena(n)
                if resultado == "PROXIMA_ARENA":
                    arena_ativa = False
        
        print("[SISTEMA] Ciclo de arenas completo. Reiniciando...")
        time.sleep(5)

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        print(f"[BOT ON] Monitorando Arenas {ARENA_INICIO} a {ARENA_FIM}")
        threading.Thread(target=fluxo_principal, daemon=True).start()

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', lambda: exec("global rodando; rodando=False"))

print(f"=== CABAL PERSISTENT BOT (Arenas {ARENA_INICIO}-{ARENA_FIM}) ===")
print("F7: Iniciar | F8: Parar")
keyboard.wait()
