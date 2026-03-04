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
#        CONFIGURAÇÕES DE SELEÇÃO DE ARENAS
# ==========================================================
ARENA_INICIAL = 2      # De qual arena começar
ARENA_FINAL   = 3      # Em qual arena terminar
ORDEM_CRESCENTE = True # True para (1,2,3) | False para (3,2,1)
# ==========================================================

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

# Timings
BM_DURATION_TOTAL, BM_COOLDOWN = 89.0, 35.0
AURA_TRIGGER_BEFORE, AURA_EXTEND_VAL = 5.0, 47.0
SMALL_HEAL_CD, BIG_HEAL_CD = 3.0, 70.0

# Coordenadas
PORTAL_DASH_COORD = (1662, 529)   
PORTAL_INTERAGIR = (1228, 603)    
COORD_DESATIVAR_BM = (252, 139) 

# Todas as arenas mapeadas (O bot vai filtrar estas automaticamente)
ARENAS_DISPONIVEIS = {
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
    "arena_passo10": ((972, 897), [1]),
    "arena_passo11": ((461, 955), [2, 1, 2, 1, 2, 1])
}

rodando = False
modo_critico = False
bm_ativa = False
aura_ativa = False
inicio_bm = fim_cooldown_bm = ultima_small_heal = ultima_big_heal = 0

# --- FUNÇÕES DE SISTEMA ---

def calibrar_zoom():
    print("[SISTEMA] Calibrando zoom...")
    keyboard.press(ZOOM_OUT_KEY)
    time.sleep(3.0)
    keyboard.release(ZOOM_OUT_KEY)

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
                time.sleep(1.0); pyautogui.click(pos); time.sleep(1.5)
                return True
        except: pass
        time.sleep(0.5)
    return False

# --- SISTEMAS DE COMBATE ---

def combate_normal():
    if modo_critico: return
    keyboard.press_and_release(SELECT_MOB_KEY)
    for sk in NORMAL_SKILLS:
        if not rodando: break
        keyboard.press_and_release(sk); time.sleep(0.4)

def gerenciar_combate_full():
    global bm_ativa, aura_ativa, inicio_bm, fim_cooldown_bm
    if modo_critico: return
    agora = time.time()
    
    if bm_ativa:
        tempo = agora - inicio_bm
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

        if pode_bm and agora >= fim_cooldown_bm:
            print("[COMBATE] Ativando BM (2s)...")
            keyboard.press_and_release("esc"); time.sleep(0.1)
            fim_tentativa = time.time() + 2.0
            while time.time() < fim_tentativa:
                keyboard.press_and_release(BM_KEY); time.sleep(0.1)
            inicio_bm, bm_ativa = time.time(), True
        else:
            combate_normal()

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
                modo_critico = True; keyboard.press_and_release("esc")
                for _ in range(3): keyboard.press_and_release(BIG_HEAL_KEY); time.sleep(0.08)
                ultima_big_heal = agora; modo_critico = False
            elif hp < 75 and (agora - ultima_small_heal) >= SMALL_HEAL_CD:
                modo_critico = True; keyboard.press_and_release("esc")
                for _ in range(3): keyboard.press_and_release(SMALL_HEAL_KEY); time.sleep(0.08)
                ultima_small_heal = agora; modo_critico = False
        time.sleep(0.2)

# --- CICLO DA ARENA ---

def ciclo_arena(num):
    print(f"\n[INFO] Iniciando Arena {num}...")
    calibrar_zoom()

    pyautogui.click(PORTAL_DASH_COORD, button='right')
    time.sleep(0.3); keyboard.press_and_release(DASH_1); time.sleep(1.2)

    menu_aberto = False
    tentativas = 0
    while not menu_aberto and tentativas < 10:
        if not rodando: return False
        pyautogui.click(PORTAL_INTERAGIR); time.sleep(0.8)
        if verificar_imagem('botao_entrar'):
            menu_aberto = True; print("[OK] Menu detectado.")
        tentativas += 1

    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.5)
    pyautogui.click(ARENAS_DISPONIVEIS[num]); time.sleep(1.5)
    
    achou_entrar = False
    inicio_t = time.time()
    while time.time() - inicio_t < 5:
        if verificar_imagem('botao_entrar'):
            achou_entrar = True; break
        if verificar_imagem('indisponivel', conf=0.7):
            print(f"[AVISO] Arena {num} ocupada."); keyboard.press_and_release("esc")
            return "PROXIMA_ARENA"
        time.sleep(0.5)
    
    if not achou_entrar: return "PROXIMA_ARENA"
    if not clicar_no_botao('botao_entrar'): return True
    if not clicar_no_botao('botao_confirmar'): return True
    
    print("Entrou! Aguardando Loading...")
    time.sleep(4); calibrar_zoom()

    for i in range(1, 9):    
        p = f"arena_passo{i}"
        keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            if not rodando: break
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)
            if verificar_imagem(p): break

    print("[PORTÃO] Quebrando portão...")
    keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
    pyautogui.click(ROTA_DETALHADA["arena_passo9_portao"][0], button='right')
    keyboard.press_and_release(DASH_2); time.sleep(1.5)
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
    
    confirmacao_destruido = 0
    while rodando:
        combate_normal()
        if not verificar_imagem('arena_portao', conf=0.8): confirmacao_destruido += 1
        else: confirmacao_destruido = 0 
        if confirmacao_destruido >= 5: break
        time.sleep(0.1)

    for i in [10, 11]:
        p = f"arena_passo{i}"
        keyboard.press_and_release(ABA_MOVIMENTO); time.sleep(0.3)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.9)

    print("[BOSS] Combatendo...")
    keyboard.press_and_release(ABA_COMBATE); time.sleep(0.3)
    while not verificar_imagem('botao_ok') and rodando:
        gerenciar_combate_full(); keyboard.press_and_release(LOOT_KEY)

    for _ in range(10): keyboard.press_and_release(LOOT_KEY); time.sleep(0.2)
    clicar_no_botao('botao_ok'); clicar_no_botao('botao_sair')
    
    print("[SISTEMA] Resetando BM...")
    time.sleep(5); pyautogui.click(COORD_DESATIVAR_BM, button='right'); time.sleep(2)
    return True

# --- FLUXO PRINCIPAL COM LÓGICA DE ORDEM ---

def fluxo_principal():
    global rodando
    while rodando:
        calibrar_zoom()
        
        # Cria a lista baseada na sua configuração
        lista_arenas = list(range(ARENA_INICIAL, ARENA_FINAL + 1))
        
        # Se não for crescente, inverte a lista (ex: 3, 2, 1)
        if not ORDEM_CRESCENTE:
            lista_arenas.reverse()
            
        print(f"[SISTEMA] Sequência de arenas: {lista_arenas}")
        
        for n in lista_arenas:
            if not rodando: break
            if n not in ARENAS_DISPONIVEIS: continue # Pula se o número não existir no dicionário
            
            arena_ativa = True
            while arena_ativa and rodando:
                resultado = ciclo_arena(n)
                if resultado == True or resultado == "PROXIMA_ARENA":
                    arena_ativa = False
        
        print("[SISTEMA] Rodada finalizada. Reiniciando...")
        time.sleep(2)

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        print(f"[ON] BOT INICIADO (Arenas {ARENA_INICIAL} a {ARENA_FINAL})")
        threading.Thread(target=thread_cura, daemon=True).start()
        threading.Thread(target=fluxo_principal, daemon=True).start()

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', lambda: exec("global rodando; rodando=False"))
print("F7: Iniciar | F8: Parar")
keyboard.wait()
