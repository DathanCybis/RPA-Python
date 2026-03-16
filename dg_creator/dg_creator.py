import pyautogui
import keyboard
import time
import threading
import json
import os
import ctypes
import tkinter as tk
from tkinter import ttk

# ===== PRECISÃO DE TELA (DPI AWARE) =====
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PASTA_APP = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_APP, "config_dgs.json")

# Estilo Visual
BG_DARK = "#121212"
BG_PANEL = "#1e1e1e"
FG_WHITE = "#e0e0e0"
ACCENT_GREEN = "#00ff7f"

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
#        MOTOR DO BOT v5.2
# ==========================================================
class BotEngine:
    def __init__(self, callback_log):
        self.rodando = False
        self.dg_atual = ""
        self.total_ciclos = 1
        self.skills_usuario = []
        self.cast_global = 0.5
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
        # Percorre as teclas configuradas na aba Combate
        for sk in self.skills_usuario:
            if not self.rodando: break
            keyboard.press_and_release(sk.strip())
            time.sleep(0.05)
        
        keyboard.press_and_release("space") # Loot passivo
        
        # Respeita o Tempo de Cast Global
        if self.cast_global > 0:
            time.sleep(self.cast_global)

    def executar_passo(self, p, nome_p, ultimo_esq):
        if not self.rodando: return
        self.log(f"Passo: {nome_p}")

        # Lógica de Zoom Inteligente
        if p.get("reset_zoom", False): 
            self.resetar_zoom(3.0)
        elif ultimo_esq and p.get("click_btn") == "Direito": 
            self.resetar_zoom(1.5)

        # Movimentação
        keyboard.press_and_release("f3")
        time.sleep(0.1)
        btn = 'right' if p.get("click_btn") == "Direito" else 'left'
        pyautogui.click(p["coord"][0], p["coord"][1], button=btn)
        
        for d in p.get("dashs", []):
            if not self.rodando: break
            keyboard.press_and_release(str(d))
            time.sleep(1.0)

        time.sleep(p.get("espera_pos", 1))

        # Lógica de Combate
        if p.get("is_boss", False):
            self.log("Alvo: BOSS")
            keyboard.press_and_release("f2")
            while self.rodando:
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
            self.log("Loot Final...")
            for _ in range(15):
                if not self.rodando: break
                keyboard.press_and_release("space"); time.sleep(0.1)

    def thread_principal(self):
        for c in range(self.total_ciclos):
            if not self.rodando: break
            self.log(f"Ciclo {c+1}/{self.total_ciclos}")
            keyboard.press_and_release("f3")
            for b in ["3", "4"]: keyboard.press_and_release(b); time.sleep(1.3)
            
            passos = self.dados["Dungeons"][self.dg_atual]
            chaves = sorted(passos.keys(), key=lambda x: int(x.split("passo")[1]))
            ultimo_esq = False
            for k in chaves:
                if not self.rodando: break
                self.executar_passo(passos[k], k, ultimo_esq)
                ultimo_esq = (passos[k].get("click_btn") == "Esquerdo")
        
        self.rodando = False
        self.log("BOT PARADO")

# ==========================================================
#        INTERFACE GRÁFICA (TABS + OVERLAY)
# ==========================================================
class AppDG:
    def __init__(self, root):
        self.engine = BotEngine(self.update_overlay)
        self.root = root
        self.root.title("Cabal Pro v5.2")
        self.root.geometry("450x650")
        
        # Sistema de Abas
        self.tabs = ttk.Notebook(root)
        self.tab_principal = ttk.Frame(self.tabs)
        self.tab_combate = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_principal, text=' Rota & Passos ')
        self.tabs.add(self.tab_combate, text=' Skills & Cast ')
        self.tabs.pack(expand=1, fill="both")
        
        self.setup_aba_principal()
        self.setup_aba_combate()
        self.setup_overlay()
        
        # Atalhos
        keyboard.add_hotkey('f7', self.iniciar_bot)
        keyboard.add_hotkey('f8', self.parar_bot)
        keyboard.add_hotkey('f9', self.gravar_coordenada)

    def setup_aba_principal(self):
        f = self.tab_principal
        ttk.Label(f, text="Selecione a Dungeon:").pack(pady=(10,0))
        self.combo_dg = ttk.Combobox(f, postcommand=self.carregar_lista_dgs)
        self.combo_dg.pack(fill=tk.X, padx=20)
        self.combo_dg.bind("<<ComboboxSelected>>", self.atualizar_lista_passos)

        ttk.Label(f, text="Quantidade de Ciclos:").pack(pady=(10,0))
        self.ent_ciclos = ttk.Entry(f); self.ent_ciclos.insert(0, "1"); self.ent_ciclos.pack(padx=20)

        self.listbox = tk.Listbox(f, bg=BG_PANEL, fg=FG_WHITE, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Button(f, text="REMOVER PASSO", bg="#ff4d4d", fg="white", command=self.remover_passo).pack(fill=tk.X, padx=20, pady=5)
        tk.Label(f, text="F7: Iniciar | F8: Parar | F9: Gravar", font=("Arial", 9, "italic")).pack()

    def setup_aba_combate(self):
        f = self.tab_combate
        ttk.Label(f, text="Sequência de Teclas (ex: 1, 2, 3, 4, f1):").pack(pady=(20,0))
        self.ent_skills = ttk.Entry(f); self.ent_skills.insert(0, "1, 2, 3, 4, 5"); self.ent_skills.pack(fill=tk.X, padx=40)

        ttk.Label(f, text="Tempo de Cast Global (segundos):").pack(pady=(20,0))
        self.ent_cast = ttk.Entry(f); self.ent_cast.insert(0, "0.5"); self.ent_cast.pack(padx=40)
        
        info = "Dica: O tempo de cast é a pausa necessária\npara a animação da skill terminar antes do movimento."
        tk.Label(f, text=info, font=("Arial", 8), fg="gray").pack(pady=20)

    def setup_overlay(self):
        self.overlay_win = tk.Toplevel(self.root)
        self.overlay_win.geometry("200x80+10+350")
        self.overlay_win.overrideredirect(True)
        self.overlay_win.attributes('-topmost', True, '-alpha', 0.8)
        self.overlay_win.configure(bg="black")
        self.lbl_ov = tk.Label(self.overlay_win, text="PRONTO", fg=ACCENT_GREEN, bg="black", font=("Consolas", 10, "bold"))
        self.lbl_ov.pack(expand=True)

    def update_overlay(self, msg):
        self.lbl_ov.config(text=msg)

    def carregar_lista_dgs(self):
        self.engine.dados = carregar_dados()
        self.combo_dg['values'] = list(self.engine.dados.get("Dungeons", {}).keys())

    def atualizar_lista_passos(self, e=None):
        self.listbox.delete(0, tk.END)
        dg = self.combo_dg.get()
        if dg in self.engine.dados["Dungeons"]:
            p = self.engine.dados["Dungeons"][dg]
            for k in sorted(p.keys(), key=lambda x: int(x.split("passo")[1])):
                info = f"{k}: {p[k]['click_btn']}"
                if p[k].get("is_boss"): info += " [BOSS]"
                self.listbox.insert(tk.END, info)

    def remover_passo(self):
        sel = self.listbox.curselection()
        if not sel or not self.combo_dg.get(): return
        dg = self.combo_dg.get()
        p = self.engine.dados["Dungeons"][dg]
        keys = sorted(p.keys(), key=lambda x: int(x.split("passo")[1]))
        del p[keys[sel[0]]]
        # Re-indexar
        self.engine.dados["Dungeons"][dg] = {f"passo{i}": p[k] for i, k in enumerate(sorted(p.keys(), key=lambda x: int(x.split("passo")[1])), 1)}
        salvar_dados(self.engine.dados); self.atualizar_lista_passos()

    def gravar_coordenada(self):
        coord = pyautogui.position(); dg = self.combo_dg.get()
        if not dg: return
        win = tk.Toplevel(self.root); win.title("Novo Passo"); win.geometry("280x420")
        win.attributes('-topmost', True); win.configure(bg=BG_PANEL)
        
        ttk.Label(win, text=f"X: {coord.x} | Y: {coord.y}").pack(pady=5)
        ttk.Label(win, text="Botão:").pack()
        btn_c = ttk.Combobox(win, values=["Direito", "Esquerdo"]); btn_c.set("Direito"); btn_c.pack()
        ttk.Label(win, text="Dashs (ex: 1, 2):").pack()
        ent_d = ttk.Entry(win); ent_d.pack()
        ttk.Label(win, text="Tempo de Ataque (s):").pack()
        ent_atq = ttk.Entry(win); ent_atq.insert(0, "0"); ent_atq.pack()
        
        v_z = tk.BooleanVar(); ttk.Checkbutton(win, text="Resetar Zoom?", variable=v_z).pack()
        v_b = tk.BooleanVar(); ttk.Checkbutton(win, text="É Boss?", variable=v_b).pack()
        v_l = tk.BooleanVar(); ttk.Checkbutton(win, text="Loot Final?", variable=v_l).pack()

        def salvar():
            if dg not in self.engine.dados["Dungeons"]: self.engine.dados["Dungeons"][dg] = {}
            num = len(self.engine.dados["Dungeons"][dg]) + 1
            self.engine.dados["Dungeons"][dg][f"passo{num}"] = {
                "coord": [coord.x, coord.y], "click_btn": btn_c.get(),
                "dashs": [int(x.strip()) for x in ent_d.get().split(",")] if ent_d.get() else [],
                "espera_pos": 2, "tempo_ataque": float(ent_atq.get() or 0),
                "is_boss": v_b.get(), "loot_final": v_l.get(), "reset_zoom": v_z.get()
            }
            salvar_dados(self.engine.dados); self.atualizar_lista_passos(); win.destroy()
        tk.Button(win, text="SALVAR (ENTER)", bg=ACCENT_GREEN, command=salvar).pack(pady=10)

    def iniciar_bot(self):
        if not self.engine.rodando:
            self.engine.dg_atual = self.combo_dg.get()
            if not self.engine.dg_atual: return
            try:
                self.engine.total_ciclos = int(self.ent_ciclos.get())
                self.engine.skills_usuario = self.ent_skills.get().split(",")
                self.engine.cast_global = float(self.ent_cast.get())
                self.engine.rodando = True
                threading.Thread(target=self.engine.thread_principal, daemon=True).start()
            except: pass

    def parar_bot(self):
        self.engine.rodando = False
        self.update_overlay("BOT PARADO")

if __name__ == "__main__":
    root = tk.Tk(); app = AppDG(root); root.mainloop()
