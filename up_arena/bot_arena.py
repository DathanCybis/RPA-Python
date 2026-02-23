import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw

# ===== CONFIGURAÇÕES DE INTERFACE =====
NOME_JANELA = "CABAL"
ABA_COMBATE = "f2"
ABA_MOVIMENTO = "f3"

# Coordenadas Calibradas (HP e SP)
HP_BAR_START = 82
HP_BAR_END = 276
HP_BAR_Y = 49
SP_BOLINHA_X = 204   
SP_BOLINHA_Y = 85    
SP_COR_RGB = (255, 181, 98) 

# ===== TECLAS =====
SELECT_MOB_KEY = "z"
LOOT_KEY = "space"
BM_KEY = "5"            
AURA_KEY = "6"          
NORMAL_SKILLS = ["1", "2", "3", "4"]
BM_SKILLS = ["7", "8"]
DASH_1 = "1"
DASH_2 = "2"
SMALL_HEAL_KEY = "0"
BIG_HEAL_KEY = "9"

# Timings
BM_DURATION_TOTAL = 89        
BM_CAST_TIME = 2.0
BM_COOLDOWN = 35.0
AURA_TRIGGER_BEFORE = 5.0 
AURA_EXTEND_VAL = 47.0
SMALL_HEAL_CD = 3.0
BIG_HEAL_CD = 70.0

# ===== ARENAS E ROTAS (COORDENADAS FIXAS SÓ PARA AS ARENAS) =====
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
    "arena_passo10": ((976, 1008), [1]),
    "arena_passo11": ((461, 955), [2, 1, 2, 1, 2, 1])
}

# Estados
rodando = False
modo_critico = False
bm_ativa = False
aura_ativa = False
inicio_bm = 0
fim_cooldown_bm = 0
ultima_small_heal = 0
ultima_big_heal = 0

# --- FUNÇÕES DE VISÃO ---

def verificar_imagem(img, confidence=0.7):
    try:
        path = f"{img}.png"
        return pyautogui.locateOnScreen(path, confidence=confidence) is not None
    except: return False

def clicar_no_botao(img, timeout=10):
    """Varre a tela inteira atrás do botão e clica nele."""
    print(f"[VISÃO] Procurando botão: {img}...")
    inicio = time.time()
    while time.time() - inicio < timeout:
        if not rodando: return False
        try:
            pos = pyautogui.locateCenterOnScreen(f"{img}.png", confidence=0.7)
            if pos:
                pyautogui.click(pos)
                print(f"[OK] Botão {img} clicado!")
                return True
        except: pass
        time.sleep(0.5)
    print(f"[AVISO] Botão {img} não encontrado após {timeout}s.")
    return False

# --- FUNÇÕES DE AUXÍLIO ---

def janela_ativa():
    try:
        janela = gw.getActiveWindow()
        return janela is not None and NOME_JANELA.lower() in janela.title.lower()
    except: return False

def calcular_hp_percentual():
    try:
        largura = HP_BAR_END - HP_BAR_START
        screenshot = pyautogui.screenshot(region=(HP_BAR_START, HP_BAR_Y, largura, 1))
        pixels_vida = 0
        for x in range(largura):
            r, g, b = screenshot.getpixel((x, 0))
            if r > g + 25 and r > b + 25: pixels_vida += 1
        return (pixels_vida / largura) * 100
    except: return 100

def checar_sp():
    try:
        r, g, b = pyautogui.pixel(SP_BOLINHA_X, SP_BOLINHA_Y)
        return abs(r - SP_COR_RGB[0]) < 15 and abs(g - SP_COR_RGB[1]) < 15
    except: return False

def mudar_aba(aba):
    keyboard.press_and_release(aba)
    time.sleep(0.2)

def limpar_e_usar(tecla, delay=0.1, repete=3):
    keyboard.press_and_release("esc")
    time.sleep(0.12)
    for _ in range(repete):
        keyboard.press_and_release(tecla)
        time.sleep(0.08)
    time.sleep(delay)

# --- SISTEMAS DE COMBATE E CURA ---

def thread_cura():
    global modo_critico, ultima_big_heal, ultima_small_heal
    while rodando:
        if janela_ativa():
            agora = time.time()
            hp = calcular_hp_percentual()
            if hp < 40 and (agora - ultima_big_heal) >= BIG_HEAL_CD:
                modo_critico = True
                limpar_e_usar(BIG_HEAL_KEY, 0.2, 3)
                ultima_big_heal = agora
                modo_critico = False
            elif hp < 75 and (agora - ultima_small_heal) >= SMALL_HEAL_CD:
                modo_critico = True
                limpar_e_usar(SMALL_HEAL_KEY, 1.1, 3)
                ultima_small_heal = agora
                modo_critico = False
        time.sleep(0.2)

def gerenciar_combate():
    global bm_ativa, aura_ativa, inicio_bm, fim_cooldown_bm
    if modo_critico: return
    agora = time.time()
    
    if bm_ativa:
        tempo = agora - inicio_bm
        if not aura_ativa and tempo >= (BM_DURATION_TOTAL - AURA_TRIGGER_BEFORE):
            if checar_sp():
                limpar_e_usar(AURA_KEY, 1.0, 3)
                aura_ativa = True
                inicio_bm = agora - (BM_DURATION_TOTAL - AURA_EXTEND_VAL)
        if tempo >= BM_DURATION_TOTAL:
            bm_ativa = False
            aura_ativa = False
            fim_cooldown_bm = agora + BM_COOLDOWN
            return
        keyboard.press_and_release(SELECT_MOB_KEY)
        for s in BM_SKILLS: keyboard.press_and_release(s); time.sleep(0.1)
    elif checar_sp() and agora >= fim_cooldown_bm:
        limpar_e_usar(BM_KEY, BM_CAST_TIME, 6)
        inicio_bm = time.time()
        bm_ativa = True
    else:
        keyboard.press_and_release(SELECT_MOB_KEY)
        for sk in NORMAL_SKILLS: keyboard.press_and_release(sk); time.sleep(0.3)

# --- FLUXO DA ARENA ---

def ciclo_arena(num):
    mudar_aba(ABA_COMBATE)
    pyautogui.click(ARENAS[num])
    time.sleep(0.8)
    
    if verificar_imagem('indisponivel'): return False
    
    # BUSCA AUTOMÁTICA DOS BOTÕES NA TELA
    if not clicar_no_botao('botao_entrar'): return True
    if not clicar_no_botao('botao_confirmar'): return True
    
    print("Aguardando carregamento...")
    time.sleep(12)

    # Navegação 1-8
    for i in range(1, 9):
        p = f"arena_passo{i}"
        mudar_aba(ABA_MOVIMENTO)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            if not rodando: break
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.8)
            if verificar_imagem(p): break

    # Passo 9 (Portão)
    mudar_aba(ABA_COMBATE)
    while verificar_imagem('arena_portao'):
        gerenciar_combate()

    # Passos 10 e 11
    for i in [10, 11]:
        p = f"arena_passo{i}"
        mudar_aba(ABA_MOVIMENTO)
        pyautogui.click(ROTA_DETALHADA[p][0], button='right')
        for d in ROTA_DETALHADA[p][1]:
            if not rodando: break
            keyboard.press_and_release(DASH_1 if d == 1 else DASH_2); time.sleep(0.8)
            if verificar_imagem(p): break

    # Combate Boss até o botão OK aparecer
    mudar_aba(ABA_COMBATE)
    while not verificar_imagem('botao_ok'):
        if not rodando: break
        gerenciar_combate()
        keyboard.press_and_release(LOOT_KEY)

    # Coleta e Saída
    for _ in range(15): keyboard.press_and_release(LOOT_KEY); time.sleep(0.2)
    clicar_no_botao('botao_ok')
    time.sleep(1)
    clicar_no_botao('botao_sair')
    time.sleep(8)
    return True

# --- CONTROLE ---

def fluxo_principal():
    while rodando:
        for n in list(ARENAS.keys()):
            if not rodando: break
            ok = True
            while ok and rodando: ok = ciclo_arena(n)

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        print("[ON] BOT INICIADO")
        threading.Thread(target=thread_cura, daemon=True).start()
        threading.Thread(target=fluxo_principal, daemon=True).start()

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', lambda: exec("global rodando; rodando=False"))

print("Pressione F7 para iniciar o bot.")
print("Pressione F8 para parar o bot.")

keyboard.wait()
