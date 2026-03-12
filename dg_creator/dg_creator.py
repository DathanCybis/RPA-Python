import pyautogui
import keyboard
import time
import threading
import json
import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

# ===== AJUSTE DE PRECISÃO =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PASTA_APP = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_APP, "config_dgs.json")

# Cores Dark Mode
BG_DARK = "#1e1e1e"
BG_PANEL = "#2d2d2d"
FG_WHITE = "#ffffff"
ACCENT_BLUE = "#3794ff"

def caminho_img(nome):
    if not nome.endswith('.png'): nome += '.png'
    # Retorna o caminho absoluto completo
    return os.path.normpath(os.path.join(PASTA_APP, nome))

# ==========================================================
#        CONFIGURAÇÕES TÉCNICAS
# ==========================================================
TECLAS = {
    "combate": "f2", "movimento": "f3", "select": "z", "loot": "space",
    "skills": ["1", "2", "3", "4", "5", "space"],
    "dash_longo": "1", # Geralmente Dash maior
    "dash_curto": "2"  # Geralmente Fade/Dash menor
}

# ==========================================================
#        SISTEMA DE ARQUIVOS
# ==========================================================
def carregar_dados():
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r') as f:
                return json.load(f)
        except: return {"Dungeons": {}}
    return {"Dungeons": {}}

def salvar_dados(dados):
    with open(ARQUIVO_CONFIG, 'w') as f:
        json.dump(dados, f, indent=4)

# ==========================================================
#        MOTOR DO BOT (LÓGICA DE EXECUÇÃO)
# ==========================================================
class BotEngine:
    def __init__(self):
        self.rodando = False
        self.dg_atual = ""
        self.passo_inicial = 1
        self.total_ciclos = 1
        self.dados = carregar_dados()

    def verificar_imagem(self, img_nome):
        path = caminho_img(img_nome)
        if not os.path.exists(path):
            # Se a imagem não existir, ele avisa no console e pula a verificação
            print(f"[ERRO] Imagem não encontrada: {path}")
            return False
        try: 
            return pyautogui.locateOnScreen(path, confidence=0.8) is not None
        except Exception as e:
            print(f"[AVISO] Erro ao processar imagem: {e}")
            return False

    def combate_estavel(self, trava_z=False):
        if not trava_z:
            keyboard.press_and_release(TECLAS["select"])
        for sk in TECLAS["skills"]:
            if not self.rodando: break
            keyboard.press_and_release(sk)
            time.sleep(0.08)

    def executar_passo(self, config_passo):
        if not self.rodando: return

        # 1. Movimentação
        keyboard.press_and_release(TECLAS["movimento"])
        time.sleep(0.15)
        
        btn = 'right' if config_passo.get("click_btn", "Direito") == "Direito" else 'left'
        pyautogui.click(config_passo["coord"][0], config_passo["coord"][1], button=btn)
        
        # --- AJUSTE DE TEMPO DOS DASHS ---
        for d in config_passo.get("dashs", []):
            if not self.rodando: break
            if str(d) == "1":
                keyboard.press_and_release(TECLAS["dash_longo"])
                time.sleep(1) # Tempo do Dash Maior
            else:
                keyboard.press_and_release(TECLAS["dash_curto"])
                time.sleep(1) # Tempo do Dash Menor

        # Espera de chegada (configurável no JSON)
        espera = config_passo.get("espera_pos", 0)
        if espera > 0:
            time.sleep(espera)

        # 2. Combate
        keyboard.press_and_release(TECLAS["combate"])
        if config_passo.get("is_boss", False):
            while self.rodando:
                boss_visivel = self.verificar_imagem("icone_boss")
                self.combate_estavel(trava_z=boss_visivel)
                keyboard.press_and_release(TECLAS["loot"])
                # Checa se o baú/dg acabou
                if self.verificar_imagem("botao_ok"): 
                    print("[BOT] Botão OK detectado. Finalizando combate.")
                    break
                time.sleep(0.05)
        elif config_passo.get("tempo_ataque", 0) > 0:
            fim = time.time() + config_passo["tempo_ataque"]
            while time.time() < fim and self.rodando:
                self.combate_estavel()
                time.sleep(0.1)

        # 3. Loot
        if config_passo.get("loot_final", False):
            for _ in range(25):
                if not self.rodando: break
                keyboard.press_and_release(TECLAS["loot"])
                time.sleep(0.1)
        
        time.sleep(0.3)

    def thread_principal(self):
        for c in range(self.total_ciclos):
            if not self.rodando: break
            print(f"[LOOP] Iniciando Ciclo {c+1}/{self.total_ciclos}")
            
            passos = self.dados["Dungeons"][self.dg_atual]
            chaves = sorted(passos.keys(), key=lambda x: int(x.split("passo")[1]))
            
            inicio_efetivo = self.passo_inicial if c == 0 else 1
            chaves_para_rodar = [k for k in chaves if int(k.split("passo")[1]) >= inicio_efetivo]

            for k in chaves_para_rodar:
                if not self.rodando: break
                self.executar_passo(passos[k])
            
            time.sleep(2) 
        
        self.rodando = False
        print("[SISTEMA] Finalizado.")

# ==========================================================
#        INTERFACE GRÁFICA (GUI)
# ==========================================================
class AppDG:
    def __init__(self, root):
        self.engine = BotEngine()
        self.root = root
        self.root.title("Cabal DG Creator Pro - v2.2")
        self.root.geometry("600x500")
        self.root.configure(bg=BG_DARK)
        
        self.setup_styles()
        self.setup_ui()
        self.atualizar_combo_dgs()
        
        keyboard.add_hotkey('f9', self.gravar_coordenada)
        keyboard.add_hotkey('f7', self.iniciar_bot)
        keyboard.add_hotkey('f8', self.parar_bot)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=BG_DARK)
        style.configure("TLabel", background=BG_DARK, foreground=FG_WHITE)
        style.configure("TLabelframe", background=BG_DARK, foreground=ACCENT_BLUE)
        style.configure("TLabelframe.Label", background=BG_DARK, foreground=ACCENT_BLUE)
        style.configure("TButton", background=BG_PANEL, foreground=FG_WHITE)

    def setup_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        panel = ttk.LabelFrame(container, text=" Controle de Dungeons ", padding=10)
        panel.pack(fill=tk.X)

        ttk.Label(panel, text="DG:").grid(row=0, column=0)
        self.combo_dg = ttk.Combobox(panel, width=15)
        self.combo_dg.grid(row=0, column=1, padx=5)
        self.combo_dg.bind("<<ComboboxSelected>>", self.carregar_passos_na_lista)

        ttk.Label(panel, text="Ciclos:").grid(row=0, column=2, padx=5)
        self.ent_ciclos = ttk.Entry(panel, width=5)
        self.ent_ciclos.insert(0, "1"); self.ent_ciclos.grid(row=0, column=3)

        self.lista_passos = tk.Listbox(container, bg=BG_PANEL, fg=FG_WHITE, borderwidth=0, font=("Consolas", 10))
        self.lista_passos.pack(fill=tk.BOTH, expand=True, pady=10)

        footer = ttk.Label(container, text="F7: Iniciar | F8: Parar | F9: Gravar Novo Ponto", font=("Arial", 9, "italic"))
        footer.pack()

    def atualizar_combo_dgs(self):
        self.engine.dados = carregar_dados()
        self.combo_dg['values'] = list(self.engine.dados.get("Dungeons", {}).keys())

    def carregar_passos_na_lista(self, event=None):
        self.lista_passos.delete(0, tk.END)
        dg = self.combo_dg.get()
        if dg in self.engine.dados.get("Dungeons", {}):
            passos = self.engine.dados["Dungeons"][dg]
            for k in sorted(passos.keys(), key=lambda x: int(x.split("passo")[1])):
                p = passos[k]
                self.lista_passos.insert(tk.END, f"{k} | Click: {p.get('click_btn')} | Dashs: {p.get('dashs')}")

    def gravar_coordenada(self):
        coord = pyautogui.position()
        dg = self.combo_dg.get()
        if not dg:
            messagebox.showwarning("Aviso", "Digite um nome para a DG no campo acima!")
            return

        win = tk.Toplevel(self.root); win.configure(bg=BG_DARK); win.title("Gravar Passo")
        
        ttk.Label(win, text=f"Posição: {coord}").pack(pady=5)
        
        ttk.Label(win, text="Botão Mouse:").pack()
        btn_c = ttk.Combobox(win, values=["Direito", "Esquerdo"]); btn_c.set("Direito"); btn_c.pack()

        ttk.Label(win, text="Dashs (1=Maior, 2=Menor):").pack()
        ent_d = ttk.Entry(win); ent_d.pack()
        
        ttk.Label(win, text="Espera após mover (seg):").pack()
        ent_w = ttk.Entry(win); ent_w.insert(0, "2"); ent_w.pack()

        v_b = tk.BooleanVar(); ttk.Checkbutton(win, text="É Boss?", variable=v_b).pack()

        def salvar():
            if "Dungeons" not in self.engine.dados: self.engine.dados["Dungeons"] = {}
            if dg not in self.engine.dados["Dungeons"]: self.engine.dados["Dungeons"][dg] = {}
            
            num = len(self.engine.dados["Dungeons"][dg]) + 1
            self.engine.dados["Dungeons"][dg][f"passo{num}"] = {
                "coord": [coord.x, coord.y],
                "click_btn": btn_c.get(),
                "dashs": [int(x.strip()) for x in ent_d.get().split(",")] if ent_d.get() else [],
                "espera_pos": float(ent_w.get() or 2),
                "tempo_ataque": 0,
                "is_boss": v_b.get(),
                "loot_final": False
            }
            salvar_dados(self.engine.dados)
            self.atualizar_combo_dgs(); self.carregar_passos_na_lista(); win.destroy()

        ttk.Button(win, text="SALVAR", command=salvar).pack(pady=10)

    def iniciar_bot(self):
        if not self.engine.rodando:
            self.engine.dg_atual = self.combo_dg.get()
            self.engine.total_ciclos = int(self.ent_ciclos.get() or 1)
            if self.engine.dg_atual:
                self.engine.rodando = True
                threading.Thread(target=self.engine.thread_principal, daemon=True).start()

    def parar_bot(self):
        self.engine.rodando = False

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDG(root)
    root.mainloop()
