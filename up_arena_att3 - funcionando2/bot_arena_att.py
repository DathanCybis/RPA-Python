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
    if not nome.endswith('.png'): nome += '.png'
    return os.path.join(PASTA_DO_SCRIPT, nome)

# ==========================================================
#        CONFIGURAÇÕES DE SELEÇÃO E NAVEGAÇÃO
# ==========================================================
ARENA_INICIAL = 3      
ARENA_FINAL   = 5     
ORDEM_CRESCENTE = False 
PASSO_INICIAL = 10    

NOME_JANELA = "CABAL"
ABA_COMBATE, ABA_MOVIMENTO, ABA_BUFFS = "f2", "f3", "f3"
ABA_BM = "f4" # Nova aba configurada por você

# Teclas
SELECT_MOB_KEY, LOOT_KEY = "z", "space"
BM_KEY, AURA_KEY = "5", "6"
BUFF_KEYS = ["3", "4"]        # No F3
DEBUFF_KEYS = ["7", "8", "9"] # No F3
NORMAL_SKILLS = ["1", "2", "3", "4"] # No F2
BM_SKILLS = ["7", "8"] # No F4
DASH_1, DASH_2 = "1", "2"
SMALL_HEAL_KEY, BIG_HEAL_KEY = "0", "9"
ZOOM_OUT_KEY = "-"

# Timings e Coordenadas do Boss
AURA_TRIGGER_TIME = 85.0 
HP_BAR_START, HP_BAR_END, HP_BAR_Y = 82, 276, 49 # HP Personagem
# Coordenadas do Portal e Desativar BM
PORTAL_DASH_COORD = (1662, 529)   
PORTAL_INTERAGIR = (1228, 603)    
COORD_DESATIVAR_BM = (252, 139) 

ARENAS_DISPONIVEIS = {
    1: (774, 270), 2: (765, 299), 3: (765, 322),
    4: (772, 345), 5: (769, 371), 6: (771, 396), 7: (768, 425)
}

ROTA_DETALHADA = {
    "arena_passo1": ((483, 124), [1]), "arena_passo2": ((10, 622), [1]),
    "arena_passo3": ((409, 30), [1, 2, 1]), "arena_passo4": ((10, 923), [1, 2]),
    "arena_passo5": ((1485, 962), [1]), "arena_passo6": ((10, 906), [1, 2, 1]),
    "arena_passo7": ((1412, 847), [1]), "arena_passo8": ((10, 767), [1, 2]),
    "arena_passo9_portao": ((10, 942), [2]), "arena_passo10": ((972, 897), [1]),
    "arena_passo11": ((461, 955), [2, 1, 2, 1, 2, 1])
}

rodando = False
modo_critico = False
bm_ativa_no_boss = False
aura_ativa = False
inicio_bm = 0
ultima_small_heal = ultima_big_heal = 0

# --- FUNÇÕES DE SISTEMA ---

def calibrar_zoom():
    print("[SISTEMA] Ajustando zoom...")
    keyboard.press(ZOOM_OUT_KEY); time.sleep(3.0); keyboard.release(ZOOM_OUT_KEY)

def verificar_imagem(img, conf=0.85):
    try: return pyautogui.locateOnScreen(caminho_img(img), confidence=conf) is not None
    except: return False

def clicar_no_botao(img, timeout=7):
    inicio = time.time()
    while time.time() - inicio < timeout:
        if not rodando: return False
        try:
            pos = pyautogui.locateCenterOnScreen(caminho_img(img), confidence=0.85)
            if pos:
                time.sleep(1.0); pyautogui.click(pos); time.sleep(1.5); return True
        except: pass
        time.sleep(0.5)
    return False

def boss_selecionado():
    """Identifica o ícone do boss para travar o combate e parar o 'Z'"""
    return verificar_imagem('icone_boss', conf=0.80)

def executar_buffs_pre_entrada():
    print("[SISTEMA] Aplicando Buffs Iniciais (F3)...")
    keyboard.press_and_release(ABA_BUFFS); time.sleep(0.3)
    for b in BUFF_KEYS:
        keyboard.press_and_release(b); time.sleep(1.2)
    keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)

# --- SISTEMA DE COMBATE HÍBRIDO ---

def combate_estavel(permitir_z=True):
    global bm_ativa_no_boss, aura_ativa, inicio_bm
    if modo_critico: return
    
    agora = time.time()

    if boss_selecionado():
        # --- MODO BOSS: 'Z' BLOQUEADO ---
        if not bm_ativa_no_boss:
            print("[BOSS] Alvo Identificado! Iniciando Debuffs e BM...")
            # 1. Debuffs no F3
            keyboard.press_and_release(ABA_BUFFS); time.sleep(0.2)
            for d in DEBUFF_KEYS:
                keyboard.press_and_release(d); time.sleep(0.4)
            
            # 2. Ativar BM e mudar para F4
            keyboard.press_and_release("esc"); time.sleep(0.1)
            for _ in range(8): keyboard.press_and_release(BM_KEY); time.sleep(0.1)
            keyboard.press_and_release(ABA_BM); time.sleep(0.2)
            
            bm_ativa_no_boss = True
            inicio_bm = agora
            aura_ativa = False

        # 3. Gerenciamento de Aura
        if bm_ativa_no_boss and not aura_ativa:
            if (agora - inicio_bm) >= AURA_TRIGGER_TIME:
                print("[COMBO] Hora da Aura!")
                keyboard.press_and_release(AURA_KEY)
                aura_ativa = True
        
        # 4. Skills de BM (Aba F4)
        for sk in BM_SKILLS:
            if not rodando: break
            keyboard.press_and_release(sk); time.sleep(0.1)
    else:
        # --- MODO NORMAL ---
        if bm_ativa_no_boss:
            # Boss morreu ou sumiu: volta para F2
            keyboard.press_and_release(ABA_COMBATE); time.sleep(0.2)
            bm_ativa_no_boss = False

        if permitir_z: 
            keyboard.press_and_release(SELECT_MOB_KEY)
        
        for sk in NORMAL_SKILLS:
            if not rodando: break
            keyboard.press_and_release(sk); time.sleep(0.4)

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
                if hp < 40 and (agora - ultima_big_heal) >= 70:
                    modo_critico = True; keyboard.press_and_release("esc")
                    for _ in range(3): keyboard.press_and_release("9"); time.sleep(0.08)
                    ultima_big_heal = agora; modo_critico = False
                elif hp < 75 and (agora - ultima_small_heal) >= 3:
                    modo_critico = True; keyboard.press_and_release("esc")
                    for _ in range(3): keyboard.press_and_release("0"); time.sleep(0.08)
                    ultima_small_heal = agora; modo_critico = False
            except: pass
        time.sleep(0.2)

# --- CICLO DA ARENA ---

def ciclo_arena(num):
    global PASSO_INICIAL, bm_ativa_no_boss, aura_ativa
    bm_ativa_no_boss = False
    aura_ativa = False
    
    print(f"\n[INFO] Iniciando Arena {num} no Passo {PASSO_INICIAL}...")
    calibrar_zoom()

    if PASSO_INICIAL == 1:
        executar_buffs_pre_entrada()
        pyautogui.click(PORTAL_DASH_COORD, button='right')
        time.sleep(0.3); keyboard.press_and_release(DASH_1); time.sleep(1.2)

        menu_aberto = False
        tentativas = 0
        while not menu_aberto and tentativas < 10:
            if not rodando: return False
            pyautogui.click(PORTAL_INTERAGIR); time.sleep(0.8)
            if verificar_imagem('botao_entrar'):
                menu_aberto = True
            tentativas += 1

        keyboard.press_and_release(ABA_COMBATE); time.sleep(0.5)
        pyautogui.click(ARENAS_DISPONIVEIS[num]); time.sleep(1.5)
        
        if verificar_imagem('indisponivel', conf=0.7):
            print(f"[AVISO] Arena ocupada."); keyboard.press_and_release("esc")
            return "PROXIMA_ARENA"
        
        if not clicar_no_botao('botao_entrar') or not clicar_no_botao('botao_confirmar'): return True
        time.sleep(4); calibrar_zoom()

    # Navegação até o Portão
    for i in range(PASSO_INICIAL, 9):    
        p = f"arena_passo{i}"; keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)
    
    # Destruição do Portão
    if PASSO_INICIAL <= 9:
        keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA["arena_passo9_portao"][0], button='right')
        keyboard.press_and_release(DASH_2); time.sleep(1.5)
        keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
        while rodando:
            combate_estavel(permitir_z=True)
            if not verificar_imagem('arena_portao'): break
            time.sleep(0.1)

    # Caminho Final e Boss
    for i in [10, 11]:
        if i >= PASSO_INICIAL:
            p = f"arena_passo{i}"; keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
            pyautogui.click(ROTA_DETALHADA[p][0], button='right')
            for d in ROTA_DETALHADA[p][1]: keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)

    print("[BOSS] Iniciando protocolo de combate...")
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
    while not verificar_imagem('botao_ok') and rodando:
        combate_estavel(permitir_z=True) 
        keyboard.press_and_release(LOOT_KEY)

    print("[LOOT] Coleta Intensiva (30 cliques)...")
    for _ in range(30): 
        if not rodando: break
        keyboard.press_and_release(LOOT_KEY); time.sleep(0.12)

    clicar_no_botao('botao_ok')
    clicar_no_botao('botao_sair')
    
    time.sleep(5); pyautogui.click(COORD_DESATIVAR_BM, button='right'); time.sleep(2)
    return True

# --- FLUXO PRINCIPAL ---
def fluxo_principal():
    global rodando, PASSO_INICIAL
    while rodando:
        calibrar_zoom()
        lista = list(range(ARENA_INICIAL, ARENA_FINAL + 1))
        if not ORDEM_CRESCENTE: lista.reverse()
        for n in lista:
            if not rodando: break
            if n not in ARENAS_DISPONIVEIS: continue
            while rodando:
                res = ciclo_arena(n)
                if res in [True, "PROXIMA_ARENA"]:
                    PASSO_INICIAL = 1 
                    break
        time.sleep(2)

def iniciar():
    global rodando
    if not rodando:
        rodando = True; print(f"[ON] BOT INTEGRADO ATIVO (Passo: {PASSO_INICIAL})")
        threading.Thread(target=thread_cura, daemon=True).start()
        threading.Thread(target=fluxo_principal, daemon=True).start()

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', lambda: exec("global rodando; rodando=False"))
print("F7: Iniciar | F8: Parar")
keyboard.wait()
