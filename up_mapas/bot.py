import pyautogui
import keyboard
import time
import threading
import pygetwindow as gw

# ===== CONFIGURAÇÕES =====
NOME_DA_JANELA = "CABAL"  # Altere para o nome exato da janela do jogo

# Barra de HP (Coordenadas)
HP_BAR_START = 82
HP_BAR_END = 276
HP_BAR_Y = 49

# ===== THRESHOLDS (Limiares) =====
CRITICAL_THRESHOLD = 25
CRITICAL_EXIT = 35        # Um pouco maior que o threshold para evitar "flicker"
SMALL_HEAL_THRESHOLD = 70
BIG_HEAL_THRESHOLD = 40

# ===== CURAS =====
SMALL_HEAL_KEY = "0"
SMALL_HEAL_COOLDOWN = 3
BIG_HEAL_KEY = "9"
BIG_HEAL_COOLDOWN = 70

# Histórico de cura
ultima_small_heal = 0
ultima_big_heal = 0

# Ataque
SKILL_KEYS = ["z", "3", "4", "5", "6", "space"]
DELAY_SKILL = 0.2
DELAY_LOOP = 0.05

# Controle Global
rodando = False
modo_critico = False

# --- FUNÇÕES DE SUPORTE ---

def janela_ativa():
    """Verifica se o Cabal é a janela em foco."""
    try:
        janela = gw.getActiveWindow()
        return janela is not None and NOME_DA_JANELA.lower() in janela.title.lower()
    except:
        return False

def calcular_hp_percentual():
    largura = HP_BAR_END - HP_BAR_START
    # Captura apenas a linha da barra de HP para performance
    screenshot = pyautogui.screenshot(region=(HP_BAR_START, HP_BAR_Y, largura, 1))
    
    pixels_vida = 0
    for x in range(largura):
        r, g, b = screenshot.getpixel((x, 0))
        # Lógica para detectar o vermelho da barra
        if r > g + 25 and r > b + 25:
            pixels_vida += 1
    
    return (pixels_vida / largura) * 100 if largura > 0 else 0

def usar_cura(tipo):
    global ultima_small_heal, ultima_big_heal
    
    # Cancela casting atual com ESC (comum no Cabal para garantir a cura)
    keyboard.press_and_release("esc")
    time.sleep(0.05)
    
    if tipo == "BIG":
        print("\n>>> USANDO CURA GRANDE (9) <<<")
        keyboard.press_and_release(BIG_HEAL_KEY)
        ultima_big_heal = time.time()
    else:
        print("\n>>> USANDO CURA PEQUENA (0) <<<")
        keyboard.press_and_release(SMALL_HEAL_KEY)
        ultima_small_heal = time.time()

# --- THREADS ---

def loop_ataque():
    """Roda em paralelo ao HP para não interromper a leitura da vida."""
    global rodando, modo_critico
    while rodando:
        if janela_ativa() and not modo_critico:
            for skill in SKILL_KEYS:
                if not rodando or modo_critico or not janela_ativa(): 
                    break
                keyboard.press_and_release(skill)
                time.sleep(DELAY_SKILL)
        else:
            time.sleep(0.2) # Dorme um pouco se estiver fora da janela ou em perigo

def loop_bot():
    global rodando, modo_critico, ultima_small_heal, ultima_big_heal

    print(f"Bot Monitorando Janela: [{NOME_DA_JANELA}]")
    
    hp_anterior = calcular_hp_percentual()
    tempo_anterior = time.time()

    while rodando:
        if not janela_ativa():
            time.sleep(0.5)
            continue

        agora = time.time()
        hp = calcular_hp_percentual()

        # Cálculo de DPS e Previsão (Sua lógica original)
        delta_hp = hp_anterior - hp
        delta_tempo = agora - tempo_anterior
        dps_recebido = max(0, delta_hp / delta_tempo) if delta_tempo > 0 else 0
        
        hp_anterior = hp
        tempo_anterior = agora

        tempo_ate_morrer = hp / dps_recebido if dps_recebido > 0 else 999
        cd_big = max(0, BIG_HEAL_COOLDOWN - (agora - ultima_big_heal))
        cd_small = max(0, SMALL_HEAL_COOLDOWN - (agora - ultima_small_heal))

        print(f"HP: {hp:.1f}% | DPS: {dps_recebido:.1f} | Morte em: {tempo_ate_morrer:.1f}s | CD Big: {cd_big:.1f}s", end="\r")

        # --- LÓGICA DE DECISÃO ---

        # 1. Modo Crítico (Entrada e Saída)
        if hp < CRITICAL_THRESHOLD or tempo_ate_morrer < cd_big:
            modo_critico = True
        elif hp > CRITICAL_EXIT:
            modo_critico = False

        # 2. Execução das Curas
        if modo_critico:
            if cd_big == 0:
                usar_cura("BIG")
            elif cd_small == 0:
                usar_cura("SMALL")
        
        elif hp < SMALL_HEAL_THRESHOLD:
            if hp < BIG_HEAL_THRESHOLD and cd_big == 0:
                usar_cura("BIG")
            elif cd_small == 0:
                usar_cura("SMALL")

        time.sleep(DELAY_LOOP)

# --- CONTROLES DE INÍCIO ---

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=loop_bot, daemon=True).start()
        threading.Thread(target=loop_ataque, daemon=True).start()
        print("\n[ON] Bot em execução...")

def parar():
    global rodando
    rodando = False
    print("\n[OFF] Bot desligado.")

keyboard.add_hotkey("F7", iniciar)
keyboard.add_hotkey("F8", parar)

print("F7: Iniciar | F8: Parar")
keyboard.wait()