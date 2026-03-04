import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw
import os
import ctypes

# ===== AJUSTE DE PRECISÃO DO MOUSE (DPI AWARE) =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

# ===== LOGICA DE CAMINHO DE ARQUIVOS =====
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

def caminho_img(nome):
    if not nome.endswith('.png'):
        nome += '.png'
    return os.path.join(PASTA_DO_SCRIPT, nome)

# ===== CONFIGURAÇÕES DE INTERFACE =====
NOME_JANELA = "CABAL"
ABA_COMBATE, ABA_MOVIMENTO = "f2", "f3"
HP_BAR_START, HP_BAR_END, HP_BAR_Y = 82, 276, 49
SP_BOLINHA_X, SP_BOLINHA_Y = 204, 85
SP_COR_RGB = (255, 181, 98)

# Teclas
SELECT_MOB_KEY, LOOT_KEY = "z", "space"
BM_KEY, AURA_KEY = "5", "6"
NORMAL_SKILLS, BM_SKILLS = ["1", "2", "3", "4"], ["7", "8"]
DASH_1, DASH_2 = "1", "2"
SMALL_HEAL_KEY, BIG_HEAL_KEY = "0", "9"
ZOOM_OUT_KEY = "-"

# Timings (RESTAURADOS)
BM_DURATION_TOTAL, BM_CAST_TIME, BM_COOLDOWN = 89.0, 2.0, 35.0
AURA_TRIGGER_BEFORE, AURA_EXTEND_VAL = 5.0, 47.0
SMALL_HEAL_CD, BIG_HEAL_CD = 3.0, 70.0

# Coordenadas do Portal e Interação
PORTAL_DASH_COORD = (1662, 529)   # Para o dash inicial
PORTAL_INTERAGIR = (1228, 603)    # Região de insistência

# Arenas 1 a 7
ARENAS = {
    1: (774, 270), 2: (765, 299), 3: (765, 322),
    4: (772, 345), 5: (769, 371), 6: (771, 396), 7: (768, 425)
}

ROTA_DETALHADA = {
    "arena_passo1": ((483, 124), [1]),
    "arena_passo2": ((10, 622), [1]),
    "arena_passo3": ((409, 30), [1, 2, 1]),
    "arena_passo4": ((10, 923), [1, 2]),
    "arena_passo5": ((1485, 962), [1]),
    "arena_passo6": ((10, 906), [1, 2, 1]),
    "arena_passo7": ((1412, 847), [1]),
    "arena_passo8": ((10, 767), [1, 2]),
    "arena_passo9_portao": ((10, 942), [2]),
    "arena_passo10": ((972, 897), [1]),                 # "arena_passo10": ((976, 1008), [1]),   - original
    "arena_passo11": ((461, 955), [2, 1, 2, 1, 2, 1])
}

# Estados (RESTAURADOS)
rodando = False
modo_critico = False
bm_ativa = False
aura_ativa = False
inicio_bm = fim_cooldown_bm = ultima_small_heal = ultima_big_heal = 0
tempo_liberacao_bm = 0 

# --- FUNÇÕES AUXILIARES ---

def calibrar_zoom():
    print("[SISTEMA] Calibrando zoom (5s)...")
    keyboard.press(ZOOM_OUT_KEY)
    time.sleep(5.0)
    keyboard.release(ZOOM_OUT_KEY)

def verificar_imagem(img, conf=0.85):
    try:
        return pyautogui.locateOnScreen(caminho_img(img), confidence=conf) is not None
    except: return False

def clicar_no_botao(img, timeout=7):
    inicio = time.time()
    while time.time() - inicio < timeout:
        if not rodando: return False
        try:
            pos = pyautogui.locateCenterOnScreen(caminho_img(img), confidence=0.85)
            if pos:
                time.sleep(1.0)
                pyautogui.click(pos)
                time.sleep(1.5)
                return True
        except: pass
        time.sleep(0.5)
    return False

# --- SISTEMAS DE SUPORTE ---

def thread_cura():
    global modo_critico, ultima_big_heal, ultima_small_heal
    while rodando:
        if gw.getActiveWindow() and NOME_JANELA.lower() in gw.getActiveWindow().title.lower():
            agora = time.time()
            try:
                largura = HP_BAR_END - HP_BAR_START
                screenshot = pyautogui.screenshot(region=(HP_BAR_START, HP_BAR_Y, largura, 1))
                pixels_vida = sum(1 for x in range(largura) if screenshot.getpixel((x, 0))[0] > 160)
                hp = (pixels_vida / largura) * 100
            except: hp = 100

            if hp < 40 and (agora - ultima_big_heal) >= BIG_HEAL_CD:
                modo_critico = True
                keyboard.press_and_release("esc")
                for _ in range(3): keyboard.press_and_release(BIG_HEAL_KEY); time.sleep(0.08)
                ultima_big_heal = agora
                modo_critico = False
            elif hp < 75 and (agora - ultima_small_heal) >= SMALL_HEAL_CD:
                modo_critico = True
                keyboard.press_and_release("esc")
                for _ in range(3): keyboard.press_and_release(SMALL_HEAL_KEY); time.sleep(0.08)
                ultima_small_heal = agora
                modo_critico = False
        time.sleep(0.2)

def gerenciar_combate():
    global bm_ativa, aura_ativa, inicio_bm, fim_cooldown_bm, tempo_liberacao_bm
    if modo_critico: return
    agora = time.time()
    
    if bm_ativa:
        tempo = agora - inicio_bm
        # Lógica de Aura para estender BM
        if not aura_ativa and tempo >= (BM_DURATION_TOTAL - AURA_TRIGGER_BEFORE):
            try:
                r, g, b = pyautogui.pixel(SP_BOLINHA_X, SP_BOLINHA_Y)
                if abs(r - SP_COR_RGB[0]) < 15:
                    keyboard.press_and_release("esc"); time.sleep(0.1)
                    for _ in range(3): keyboard.press_and_release(AURA_KEY); time.sleep(0.08)
                    aura_ativa = True
                    inicio_bm = agora - (BM_DURATION_TOTAL - AURA_EXTEND_VAL)
            except: pass
            
        if tempo >= BM_DURATION_TOTAL:
            bm_ativa, aura_ativa = False, False
            fim_cooldown_bm = agora + BM_COOLDOWN
            return
            
        keyboard.press_and_release(SELECT_MOB_KEY)
        for s in BM_SKILLS: keyboard.press_and_release(s); time.sleep(0.1)
    else:
        try:
            r, g, b = pyautogui.pixel(SP_BOLINHA_X, SP_BOLINHA_Y)
            pode_bm = abs(r - SP_COR_RGB[0]) < 15
        except: pode_bm = False

        if pode_bm and agora >= fim_cooldown_bm and agora >= tempo_liberacao_bm:
            keyboard.press_and_release("esc"); time.sleep(0.1)
            for _ in range(6): keyboard.press_and_release(BM_KEY); time.sleep(0.08)
            inicio_bm, bm_ativa = time.time(), True
        else:
            keyboard.press_and_release(SELECT_MOB_KEY)
            for sk in NORMAL_SKILLS: keyboard.press_and_release(sk); time.sleep(0.3)

# --- CICLO DA ARENA ---

def ciclo_arena(num):
    global tempo_liberacao_bm
    print(f"\n[INFO] Preparando entrada para Arena {num}...")
    
    calibrar_zoom()

    # 1. Movimentação até o Portal
    print("[PORTAL] Dash para aproximação...")
    pyautogui.click(PORTAL_DASH_COORD, button='right')
    time.sleep(0.3)
    keyboard.press_and_release(DASH_1)
    time.sleep(1.2)

    # 2. Interação Resiliente
    menu_aberto = False
    tentativas = 0
    while not menu_aberto and tentativas < 10:
        if not rodando: return False
        pyautogui.click(PORTAL_INTERAGIR)
        time.sleep(0.8)
        if verificar_imagem('botao_entrar'):
            menu_aberto = True
            print("[OK] Menu detectado.")
        tentativas += 1

    tempo_liberacao_bm = 0 
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.5)
    
    # 3. Seleção e Entrada
    pyautogui.click(ARENAS[num])
    time.sleep(1.5)
    
    achou_entrar = False
    inicio_t = time.time()
    while time.time() - inicio_t < 5:
        if verificar_imagem('botao_entrar'):
            achou_entrar = True
            break
        if verificar_imagem('indisponivel', conf=0.7):
            keyboard.press_and_release("esc")
            return "PROXIMA_ARENA"
        time.sleep(0.5)
    
    if not achou_entrar: return "PROXIMA_ARENA"

    if not clicar_no_botao('botao_entrar'): return True
    if not clicar_no_botao('botao_confirmar'): return True
    
    print("Entrou! Aguardando Loading...")
    time.sleep(6)       # time.sleep(15)

    calibrar_zoom()

    # Navegação 1-8
    for i in range(1, 9):    
        p = f"arena_passo{i}"
        keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            if not rodando: break
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)
            if verificar_imagem(p): break

    # Passo 9: Portão
    print("[PORTÃO] Iniciando destruição...")
    keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
    pyautogui.click(ROTA_DETALHADA["arena_passo9_portao"][0], button='right')
    keyboard.press_and_release(DASH_2); time.sleep(1.5)
    
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
    
    confirmacao_destruido = 0
    while rodando:
        keyboard.press_and_release(SELECT_MOB_KEY)
        if not verificar_imagem('arena_portao', conf=0.8):
            confirmacao_destruido += 1
        else:
            confirmacao_destruido = 0 
        
        if confirmacao_destruido >= 5:
            print("[PORTÃO] Destruição confirmada!")
            tempo_liberacao_bm = time.time() + 120
            print("[INFO] BM bloqueada por 2 min.")
            break
            
        gerenciar_combate()
        time.sleep(0.2)

    # Passos 10-11
    for i in [10, 11]:
        p = f"arena_passo{i}"
        keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)

    # Boss Final
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
    while not verificar_imagem('botao_ok') and rodando:
        gerenciar_combate()
        keyboard.press_and_release(LOOT_KEY)

    # Sair
    for _ in range(10): keyboard.press_and_release(LOOT_KEY); time.sleep(0.2)
    clicar_no_botao('botao_ok')
    clicar_no_botao('botao_sair')
    time.sleep(10)
    return True

# --- FLUXO PRINCIPAL ---

def fluxo_principal():
    global rodando
    while rodando:
        calibrar_zoom()
        for n in sorted(ARENAS.keys()):
            if not rodando: break
            arena_ativa = True
            while arena_ativa and rodando:
                resultado = ciclo_arena(n)
                if resultado == "PROXIMA_ARENA":
                    arena_ativa = False
        
        print("[SISTEMA] Ciclo concluído. Parando bot.")
        rodando = False

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        print("[ON] BOT INICIADO")
        threading.Thread(target=thread_cura, daemon=True).start()
        threading.Thread(target=fluxo_principal, daemon=True).start()

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', lambda: exec("global rodando; rodando=False"))
print("F7: Iniciar | F8: Parar")
keyboard.wait()
