import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw

# ===== CONFIGURAÇÕES GERAIS =====
NOME_DA_JANELA = "CABAL"

# Coordenadas Calibradas (HP e SP)
HP_BAR_START = 82
HP_BAR_END = 276
HP_BAR_Y = 49

SP_BOLINHA_X = 204  # <--- Sua coordenada X calibrada
SP_BOLINHA_Y = 85   # <--- Sua coordenada Y calibrada
SP_COR_RGB = (255, 181, 98) # <--- Sua cor capturada

# ===== CONFIGURAÇÕES DE BM & AURA =====
BM_KEY = "-"
AURA_KEY = "="
BM_SKILLS = ["7", "8"]
SKILL_KEYS = ["z", "3", "4", "5", "6", "space"]

BM_DURATION = 89       
AURA_EXTEND_TIME = 5   
BM_COOLDOWN = 30

# ===== CURAS & TIMINGS =====
SMALL_HEAL_KEY = "0"
BIG_HEAL_KEY = "9"
SMALL_HEAL_COOLDOWN = 3
BIG_HEAL_COOLDOWN = 70
DELAY_SKILL = 0.2
DELAY_LOOP = 0.05

# Variáveis de Estado
rodando = False
modo_critico = False
bm_ativa = False
aura_ativa = False
inicio_bm = 0
ultima_small_heal = 0
ultima_big_heal = 0

# --- FUNÇÕES AUXILIARES ---

def janela_ativa():
    try:
        janela = gw.getActiveWindow()
        return janela is not None and NOME_DA_JANELA.lower() in janela.title.lower()
    except: return False

def calcular_hp_percentual():
    largura = HP_BAR_END - HP_BAR_START
    screenshot = pyautogui.screenshot(region=(HP_BAR_START, HP_BAR_Y, largura, 1))
    pixels_vida = 0
    for x in range(largura):
        r, g, b = screenshot.getpixel((x, 0))
        if r > g + 25 and r > b + 25: pixels_vida += 1
    return (pixels_vida / largura) * 100 if largura > 0 else 0

def tem_sp_suficiente():
    """Verifica se a bolinha de SP está na cor capturada (com margem de erro)."""
    try:
        # Pega a cor do pixel na coordenada exata
        r, g, b = pyautogui.pixel(SP_BOLINHA_X, SP_BOLINHA_Y)
        
        # Compara com a sua cor (255, 181, 98) permitindo variação de 20 tons
        alvo_r, alvo_g, alvo_b = SP_COR_RGB
        return abs(r - alvo_r) < 20 and abs(g - alvo_g) < 20
    except: return False

# --- LOGICA DE COMBATE ---

def loop_ataque():
    global rodando, modo_critico, bm_ativa, inicio_bm, aura_ativa
    while rodando:
        if janela_ativa() and not modo_critico:
            agora = time.time()
            
            # --- Gerenciamento de BM e Aura ---
            if bm_ativa:
                tempo_passado = agora - inicio_bm
                tempo_restante = BM_DURATION - tempo_passado

                # Lógica para usar AURA (Extensão)
                if not aura_ativa and tempo_restante <= AURA_EXTEND_TIME:
                    print("\n[!] ATIVANDO AURA (Reseting para +45s)")
                    keyboard.press_and_release(AURA_KEY)
                    aura_ativa = True
                    # Ajuste matemático: faz o bot acreditar que restam 45s
                    inicio_bm = time.time() - (BM_DURATION - 45) 
                    time.sleep(1.0) # Tempo de animação da Aura
                
                # Fim real da BM
                if tempo_passado >= BM_DURATION:
                    print("\n[.] BM Finalizada - Voltando rotação normal")
                    bm_ativa = False
                    aura_ativa = False

            elif tem_sp_suficiente():
                print("\n[!] SP DETECTADO: Ativando Battle Mode")
                keyboard.press_and_release(BM_KEY)
                inicio_bm = time.time()
                bm_ativa = True
                aura_ativa = False
                time.sleep(2.0) # Tempo de animação da BM

            # --- Execução das Skills ---
            rotação = BM_SKILLS if bm_ativa else SKILL_KEYS
            for skill in rotação:
                if not rodando or modo_critico or not janela_ativa(): 
                    break
                keyboard.press_and_release(skill)
                time.sleep(DELAY_SKILL)
        else:
            time.sleep(0.1)

def loop_bot():
    global rodando, modo_critico, ultima_small_heal, ultima_big_heal
    print("Monitorando HP e DPS...")
    hp_anterior = calcular_hp_percentual()
    tempo_anterior = time.time()

    while rodando:
        if not janela_ativa():
            time.sleep(0.5)
            continue

        agora = time.time()
        hp = calcular_hp_percentual()
        
        # Previsão de risco baseada em DPS
        dps = (hp_anterior - hp) / (agora - tempo_anterior) if (agora - tempo_anterior) > 0 else 0
        hp_anterior, tempo_anterior = hp, agora
        
        # Cura de Emergência (Prioridade sobre tudo)
        if hp < 25 or (dps > 8 and hp < 50): 
            modo_critico = True
            if (agora - ultima_big_heal) >= BIG_HEAL_COOLDOWN:
                keyboard.press_and_release("esc") # Garante que não está 'preso' em skill
                keyboard.press_and_release(BIG_HEAL_KEY)
                ultima_big_heal = agora
            elif (agora - ultima_small_heal) >= SMALL_HEAL_COOLDOWN:
                keyboard.press_and_release(SMALL_HEAL_KEY)
                ultima_small_heal = agora
        else:
            modo_critico = False
            # Cura Preventiva
            if hp < 75 and (agora - ultima_small_heal) >= SMALL_HEAL_COOLDOWN:
                keyboard.press_and_release(SMALL_HEAL_KEY)
                ultima_small_heal = agora

        time.sleep(DELAY_LOOP)

# --- CONTROLES ---

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=loop_bot, daemon=True).start()
        threading.Thread(target=loop_ataque, daemon=True).start()
        print("\n>>> BOT LIGADO (F7) <<<")

def parar():
    global rodando
    rodando = False
    print("\n>>> BOT DESLIGADO (F8) <<<")

keyboard.add_hotkey("F7", iniciar)
keyboard.add_hotkey("F8", parar)

print(f"Janela Alvo: {NOME_DA_JANELA}")
print("Pressione F7 para começar.")
keyboard.wait()
