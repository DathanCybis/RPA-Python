import pyautogui
import keyboard
import time
import threading
import json
import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import pygetwindow as gw

# ===== AJUSTE DE PRECISÃO =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PASTA_APP = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_APP, "config_dgs.json")

def caminho_img(nome):
    if not nome.endswith('.png'): nome += '.png'
    return os.path.join(PASTA_APP, nome)

# ==========================================================
#        CONFIGURAÇÕES TÉCNICAS (CONFORME SEU AJUSTE)
# ==========================================================
TECLAS = {
    "combate": "f2", "movimento": "f3", "bm_aba": "f4",
    "select": "z", "loot": "space", "zoom": "-",
    "skills": ["1", "2", "3", "4", "5"],
    "dash_longo": "1", "dash_curto": "2",
    "heal_pequeno": "0", "heal_grande": "9"
}
HP_BAR = {"start": 82, "end": 276, "y": 49}

# ==========================================================
#        SISTEMA DE ARQUIVOS (JSON)
# ==========================================================
def carregar_dados():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, 'r') as f:
            return json.load(f)
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
        self.modo_critico = False
        self.dg_atual = ""
        self.passo_inicial = 1
        self.dados = carregar_dados()

    def verificar_imagem(self, img, conf=0.85):
        try: return pyautogui.locateOnScreen(caminho_img(img), confidence=conf) is not None
        except: return False

    def combate_estavel(self, trava_z=False):
        if self.modo_critico: return
        if not trava_z:
            keyboard.press_and_release(TECLAS["select"])
        
        for sk in TECLAS["skills"]:
            if not self.rodando: break
            keyboard.press_and_release(sk)
            time.sleep(0.1) # Seu ajuste de 0.1s

    def executar_passo(self, config_passo):
        if not self.rodando: return

        # 1. Movimentação
        keyboard.press_and_release(TECLAS["movimento"])
        time.sleep(0.2)
        coord = config_passo["coord"]
        pyautogui.click(coord[0], coord[1], button='right')
        
        for d in config_passo["dashs"]:
            tecla = TECLAS["dash_longo"] if str(d) == "1" else TECLAS["dash_curto"]
            keyboard.press_and_release(tecla)
            time.sleep(0.8)

        # 2. Lógica de Combate
        keyboard.press_and_release(TECLAS["combate"])
        
        # Se for BOSS
        if config_passo.get("is_boss", False):
            print("[BOT] Aguardando Boss...")
            while self.rodando:
                # Se detectar ícone de boss, trava o Z (Lógica anterior)
                no_boss = self.verificar_imagem("icone_boss")
                self.combate_estavel(trava_z=no_boss)
                keyboard.press_and_release(TECLAS["loot"])
                if self.verificar_imagem("botao_ok"): break # Boss morreu
                time.sleep(0.05)
        
        # Se for Tempo de Ataque
        elif config_passo.get("tempo_ataque", 0) > 0:
            fim = time.time() + config_passo["tempo_ataque"]
            while time.time() < fim and self.rodando:
                self.combate_estavel()
                time.sleep(0.1)

        # 3. Lógica de Loot
        if config_passo.get("loot_final", False):
            print("[BOT] Coletando itens...")
            for _ in range(30):
                if not self.rodando: break
                keyboard.press_and_release(TECLAS["loot"])
                time.sleep(0.12)

    def thread_principal(self):
        passos = self.dados["Dungeons"][self.dg_atual]
        chaves = sorted(passos.keys(), key=lambda x: int(x.split("passo")[1]))
        
        # Filtra a partir do passo inicial
        chaves_para_rodar = [c for c in chaves if int(c.split("passo")[1]) >= self.passo_inicial]

        for k in chaves_para_rodar:
            if not self.rodando: break
            print(f"[BOT] Executando {k}")
            self.executar_passo(passos[k])
        
        print("[BOT] DG Finalizada ou Parada.")
        self.rodando = False

# ==========================================================
#        INTERFACE GRÁFICA (GUI)
# ==========================================================
class AppDG:
    def __init__(self, root):
        self.engine = BotEngine()
        self.root = root
        self.root.title("Cabal DG Creator Pro")
        self.root.geometry("600x500")
        
        # Widgets
        self.setup_ui()
        self.atualizar_combo_dgs()
        
        # Atalhos Globais
        keyboard.add_hotkey('f9', self.gravar_coordenada)
        keyboard.add_hotkey('f7', self.iniciar_bot)
        keyboard.add_hotkey('f8', self.parar_bot)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Topo: Seleção de DG
        top_frame = ttk.LabelFrame(main_frame, text=" Configurações da DG ", padding="5")
        top_frame.pack(fill=tk.X, pady=5)

        ttk.Label(top_frame, text="Selecione a DG:").grid(row=0, column=0, padx=5)
        self.combo_dg = ttk.Combobox(top_frame, values=[])
        self.combo_dg.grid(row=0, column=1, padx=5)
        self.combo_dg.bind("<<ComboboxSelected>>", self.carregar_passos_na_lista)

        ttk.Label(top_frame, text="Passo Inicial:").grid(row=0, column=2, padx=5)
        self.ent_passo_in = ttk.Entry(top_frame, width=5)
        self.ent_passo_in.insert(0, "1")
        self.ent_passo_in.grid(row=0, column=3, padx=5)

        # Centro: Lista de Passos
        self.lista_passos = tk.Listbox(main_frame, height=15)
        self.lista_passos.pack(fill=tk.BOTH, expand=True, pady=5)

        # Rodapé: Instruções
        instr = ttk.Label(main_frame, text="F9: Gravar Ponto | F7: START | F8: STOP", foreground="blue")
        instr.pack(pady=5)

    def atualizar_combo_dgs(self):
        self.engine.dados = carregar_dados()
        self.combo_dg['values'] = list(self.engine.dados["Dungeons"].keys())

    def carregar_passos_na_lista(self, event=None):
        self.lista_passos.delete(0, tk.END)
        dg = self.combo_dg.get()
        if dg in self.engine.dados["Dungeons"]:
            passos = self.engine.dados["Dungeons"][dg]
            for k in sorted(passos.keys(), key=lambda x: int(x.split("passo")[1])):
                p = passos[k]
                txt = f"{k} -> Coord: {p['coord']} | Dashs: {p['dashs']} | Boss: {p['is_boss']}"
                self.lista_passos.insert(tk.END, txt)

    def gravar_coordenada(self):
        # Janela de diálogo para capturar detalhes do passo
        coord = pyautogui.position()
        dg = self.combo_dg.get()
        if not dg:
            messagebox.showwarning("Aviso", "Escreva o nome de uma DG no seletor acima primeiro!")
            return

        # Interface simples de input
        win = tk.Toplevel(self.root)
        win.title("Configurar Passo")
        
        ttk.Label(win, text=f"Coord capturada: {coord}").pack(pady=5)
        
        ttk.Label(win, text="Sequência de Dashs (ex: 1, 2, 1):").pack()
        ent_dash = ttk.Entry(win); ent_dash.pack()
        
        ttk.Label(win, text="Tempo de Ataque (segundos):").pack()
        ent_tempo = ttk.Entry(win); ent_tempo.insert(0, "0"); ent_tempo.pack()
        
        var_boss = tk.BooleanVar()
        ttk.Checkbutton(win, text="Tem Ícone de Boss?", variable=var_boss).pack()
        
        var_loot = tk.BooleanVar()
        ttk.Checkbutton(win, text="Coletar Itens ao final?", variable=var_loot).pack()

        def salvar_passo():
            if dg not in self.engine.dados["Dungeons"]:
                self.engine.dados["Dungeons"][dg] = {}
            
            num_passo = len(self.engine.dados["Dungeons"][dg]) + 1
            dashs = [int(x.strip()) for x in ent_dash.get().split(",")] if ent_dash.get() else []
            
            self.engine.dados["Dungeons"][dg][f"passo{num_passo}"] = {
                "coord": [coord.x, coord.y],
                "dashs": dashs,
                "tempo_ataque": int(ent_tempo.get()),
                "is_boss": var_boss.get(),
                "loot_final": var_loot.get()
            }
            salvar_dados(self.engine.dados)
            self.atualizar_combo_dgs()
            self.carregar_passos_na_lista()
            win.destroy()

        ttk.Button(win, text="SALVAR PASSO", command=salvar_passo).pack(pady=10)

    def iniciar_bot(self):
        if not self.engine.rodando:
            self.engine.dg_atual = self.combo_dg.get()
            self.engine.passo_inicial = int(self.ent_passo_in.get())
            if self.engine.dg_atual:
                self.engine.rodando = True
                threading.Thread(target=self.engine.thread_principal, daemon=True).start()
                print(f"[ON] Iniciando {self.engine.dg_atual}")

    def parar_bot(self):
        self.engine.rodando = False
        print("[OFF] Bot Parado.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDG(root)
    root.mainloop()
