import pyautogui
import keyboard
import time
import threading

# ===== CONFIGURAÇÕES =====

# Barra de HP
HP_BAR_START = 82
HP_BAR_END = 276
HP_BAR_Y = 49

# ===== THRESHOLDS =====
CRITICAL_THRESHOLD = 25
CRITICAL_EXIT = 30

SMALL_HEAL_THRESHOLD = 70
BIG_HEAL_THRESHOLD = 40

# ===== CURAS =====

SMALL_HEAL_KEY = "0"
SMALL_HEAL_COOLDOWN = 3
SMALL_HEAL_ANIMATION = 1

BIG_HEAL_KEY = "9"
BIG_HEAL_COOLDOWN = 70
BIG_HEAL_ANIMATION = 0

ultima_small_heal = 0
ultima_big_heal = 0

# Ataque
SKILL_KEYS = ["z", "3", "4", "5", "6"] # "space"

# Delays
DELAY_SKILL = 0.2
DELAY_LOOP = 0.05

rodando = False
modo_critico = False


def calcular_hp_percentual():
    largura = HP_BAR_END - HP_BAR_START

    screenshot = pyautogui.screenshot(
        region=(HP_BAR_START, HP_BAR_Y, largura, 1)
    )

    pixels_vida = 0

    for x in range(largura):
        r, g, b = screenshot.getpixel((x, 0))
        if r > g + 25 and r > b + 25:
            pixels_vida += 1

    return (pixels_vida / largura) * 100


def pode_small():
    return time.time() - ultima_small_heal >= SMALL_HEAL_COOLDOWN


def pode_big():
    return time.time() - ultima_big_heal >= BIG_HEAL_COOLDOWN


def usar_small():
    global ultima_small_heal

    print("\n>>> CURA PEQUENA")

    keyboard.press_and_release("esc")
    time.sleep(0.05)

    keyboard.press_and_release(SMALL_HEAL_KEY)
    ultima_small_heal = time.time()

    time.sleep(SMALL_HEAL_ANIMATION)


def usar_big():
    global ultima_big_heal

    print("\n>>> CURA GRANDE !!!")

    keyboard.press_and_release("esc")
    time.sleep(0.05)

    keyboard.press_and_release(BIG_HEAL_KEY)
    ultima_big_heal = time.time()

    time.sleep(BIG_HEAL_ANIMATION)


def atacar():
    for skill in SKILL_KEYS:
        keyboard.press_and_release(skill)
        time.sleep(DELAY_SKILL)


def loop_bot():
    global rodando, modo_critico

    print("Bot iniciado.")

    hp_anterior = calcular_hp_percentual()
    tempo_anterior = time.time()

    while rodando:

        agora = time.time()
        hp = calcular_hp_percentual()

        # ===== CÁLCULO DE DANO POR SEGUNDO =====
        delta_hp = hp_anterior - hp
        delta_tempo = agora - tempo_anterior

        dps_recebido = 0
        if delta_tempo > 0:
            dps_recebido = delta_hp / delta_tempo

        # Atualiza histórico
        hp_anterior = hp
        tempo_anterior = agora

        # ===== TEMPO ATÉ MORRER (PREVISÃO) =====
        tempo_ate_morrer = float("inf")
        if dps_recebido > 0:
            tempo_ate_morrer = hp / dps_recebido

        # ===== TEMPO RESTANTE BIG HEAL =====
        tempo_big_restante = BIG_HEAL_COOLDOWN - (agora - ultima_big_heal)

        if tempo_big_restante < 0:
            tempo_big_restante = 0

        print(
            f"HP:{hp:.1f}% | DPS:{dps_recebido:.2f} | "
            f"T_Morte:{tempo_ate_morrer:.1f}s | "
            f"BigCD:{tempo_big_restante:.1f}s",
            end="\r"
        )

        # ===== MODO CRÍTICO PADRÃO =====
        if hp < CRITICAL_THRESHOLD:
            modo_critico = True

        if modo_critico and hp > CRITICAL_EXIT:
            modo_critico = False
            print("\nSaindo do modo crítico")

        # ===== MODO SOBREVIVÊNCIA PREDITIVO =====
        sobrevivencia_extrema = (
            tempo_ate_morrer < tempo_big_restante
        )

        if sobrevivencia_extrema:
            print("\n>>> SOBREVIVÊNCIA EXTREMA <<<")

            if pode_small():
                usar_small()

            time.sleep(DELAY_LOOP)
            continue

        # ===== MODO CRÍTICO =====
        if modo_critico:

            if pode_big():
                usar_big()

            elif pode_small():
                usar_small()

            time.sleep(DELAY_LOOP)
            continue

        # ===== COMPORTAMENTO NORMAL =====
        if hp < BIG_HEAL_THRESHOLD and pode_big():
            usar_big()

        elif hp < SMALL_HEAL_THRESHOLD and pode_small():
            usar_small()

        atacar()
        time.sleep(DELAY_LOOP)

    print("\nBot parado.")



def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=loop_bot).start()


def parar():
    global rodando
    rodando = False


keyboard.add_hotkey("F7", iniciar)
keyboard.add_hotkey("F8", parar)

print("Pressione F7 para iniciar o bot.")
print("Pressione F8 para parar o bot.")

keyboard.wait()
