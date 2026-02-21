import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw

# ===== CONFIGURAÇÕES GERAIS =====
NOME_DA_JANELA = "Cabal"

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
NORMAL_SKILLS = ["1", "2", "3", "4"]
BM_KEY = "5"            
AURA_KEY = "6"          
BM_SKILLS = ["7", "8"]
SMALL_HEAL_KEY = "0"
BIG_HEAL_KEY = "9"

# ===== TIMINGS =====
BM_DURATION_TOTAL = 89       
BM_CAST_TIME = 2.0
BM_COOLDOWN = 35.0

AURA_CAST_TIME = 1.0
AURA_EXTEND_VAL = 47.0 
AURA_TRIGGER_BEFORE = 5.0 

SMALL_HEAL_CAST = 1.1 
SMALL_HEAL_CD = 3.0
BIG_HEAL_CD = 70.0

# Variáveis de Estado
rodando = False
modo_critico = False
bm_ativa = False
aura_ativa = False
inicio_bm = 0
fim_cooldown_bm = 0
ultima_small_heal = 0
ultima_big_heal = 0

# --- FUNÇÕES DE AÇÃO ---

def limpar_e_usar(tecla, delay_pos=0.1, repetições=3):
    keyboard.press_and_release("esc")
    time.sleep(0.12)
    for _ in range(repetições):
        keyboard.press_and_release(tecla)
        time.sleep(0.08)
    time.sleep(delay_pos)

def janela_ativa():
    try:
        janela = gw.getActiveWindow()
        return janela is not None and NOME_DA_JANELA.lower() in janela.title.lower()
    except: return False

def calcular_hp_percentual():
    try:
        largura = HP_BAR_END - HP_BAR_START
        screenshot = pyautogui.screenshot(region=(HP_BAR_START, HP_BAR_Y, largura, 1))
        pixels_vida = 0
        for x in range(largura):
            r, g, b = screenshot.getpixel((x, 0))
            if r > g + 25 and r > b + 25: pixels_vida += 1
        return (pixels_vida / largura) * 100 if largura > 0 else 0
    except: return 100

def checar_sp_cor_pura():
    """Apenas checa a cor na coordenada, sem travas de estado."""
    try:
        r, g, b = pyautogui.pixel(SP_BOLINHA_X, SP_BOLINHA_Y)
        alvo_r, alvo_g, alvo_b = SP_COR_RGB
        return abs(r - alvo_r) < 15 and abs(g - alvo_g) < 15
    except: return False

def tem_sp_suficiente():
    # Trava para não tentar ativar BM se já estiver ativa ou em cooldown
    if bm_ativa or time.time() < fim_cooldown_bm: 
        return False
    return checar_sp_cor_pura()

# --- LOGICA DE COMBATE ---

def loop_ataque():
    global rodando, modo_critico, bm_ativa, inicio_bm, aura_ativa, fim_cooldown_bm
    while rodando:
        if janela_ativa():
            if modo_critico:
                time.sleep(0.1)
                continue

            agora = time.time()
            
            # 1. GERENCIAMENTO DE BM + AURA
            if bm_ativa:
                tempo_passado = agora - inicio_bm
                
                # Caso 1: Ativação da AURA (aos 84s) + CHECAGEM DE SP
                if not aura_ativa and tempo_passado >= (BM_DURATION_TOTAL - AURA_TRIGGER_BEFORE):
                    if checar_sp_cor_pura(): # Verifica se tem SP para a Aura
                        print("\n>>> SP DETECTADO! EXTENDENDO COM AURA (Spam)")
                        limpar_e_usar(AURA_KEY, AURA_CAST_TIME, repetições=3)
                        aura_ativa = True
                        inicio_bm = agora - (BM_DURATION_TOTAL - AURA_EXTEND_VAL)
                        continue
                    else:
                        # Avisa que está esperando SP para não deixar a BM acabar à toa
                        print("Aguardando SP para Aura...", end='\r')
                
                # Caso 2: Fim da BM
                if tempo_passado >= BM_DURATION_TOTAL:
                    print("\n>>> CICLO FINALIZADO. Voltando ao Normal.")
                    bm_ativa = False
                    aura_ativa = False
                    fim_cooldown_bm = agora + BM_COOLDOWN
                    continue

                # Ações em modo BM
                keyboard.press_and_release(SELECT_MOB_KEY)
                keyboard.press_and_release(LOOT_KEY)
                for skill in BM_SKILLS:
                    if modo_critico or not rodando: break
                    keyboard.press_and_release(skill)
                    time.sleep(0.2)
            
            # 2. ATIVAÇÃO DE BM
            elif tem_sp_suficiente():
                print("\n>>> SP DETECTADO. LANÇANDO BATTLE MODE.")
                limpar_e_usar(BM_KEY, BM_CAST_TIME, repetições=6)
                inicio_bm = time.time()
                bm_ativa = True
                aura_ativa = False
            
            # 3. ATAQUE NORMAL
            else:
                keyboard.press_and_release(SELECT_MOB_KEY)
                keyboard.press_and_release(LOOT_KEY)
                for sk in NORMAL_SKILLS:
                    if modo_critico or not rodando or tem_sp_suficiente(): break
                    keyboard.press_and_release(sk)
                    time.sleep(0.4)
        else:
            time.sleep(0.5)

def loop_bot():
    global rodando, modo_critico, ultima_big_heal, ultima_small_heal
    while rodando:
        if not janela_ativa():
            time.sleep(0.5)
            continue

        agora = time.time()
        hp = calcular_hp_percentual()
        
        # 1. CURA MAIOR (HP < 40%)
        if hp < 40 and (agora - ultima_big_heal) >= BIG_HEAL_CD:
            modo_critico = True
            print("\n>>> EMERGÊNCIA: CURA MAIOR (Spam)")
            limpar_e_usar(BIG_HEAL_KEY, 0.2, repetições=3)
            ultima_big_heal = agora
            modo_critico = False

        # 2. CURA MENOR (HP < 75%)
        elif hp < 75 and (agora - ultima_small_heal) >= SMALL_HEAL_CD:
            modo_critico = True
            print("\n>>> CONJURANDO CURA MENOR (Spam)")
            limpar_e_usar(SMALL_HEAL_KEY, SMALL_HEAL_CAST, repetições=3)
            ultima_small_heal = time.time()
            modo_critico = False

        time.sleep(0.1)

# --- CONTROLES ---

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        print("\n[ON] BOT INICIADO - F7")
        threading.Thread(target=loop_bot, daemon=True).start()
        threading.Thread(target=loop_ataque, daemon=True).start()

def parar():
    global rodando
    rodando = False
    print("\n[OFF] BOT PARADO - F8")

keyboard.add_hotkey('f7', iniciar)
keyboard.add_hotkey('f8', parar)

print("--- CABAL BOT MASTER (Versão Final Refinada) ---")
print("Ciclo: BM -> Checa SP para Aura aos 84s -> +47s de BM")
print("Pressione F7 para iniciar o bot.")
print("Pressione F8 para parar o bot.")

keyboard.wait()
