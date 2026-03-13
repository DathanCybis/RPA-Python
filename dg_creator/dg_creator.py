import pyautogui
import keyboard
import time
import threading
import json
import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

# ===== PRECISÃO DE TELA (DPI AWARE) =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PASTA_APP = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_APP, "config_dgs.json")

# Cores e Estilo
BG_DARK = "#121212"
BG_PANEL = "#1e1e1e"
FG_WHITE = "#e0e0e0"
ACCENT_GREEN = "#00ff7f"
ACCENT_RED = "#ff4d4d"

def carregar_dados():
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {"Dungeons": {}}
    return {"Dungeons": {}}

def salvar_dados(dados):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ==========================================================
#        MOTOR DO BOT
# ==========================================================
class BotEngine:
    def __init__(self, callback_log):
        self.rodando = False
        self.dg_atual = ""
        self.total_ciclos = 1
        self.dados = carregar_dados()
        self.callback_log = callback_log

    def log(self, msg):
        self.callback_log(msg)

    def verificar_imagem(self, img_nome):
        path = os.path.join(PASTA_APP, f"{img_nome}.png")
        if not os.path.exists(path): return False
        try: return pyautogui.locateOnScreen(path, confidence=0.7) is not None
        except: return False

    def resetar_zoom(self, segundos):
        if not self.rodando: return
        keyboard.press('-')
        time.sleep(segundos)
        keyboard.release('-')
        time.sleep(0.3)

    def soltar_skills(self):
        for sk in ["1", "2", "3", "4", "5", "space"]:
            if not self.rodando: break
            keyboard.press_and_release(sk)
            time.sleep(0.08)

    def executar_passo(self, p, nome_p, ultimo_esq):
        if not self.rodando: return
        self.log(f"Indo para: {nome_p}")

        # Lógica de Zoom
        if p.get("reset_zoom", False): self.resetar_zoom(3.0)
        elif ultimo_esq and p.get("click_btn") == "Direito": self.resetar_zoom(1.5)

        # Movimentação
        keyboard.press_and_release("f3")
        time.sleep(0.1)
        btn = 'right' if p.get("click_btn") == "Direito" else 'left'
        pyautogui.click(p["coord"][0], p["coord"][1], button=btn)
        
        for d in p.get("dashs", []):
            if not self.rodando: break
            keyboard.press_and_release(str(d)); time.sleep(1.0)

        time.sleep(p.get("espera_pos", 1))

        # Combate Inteligente
        if p.get("is_boss", False):
            self.log("Alvo: BOSS")
            keyboard.press_and_release("f2")
            while self.rodando:
                # Só aperta Z se o ícone do boss NÃO estiver na tela
                if not self.verificar_imagem("icone_boss"):
                    keyboard.press_and_release("z")
                    time.sleep(0.2)
                
                self.soltar_skills()
                
                if self.verificar_imagem("botao_ok"): break
                if not self.verificar_imagem("icone_boss"):
                    time.sleep(1.2)
                    if not self.verificar_imagem("icone_boss"): break

        elif p.get("tempo_ataque", 0) > 0:
            self.log(f"Ataque: {p['tempo_ataque']}s")
            keyboard.press_and_release("f2")
            fim = time.time() + p["tempo_ataque"]
            while time.time() < fim and self.rodando:
                keyboard.press_and_release("z")
                self.soltar_skills()

        if p.get("loot_final", False):
            self.log("Coletando Loot...")
            for _ in range(20):
                if not self.rodando: break
                keyboard.press_and_release("space"); time.sleep(0.1)

    def thread_principal(self):
        for c in range(self.total_ciclos):
            if not self.rodando: break
            self.log(f"Ciclo {c+1}/{self.total_ciclos}")
            
            # Buffs Iniciais
            keyboard.press_and_release("f3")
            for b in ["3", "4"]: keyboard.press_and_release(b); time.sleep(1.3)
            
            passos_dict = self.dados["Dungeons"][self.dg_atual]
            chaves = sorted(passos_dict.keys(), key=lambda x: int(x.split("passo")[1]))
            
            ultimo_esq = False
            for k in chaves:
                if not self.rodando: break
                self.executar_passo(passos_dict[k], k, ultimo_esq)
                ultimo_esq = (passos_dict[k].get("click_btn") == "Esquerdo")
        
        self.rodando = False
        self.log("Fim da Rota")

# ==========================================================
#        INTERFACE GRÁFICA + OVERLAY
# ==========================================================
class AppDG:
    def __init__(self, root):
        self.engine = BotEngine(self.update_overlay)
        self.root = root
        self.root.title("Cabal Pro v4.1")
        self.root.geometry("500x600")
        self.root.configure(bg=BG_DARK)
        
        self.setup_main_ui()
        self.setup_overlay()
        self.atualizar_combo()
        
        # Atalhos Globais
        keyboard.add_hotkey('f7', self.iniciar_bot)
        keyboard.add_hotkey('f8', self.parar_bot)
        keyboard.add_hotkey('f9', self.gravar_coordenada)

    def setup_main_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Dungeon Ativa:").pack(anchor="w")
        self.combo_dg = ttk.Combobox(main_frame, postcommand=self.atualizar_combo)
        self.combo_dg.pack(fill=tk.X, pady=5)
        self.combo_dg.bind("<<ComboboxSelected>>", self.mostrar_passos)

        ttk.Label(main_frame, text="Quantidade de Ciclos:").pack(anchor="w")
        self.ent_ciclos = ttk.Entry(main_frame); self.ent_ciclos.insert(0, "1")
        self.ent_ciclos.pack(fill=tk.X, pady=5)

        self.lista = tk.Listbox(main_frame, bg=BG_PANEL, fg=FG_WHITE, font=("Consolas", 10), borderwidth=0)
        self.lista.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Button(main_frame, text="REMOVER PASSO SELECIONADO", bg=ACCENT_RED, fg="white", command=self.remover_passo).pack(fill=tk.X)
        
        footer = tk.Label(main_frame, text="F7: Start | F8: Stop | F9: Gravar", font=("Arial", 10, "bold"), pady=10)
        footer.pack()

    def setup_overlay(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.geometry("200x100+10+300") # Posição: Esquerda Meio
        self.overlay.overrideredirect(True)
        self.overlay.attributes('-topmost', True, '-alpha', 0.7)
        self.overlay.configure(bg="#000000")
        
        self.lbl_ov_status = tk.Label(self.overlay, text="BOT PRONTO", fg=ACCENT_GREEN, bg="#000000", font=("Consolas", 10, "bold"))
        self.lbl_ov_status.pack(expand=True)
        
        tk.Label(self.overlay, text="[F8] PARAR", fg="white", bg="#333333", font=("Arial", 8)).pack(fill=tk.X)

    def update_overlay(self, msg):
        self.lbl_ov_status.config(text=msg)

    def atualizar_combo(self):
        self.engine.dados = carregar_dados()
        self.combo_dg['values'] = list(self.engine.dados.get("Dungeons", {}).keys())

    def mostrar_passos(self, event=None):
        self.lista.delete(0, tk.END)
        dg = self.combo_dg.get()
        if dg in self.engine.dados["Dungeons"]:
            passos = self.engine.dados["Dungeons"][dg]
            for k in sorted(passos.keys(), key=lambda x: int(x.split("passo")[1])):
                p = passos[k]
                self.lista.insert(tk.END, f"{k}: {p['click_btn']} | Boss: {p['is_boss']}")

    def remover_passo(self):
        sel = self.lista.curselection()
        if not sel: return
        dg = self.combo_dg.get()
        passos = self.engine.dados["Dungeons"][dg]
        chaves = sorted(passos.keys(), key=lambda x: int(x.split("passo")[1]))
        del passos[chaves[sel[0]]]
        
        # Reorganizar
        novos = {f"passo{i}": passos[k] for i, k in enumerate(sorted(passos.keys(), key=lambda x: int(x.split("passo")[1])), 1)}
        self.engine.dados["Dungeons"][dg] = novos
        salvar_dados(self.engine.dados); self.mostrar_passos()

    def gravar_coordenada(self):
        coord = pyautogui.position()
        dg = self.combo_dg.get()
        if not dg: return
        
        win = tk.Toplevel(self.root); win.title("Gravar Passo"); win.geometry("280x450")
        win.attributes('-topmost', True); win.configure(bg=BG_PANEL)
        
        ttk.Label(win, text=f"Coord: {coord.x}, {coord.y}").pack(pady=5)
        
        ttk.Label(win, text="Botão:").pack()
        btn_c = ttk.Combobox(win, values=["Direito", "Esquerdo"]); btn_c.set("Direito"); btn_c.pack()
        
        ttk.Label(win, text="Dashs (ex: 1,2):").pack()
        ent_d = ttk.Entry(win); ent_d.pack()
        
        ttk.Label(win, text="Tempo Ataque:").pack()
        ent_atq = ttk.Entry(win); ent_atq.insert(0, "0"); ent_atq.pack()
        
        ttk.Label(win, text="Espera pós Dash:").pack()
        ent_w = ttk.Entry(win); ent_w.insert(0, "2"); ent_w.pack()
        
        v_z = tk.BooleanVar(); ttk.Checkbutton(win, text="Resetar Zoom (3s)?", variable=v_z).pack()
        v_b = tk.BooleanVar(); ttk.Checkbutton(win, text="É Boss? (Anti-Z)", variable=v_b).pack()
        v_l = tk.BooleanVar(); ttk.Checkbutton(win, text="Loot Final?", variable=v_l).pack()

        def salvar():
            if dg not in self.engine.dados["Dungeons"]: self.engine.dados["Dungeons"][dg] = {}
            num = len(self.engine.dados["Dungeons"][dg]) + 1
            self.engine.dados["Dungeons"][dg][f"passo{num}"] = {
                "coord": [coord.x, coord.y], "click_btn": btn_c.get(),
                "dashs": [int(x.strip()) for x in ent_d.get().split(",")] if ent_d.get() else [],
                "espera_pos": float(ent_w.get() or 2), "tempo_ataque": float(ent_atq.get() or 0),
                "is_boss": v_b.get(), "loot_final": v_l.get(), "reset_zoom": v_z.get()
            }
            salvar_dados(self.engine.dados); self.mostrar_passos(); win.destroy()

        tk.Button(win, text="SALVAR", bg=ACCENT_GREEN, command=salvar).pack(pady=15)

    def iniciar_bot(self):
        if not self.engine.rodando:
            self.engine.dg_atual = self.combo_dg.get()
            self.engine.total_ciclos = int(self.ent_ciclos.get() or 1)
            if self.engine.dg_atual:
                self.engine.rodando = True
                threading.Thread(target=self.engine.thread_principal, daemon=True).start()

    def parar_bot(self):
        self.engine.rodando = False
        self.update_overlay("BOT PARADO")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDG(root)
    root.mainloop()
