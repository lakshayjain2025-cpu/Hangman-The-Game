import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
import os, random, json, time
from math import ceil
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
    try:
        pygame.mixer.init()
    except Exception:
        PYGAME_AVAILABLE = False
except Exception:
    PYGAME_AVAILABLE = False

APP_TITLE = "Hangman - The Game"
WINDOW_MIN_W = 960
WINDOW_MIN_H = 680
DATA_DIR = os.path.join(os.path.expanduser("~"), ".hangman_app")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
CUSTOM_WORDS_FILE = os.path.join(DATA_DIR, "custom_words.json")

THEME = {
    "bg": "#EBDCB3",
    "panel": "#F7E8C3",
    "accent": "#6B4423",
    "text": "#2B1608",
    "muted": "#8A6B4A",
    "danger": "#912D2D",
    "button": "#EEDCC3",
}

MAX_LIVES = 7
FONT_BASE = ("Segoe UI", 12)
BIG_FONT = ("Cooper Black", 20, "bold")
TILE_FONT = ("Segoe UI", 28, "bold")

SOUND_CORRECT = "correct.wav"
SOUND_WRONG = "wrong.wav"
SOUND_WIN = "win.mp3"
SOUND_LOSE = "lose.mp3"
MUSIC_BG = "background.wav"

WORDS = {
    "Animals": ["elephant","giraffe","alligator","butterfly","kangaroo","hippopotamus","cheetah","dolphin","penguin","rhinoceros"],
    "Fruits": ["strawberry","pineapple","pomegranate","watermelon","blueberry","blackberry","raspberry","cantaloupe","mango","papaya"],
    "Countries": ["argentina","bangladesh","cameroon","denmark","ethiopia","finland","germany","hungary","indonesia","jamaica"],
    "Movies": ["inception","interstellar","gladiator","amelie","parasite","chinatown","godfather","shawshank","casablanca","alien"],
    "Tech": ["algorithm","datacenter","microprocessor","encryption","bandwidth","virtualization","blockchain","cryptography"],
    "Random": ["sunflower","lighthouse","rainbow","starlight","butterscotch","moonbeam","paperclip","notebook","zeppelin"]
}

def ensure_data_dir():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass


def load_stats():
    ensure_data_dir()
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"games_played":0,"wins":0,"losses":0,"best_streak":0,"current_streak":0}


def save_stats(s):
    ensure_data_dir()
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass


def load_custom_words():
    ensure_data_dir()
    try:
        if os.path.exists(CUSTOM_WORDS_FILE):
            with open(CUSTOM_WORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_custom_words(d):
    ensure_data_dir()
    try:
        with open(CUSTOM_WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass


def _sfx_play(path, volume=1.0):
    """Try to play a sound file; fall back to system bell. Do not call tkinter GUI from non-main threads."""
    if PYGAME_AVAILABLE and os.path.exists(path):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(max(0.0, min(1.0, volume)))
            s.play()
            return
        except Exception:
            pass

    try:
        root = tk._default_root
        if root:
            root.bell()
    except Exception:
        pass


def play_correct():
    p = os.path.join(os.path.dirname(__file__), SOUND_CORRECT)
    _sfx_play(p, 0.95)


def play_wrong():
    p = os.path.join(os.path.dirname(__file__), SOUND_WRONG)
    _sfx_play(p, 0.95)


def play_win():
    p = os.path.join(os.path.dirname(__file__), SOUND_WIN)
    _sfx_play(p, 0.95)


def play_lose():
    p = os.path.join(os.path.dirname(__file__), SOUND_LOSE)
    _sfx_play(p, 1.0)


def try_start_music():
    p = os.path.join(os.path.dirname(__file__), MUSIC_BG)
    if PYGAME_AVAILABLE and os.path.exists(p):
        try:
            pygame.mixer.music.load(p)
            pygame.mixer.music.set_volume(0.12)
            pygame.mixer.music.play(-1)
            return True
        except Exception:
            return False
    return False



class Hangman:
    def __init__(self, word, max_lives=MAX_LIVES):
        self.word = word.lower()
        self.max_lives = max_lives
        self.reset()

    def reset(self):
        self.guessed = set()
        self.wrong = set()
        self.remaining = set([c for c in self.word if c.isalpha()])
        self.lives = self.max_lives
        self.start_time = time.time()

    def guess(self,ch):
        ch = ch.lower()
        if not ch.isalpha() or len(ch)!=1: return False,"invalid"
        if ch in self.guessed or ch in self.wrong: return False,"already"
        if ch in self.word:
            self.guessed.add(ch)
            self.remaining.discard(ch)
            return True,"correct"
        else:
            self.wrong.add(ch)
            self.lives -= 1
            return False,"wrong"

    def reveal(self):
        opts = sorted(list(self.remaining))
        if not opts: return None
        c = random.choice(opts)
        self.guessed.add(c)
        self.remaining.discard(c)
        return c

    def is_won(self): return len(self.remaining)==0
    def is_lost(self): return self.lives<=0

    def get_masked(self):
        out=[]
        for ch in self.word:
            if not ch.isalpha(): out.append(ch)
            elif ch in self.guessed: out.append(ch)
            else: out.append("_")
        return " ".join(out)

    def elapsed(self): return time.time()-self.start_time

def _load_background_path():
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("background.jpg","background.png"):
        p = os.path.join(base,name)
        if os.path.exists(p): return p
    return None


def _generate_parchment_gradient(w,h):
    img = Image.new("RGB",(w,h), "#EBDCB3")
    draw = ImageDraw.Draw(img)
    top_color = (242,230,200)
    bottom_color = (220,200,160)
    for i in range(h):
        t = i / max(1,(h-1))
        r = int(top_color[0]*(1-t) + bottom_color[0]*t)
        g = int(top_color[1]*(1-t) + bottom_color[1]*t)
        b = int(top_color[2]*(1-t) + bottom_color[2]*t)
        draw.line([(0,i),(w,i)], fill=(r,g,b))
    for i in range(1,200):
        bbox = [-i,-i,w+i,h+i]
        alpha = int(6 * (i/200))
        draw.rectangle(bbox, outline=(200-alpha,180-alpha,150-alpha))
    return img


class HangmanCanvas(tk.Canvas):
    def __init__(self, master, theme, width=420, height=420, **kw):
        super().__init__(master, width=width, height=height, bg=theme["panel"], highlightthickness=0, **kw)
        self.theme = theme
        self.width = width; self.height = height
        self.stage = 0
        self._anim_job = None
        self.create_static()

    def create_static(self):
        self.delete("all")
        w,h = self.width,self.height
        pad = 12
        self.create_rectangle(pad,pad,w-pad,h-pad, fill="#F6E7C1", outline="")
        base_y = h-40
        self.create_polygon(28,base_y,78,base_y-20,118,base_y, fill="#8A5A2B", outline="")
        self.create_line(78,base_y-18,78,58, width=8, fill="#5A3A20", capstyle=tk.ROUND)
        self.create_line(78,58,w//2,58, width=6, fill="#5A3A20", capstyle=tk.ROUND)
        self.create_line(w//2,58,w//2,108, width=4, fill="#5A3A20", capstyle=tk.ROUND)
        self.create_text(w-110,28, text="HANGMAN", font=("Cooper Black",16), fill="#5A2E0C")

    def set_stage(self,s):
        try:
            s = int(s)
        except Exception:
            s = 0
        self.stage = max(0,min(s,MAX_LIVES))
        self.draw_parts()

    def draw_parts(self):
        self.delete("parts")
        w=self.width; cx=w//2; top=110; bob=3 if self.stage>0 else 0
        # rope
        self.create_line(cx,110,cx,top+10, width=2, fill="#7A5A3A", tags=("parts",))
        if self.stage>=1:
            self.create_oval(cx-28,top+12+bob,cx+28,top+68+bob, fill="#F1D7B0", outline="#6B4123", width=3, tags=("parts",))
            self.create_oval(cx-18,top+22+bob,cx-8,top+32+bob, fill="#6B4123", tags=("parts",))
            self.create_oval(cx+8,top+22+bob,cx+18,top+32+bob, fill="#6B4123", tags=("parts",))
        if self.stage>=2:
            self.create_line(cx,top+68+bob,cx,top+150+bob, width=6, fill="#6B4123", tags=("parts",))
        if self.stage>=3:
            self.create_line(cx,top+92+bob,cx-60,top+120+bob, width=5, capstyle=tk.ROUND, fill="#6B4123", tags=("parts",))
        if self.stage>=4:
            self.create_line(cx,top+92+bob,cx+60,top+120+bob, width=5, capstyle=tk.ROUND, fill="#6B4123", tags=("parts",))
        if self.stage>=5:
            self.create_line(cx,top+150+bob,cx-40,top+230+bob, width=5, capstyle=tk.ROUND, fill="#6B4123", tags=("parts",))
        if self.stage>=6:
            self.create_line(cx,top+150+bob,cx+40,top+230+bob, width=5, capstyle=tk.ROUND, fill="#6B4123", tags=("parts",))
        if self.stage>=7:
            self.create_arc(cx-12,top+42+bob,cx+12,top+62+bob, start=0, extent=180, style=tk.CHORD, tags=("parts",), outline="#912D2D", width=2)

    def animate(self):
        if self.stage<=0: return
        if self._anim_job: self.after_cancel(self._anim_job)
        self._anim_job = self.after(200, self.animate)

    def stop_animation(self):
        if self._anim_job: self.after_cancel(self._anim_job); self._anim_job=None

class ThemedModal:
    def __init__(self, parent, title="", minw=400, minh=140, bg="#F3E3C2"):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.configure(bg=bg)
        self.win.title(title or "Dialog")
        self.minw = minw; self.minh = minh
        self.parent.update_idletasks()
        px,py = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        pw,pH = self.parent.winfo_width(), self.parent.winfo_height()
        mw = self.minw; mh = self.minh
        mx = px + max(0,(pw - mw)//2)
        my = py + max(0,(pH - mh)//2)
        try:
            self.win.geometry(f"{mw}x{mh}+{mx}+{my}")
            self.win.resizable(False, False)
        except Exception:
            pass
        try: self.win.attributes("-alpha", 0.0)
        except Exception: pass

    def fade_in(self, duration=220):
        steps = 10
        delay = max(5, duration//steps)
        def step(i=0):
            try:
                a = (i/steps); self.win.attributes("-alpha", a)
            except Exception:
                pass
            if i<steps: self.win.after(delay, lambda: step(i+1))
        step()

    def center_and_resize(self):
        self.win.update_idletasks()
        w = self.win.winfo_reqwidth(); h = self.win.winfo_reqheight()
        w = max(w, self.minw); h = max(h, self.minh)
        px,py = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        pw,pH = self.parent.winfo_width(), self.parent.winfo_height()
        mx = px + max(0,(pw-w)//2); my = py + max(0,(pH-h)//2)
        try: self.win.geometry(f"{w}x{h}+{mx}+{my}")
        except Exception: pass

    def close(self):
        try: self.win.grab_release(); self.win.destroy()
        except Exception: pass

class HangmanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_MIN_W}x{WINDOW_MIN_H}")
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.protocol("WM_DELETE_WINDOW", self.on_quit_confirm)
        self.stats = load_stats()
        self.custom_words = load_custom_words()
        self.current_category = None; self.current_word = None; self.game = None
        self.keyboard_buttons = {}; self.guess_tiles_frame = None
        self.message_label = None; self.lives_label = None; self.hangman_canvas = None
        self._bg_label = None; self._bg_image = None
        self.create_styles(); self.build_ui()
        self.bind_all("<Key>", self.on_keypress)
        try:
            self.attributes("-alpha", 0.0); self.after(40, self.fade_in_root)
        except Exception:
            pass
        try_start_music()
        self.show_category_screen()
        self.bind("<Configure>", lambda e: self._ensure_background())

    def _ensure_background(self):
        path = _load_background_path()
        if path and PIL_AVAILABLE:
            try:
                img = Image.open(path).convert("RGB")
                w = max(self.winfo_width(), WINDOW_MIN_W); h = max(self.winfo_height(), WINDOW_MIN_H)
                img = img.resize((w,h), Image.LANCZOS)
                self._bg_image = ImageTk.PhotoImage(img)
                if not self._bg_label:
                    lbl = tk.Label(self, image=self._bg_image); lbl.place(x=0,y=0,relwidth=1,relheight=1); lbl.lower(); self._bg_label = lbl
                else:
                    self._bg_label.configure(image=self._bg_image); self._bg_label.lower()
                return
            except Exception:
                pass
        if PIL_AVAILABLE:
            try:
                w = max(self.winfo_width(), WINDOW_MIN_W); h = max(self.winfo_height(), WINDOW_MIN_H)
                img = _generate_parchment_gradient(w,h)
                self._bg_image = ImageTk.PhotoImage(img)
                if not self._bg_label:
                    lbl = tk.Label(self, image=self._bg_image); lbl.place(x=0,y=0,relwidth=1,relheight=1); lbl.lower(); self._bg_label = lbl
                else:
                    self._bg_label.configure(image=self._bg_image); self._bg_label.lower()
                return
            except Exception:
                pass
        try: self.configure(bg=THEME["bg"])
        except Exception: pass

    def fade_in_root(self):
        try:
            for i in range(0, 11):
                self.attributes("-alpha", i/10); self.update(); time.sleep(0.02)
            self.attributes("-alpha", 1.0)
        except Exception:
            pass

    def create_styles(self):
        try:
            s = ttk.Style(self); s.theme_use("clam")
        except Exception:
            pass

    def build_ui(self):
        self._ensure_background()
        topbar = tk.Frame(self, bg=THEME["panel"], padx=12, pady=8); topbar.pack(fill=tk.X, side=tk.TOP)
        title_lbl = tk.Label(topbar, text=APP_TITLE, font=("Cooper Black", 22), bg=THEME["panel"], fg=THEME["accent"]); title_lbl.pack(side=tk.LEFT)
        control_frame = tk.Frame(topbar, bg=THEME["panel"]); control_frame.pack(side=tk.RIGHT)
        stats_btn = ttk.Button(control_frame, text="Stats", command=self.show_stats_modal); stats_btn.pack(side=tk.LEFT, padx=6)
        help_btn = ttk.Button(control_frame, text="Help", command=self.show_help_modal); help_btn.pack(side=tk.LEFT, padx=6)
        quit_btn = ttk.Button(control_frame, text="Quit", command=self.on_quit_confirm); quit_btn.pack(side=tk.LEFT, padx=6)
        self.content = tk.Frame(self, bg=THEME["bg"], padx=12, pady=12); self.content.pack(fill=tk.BOTH, expand=True)

    def clear_content(self):
        for child in self.content.winfo_children(): child.destroy()

    def show_category_screen(self):
        self.clear_content()
        frame = tk.Frame(self.content, bg=THEME["bg"]); frame.pack(fill=tk.BOTH, expand=True)
        header = tk.Label(frame, text="Choose a Category", font=("Cooper Black", 30), bg=THEME["bg"], fg=THEME["text"]); header.pack(pady=18)
        cards = tk.Frame(frame, bg=THEME["bg"]); cards.pack(fill=tk.BOTH, expand=True)
        all_cats = sorted(list(WORDS.keys()) + list(self.custom_words.keys()))
        for i,cat in enumerate(all_cats):
            card = tk.Frame(cards, bg="#F3E3C2", bd=2, relief=tk.RIDGE, padx=12, pady=12)
            card.grid(row=i//2, column=i%2, padx=12, pady=12, sticky="nsew")
            cards.grid_columnconfigure(i%2, weight=1)
            lbl = tk.Label(card, text=cat, font=("Segoe UI", 16, "bold"), bg="#F3E3C2", fg=THEME["accent"]); lbl.pack(anchor=tk.W)
            count = len(WORDS.get(cat, [])) + len(self.custom_words.get(cat, []))
            desc = tk.Label(card, text=f"Words: {count}", font=FONT_BASE, bg="#F3E3C2", fg=THEME["muted"]); desc.pack(anchor=tk.W, pady=(6,6))
            play_btn = ttk.Button(card, text="Play", command=lambda c=cat: self.start_game(c)); play_btn.pack(side=tk.RIGHT)
        tools = tk.Frame(frame, bg=THEME["bg"]); tools.pack(fill=tk.X, pady=12)
        add_word_btn = ttk.Button(tools, text="Add Custom Word", command=self.add_custom_word); add_word_btn.pack(side=tk.LEFT, padx=6)
        import_btn = ttk.Button(tools, text="Import Word List (JSON)", command=self.import_word_list); import_btn.pack(side=tk.LEFT, padx=6)
        shuffle_btn = ttk.Button(tools, text="Surprise Me (Random)", command=self.random_category); shuffle_btn.pack(side=tk.LEFT, padx=6)

    def random_category(self):
        cats = list(WORDS.keys()) + list(self.custom_words.keys())
        if not cats:
            self.show_info_modal("No categories", "No categories available to choose from."); return
        self.start_game(random.choice(cats))

    def add_custom_word(self):
        cat = simpledialog.askstring("Category Name", "Enter category (new or existing):", parent=self)
        if not cat: return
        word = simpledialog.askstring("Word", "Enter a single word or phrase for the category:", parent=self)
        if not word: return
        cat = cat.strip(); word = word.strip().lower()
        if not cat or not word:
            self.show_info_modal("Invalid", "Category and word must be non-empty."); return
        if cat not in self.custom_words: self.custom_words[cat] = []
        self.custom_words[cat].append(word)
        save_custom_words(self.custom_words)
        self.show_info_modal("Saved", f"Added '{word}' to category '{cat}'.")
        self.show_category_screen()

    def import_word_list(self):
        path = filedialog.askopenfilename(title="Open word list (JSON)", filetypes=[("JSON files","*.json"),("All files","*")])
        if not path: return
        try:
            with open(path,"r",encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k,v in data.items():
                    if k not in self.custom_words: self.custom_words[k] = []
                    if isinstance(v, list):
                        self.custom_words[k].extend([str(x).lower() for x in v])
                save_custom_words(self.custom_words)
                self.show_info_modal("Imported", "Imported and merged word lists.")
                self.show_category_screen()
            else:
                self.show_info_modal("Invalid", "JSON must contain a dictionary of categories to lists of words.")
        except Exception as e:
            self.show_info_modal("Error", f"Failed to import: {e}")

    def start_game(self, category):
        self.current_category = category
        pool = list(WORDS.get(category, [])) + list(self.custom_words.get(category, []))
        if not pool:
            self.show_info_modal("Empty Category", "No words in this category. Add custom words first."); return
        self.current_word = random.choice(pool)
        self.game = Hangman(self.current_word, max_lives=MAX_LIVES)
        self.stats["games_played"] = self.stats.get("games_played",0) + 1
        save_stats(self.stats)
        self.show_game_screen()

    def show_game_screen(self):
        self.clear_content()
        frame = tk.Frame(self.content, bg=THEME["bg"]); frame.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(frame, bg=THEME["bg"], padx=8, pady=8); left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = tk.Frame(frame, bg=THEME["bg"], padx=8, pady=8, width=460); right.pack(side=tk.RIGHT, fill=tk.Y)
        self.hangman_canvas = HangmanCanvas(right, THEME, width=420, height=420); self.hangman_canvas.pack()
        # set stage based on wrong guesses
        self.hangman_canvas.set_stage(MAX_LIVES - self.game.lives)
        info_frame = tk.Frame(right, bg=THEME["bg"]); info_frame.pack(fill=tk.X, pady=(8,0))
        self.lives_label = tk.Label(info_frame, text=f"Lives: {self.game.lives}", font=BIG_FONT, bg=THEME["bg"], fg=THEME["danger"]); self.lives_label.pack(side=tk.LEFT, padx=(6,12))
        self.message_label = tk.Label(right, text="Good luck!", font=FONT_BASE, bg=THEME["bg"], fg=THEME["muted"]); self.message_label.pack(pady=(8,4))
        word_frame = tk.Frame(left, bg=THEME["bg"], pady=10); word_frame.pack(fill=tk.X)
        self.guess_tiles_frame = tk.Frame(word_frame, bg=THEME["bg"]); self.guess_tiles_frame.pack()
        self.render_tiles()
        keyboard_frame = tk.Frame(left, bg=THEME["bg"], pady=12); keyboard_frame.pack()
        rows = ["qwertyuiop","asdfghjkl","zxcvbnm"]
        self.keyboard_buttons = {}
        for row in rows:
            rf = tk.Frame(keyboard_frame, bg=THEME["bg"]); rf.pack()
            for ch in row:
                b = tk.Button(rf, text=ch.upper(), width=4, height=2, font=("Segoe UI",10,"bold"), command=lambda c=ch: self.press_key(c), bg=THEME["button"], activebackground="#F7E0B0")
                b.pack(side=tk.LEFT, padx=2, pady=2)
                b.bind("<Enter>", lambda e, btn=b: btn.configure(bg="#F3DCAF"))
                b.bind("<Leave>", lambda e, btn=b: btn.configure(bg=THEME["button"]))
                self.keyboard_buttons[ch] = b
        ctrl = tk.Frame(left, bg=THEME["bg"], pady=10); ctrl.pack(fill=tk.X)
        self.hint_btn = ttk.Button(ctrl, text="Hint (Reveal Letter)", command=self.use_hint); self.hint_btn.pack(side=tk.LEFT, padx=8)
        giveup_btn = ttk.Button(ctrl, text="Give Up", command=self.give_up); giveup_btn.pack(side=tk.LEFT, padx=8)
        back_btn = ttk.Button(ctrl, text="Back to Categories", command=self.show_category_screen); back_btn.pack(side=tk.RIGHT, padx=8)
        meta = tk.Label(left, text=f"Category: {self.current_category} — Length: {len(self.current_word)}", bg=THEME["bg"], fg=THEME["muted"], font=FONT_BASE); meta.pack(anchor=tk.W, pady=(6,0))
        self.hangman_canvas.animate(); self.update_ui()

    def render_tiles(self):
        for c in self.guess_tiles_frame.winfo_children(): c.destroy()
        for ch in self.game.word:
            f = tk.Frame(self.guess_tiles_frame, width=52, height=70, bg='#F7E0B0', bd=2, relief=tk.RIDGE)
            f.pack(side=tk.LEFT, padx=6); f.pack_propagate(False)
            display = ch.upper() if (not ch.isalpha() or ch in self.game.guessed) else ""
            lbl = tk.Label(f, text=display, font=TILE_FONT, bg='#F7E0B0', fg=THEME["text"])
            lbl.pack(expand=True)

    def update_tiles(self):
        for idx, frame in enumerate(self.guess_tiles_frame.winfo_children()):
            ch = self.game.word[idx]
            lbl = frame.winfo_children()[0]
            lbl.config(text=(ch.upper() if (not ch.isalpha() or ch in self.game.guessed) else ""))

    def update_ui(self):
        if not self.game: return
        self.update_tiles()
        self.lives_label.config(text=f"Lives: {self.game.lives}")
        self.hangman_canvas.set_stage(MAX_LIVES - self.game.lives)
        for ch, btn in self.keyboard_buttons.items():
            if ch in self.game.guessed or ch in self.game.wrong:
                btn.config(state=tk.DISABLED, relief=tk.SUNKEN)
            else:
                btn.config(state=tk.NORMAL, relief=tk.RAISED)
        if self.game.is_won():
            elapsed = int(self.game.elapsed()); self.message_label.config(text=f"You won in {elapsed} seconds! 🎉"); play_win(); self.hangman_canvas.stop_animation()
            self.stats["wins"] = self.stats.get("wins",0)+1; self.stats["current_streak"] = self.stats.get("current_streak",0)+1
            self.stats["best_streak"] = max(self.stats.get("best_streak",0), self.stats.get("current_streak",0)); save_stats(self.stats)
            for _,b in self.keyboard_buttons.items(): b.config(state=tk.DISABLED)
            self.after(240, lambda: self.show_play_again_modal(f"You Won! The word was: {self.game.word}"))
        elif self.game.is_lost():
            self.message_label.config(text=f"You lost — the word was: {self.game.word} 🙁"); play_lose(); self.hangman_canvas.stop_animation()
            self.stats["losses"] = self.stats.get("losses",0)+1; self.stats["current_streak"] = 0; save_stats(self.stats)
            for _,b in self.keyboard_buttons.items(): b.config(state=tk.DISABLED)
            self.after(300, lambda: self.show_play_again_modal(f"You Lost! The word was: {self.game.word}"))

    def press_key(self, ch):
        if not self.game: return
        ok, tag = self.game.guess(ch)
        if ok:
            self.message_label.config(text=f"Nice! '{ch.upper()}' is in the word."); play_correct()
        else:
            if tag == "already":
                self.message_label.config(text=f"You already tried '{ch.upper()}'")
            elif tag == "invalid":
                self.message_label.config(text="Invalid input.")
            else:
                self.message_label.config(text=f"Oops! '{ch.upper()}' is not in the word."); play_wrong()
        self.update_ui()

    def on_keypress(self, event):
        ch = (event.char or "").lower()
        if not ch or not ch.isalpha() or len(ch)!=1: return
        if not self.game: return
        if ch in self.game.guessed or ch in self.game.wrong: return
        self.press_key(ch)

    def use_hint(self):
        if not self.game: return
        ch = self.game.reveal()
        if ch is None:
            self.message_label.config(text="No hints available — all letters revealed.")
        else:
            self.message_label.config(text=f"Revealed letter: '{ch.upper()}'."); play_correct()
        self.update_ui()

    def give_up(self):
        if not self.game: return
        answer = self.game.word
        self.stats["losses"] = self.stats.get("losses",0)+1; self.stats["current_streak"] = 0; save_stats(self.stats)
        self.show_play_again_modal(f"You gave up! The word was: {answer}")

    def show_play_again_modal(self, message):
        modal = ThemedModal(self, title="Game Over", minw=520, minh=180, bg="#F3E3C2")
        panel = tk.Frame(modal.win, bg="#F3E3C2", bd=6, relief=tk.RIDGE); panel.pack(expand=True, fill=tk.BOTH)
        lbl = tk.Label(panel, text=message, font=("Segoe UI", 14, "bold"), bg="#F3E3C2", wraplength=480); lbl.pack(pady=(12,8), padx=8)
        btns = tk.Frame(panel, bg="#F3E3C2"); btns.pack(pady=8)
        def do_play(): modal.close(); self.reset_for_new_round()
        def do_cat(): modal.close(); self.show_category_screen()
        def do_quit(): modal.close(); self.on_quit_confirm()
        b1 = ttk.Button(btns, text="Play Again 🔄", command=do_play); b1.pack(side=tk.LEFT, padx=8)
        b2 = ttk.Button(btns, text="Choose Category 📚", command=do_cat); b2.pack(side=tk.LEFT, padx=8)
        b3 = ttk.Button(btns, text="Quit ❌", command=do_quit); b3.pack(side=tk.LEFT, padx=8)
        modal.center_and_resize(); modal.fade_in()

    def reset_for_new_round(self):
        if not self.current_category:
            self.show_category_screen(); return
        pool = list(WORDS.get(self.current_category, [])) + list(self.custom_words.get(self.current_category, []))
        if not pool:
            self.show_category_screen(); return
        new_word = random.choice(pool); tries=0
        while new_word==self.current_word and len(pool)>1 and tries<8:
            new_word=random.choice(pool); tries+=1
        self.current_word=new_word; self.game=Hangman(self.current_word, max_lives=MAX_LIVES); self.show_game_screen()

    def show_info_modal(self, title, message):
        modal = ThemedModal(self, title=title, minw=520, minh=160, bg="#F3E3C2")
        panel = tk.Frame(modal.win, bg="#F3E3C2", bd=6, relief=tk.RIDGE); panel.pack(expand=True, fill=tk.BOTH)
        lbl = tk.Label(panel, text=message, font=("Segoe UI", 13), bg="#F3E3C2", wraplength=480, justify=tk.LEFT); lbl.pack(pady=(12,8), padx=12)
        btn_frame = tk.Frame(panel, bg="#F3E3C2"); btn_frame.pack(pady=(6,12))
        ok_btn = ttk.Button(btn_frame, text="OK", command=modal.close); ok_btn.pack(side=tk.LEFT, padx=6)
        modal.center_and_resize()
        modal.win.update_idletasks()
        modal.center_and_resize()
        modal.fade_in()
        self.after(50, lambda: _sfx_play(os.path.join(os.path.dirname(__file__), SOUND_CORRECT), 0.3))

    def show_stats_modal(self):
        s = self.stats
        text = (f"Games played: {s.get('games_played',0)}\n"
                f"Wins: {s.get('wins',0)}\n"
                f"Losses: {s.get('losses',0)}\n"
                f"Best streak: {s.get('best_streak',0)}\n"
                f"Current streak: {s.get('current_streak',0)}")
        self.show_info_modal("Statistics", text)

    def show_help_modal(self):
        text = ("How to play:\n"
                "- Choose a category and start the game.\n"
                "- Guess letters using keyboard or on-screen keys.\n"
                "- You have limited lives (shown on the right).\n"
                "- Use Hint to reveal a letter (limited).\n"
                "- Add custom words via Categories.")
        self.show_info_modal("Help", text)

    def on_quit_confirm(self):
        modal = ThemedModal(self, title="Quit", minw=420, minh=140, bg="#F3E3C2")
        panel = tk.Frame(modal.win, bg="#F3E3C2", bd=6, relief=tk.RIDGE); panel.pack(expand=True, fill=tk.BOTH)
        lbl = tk.Label(panel, text="Are you sure you want to quit?", font=("Segoe UI",14,"bold"), bg="#F3E3C2"); lbl.pack(pady=(12,8))
        btns = tk.Frame(panel, bg="#F3E3C2"); btns.pack(pady=8)
        b1 = ttk.Button(btns, text="Quit", command=lambda: (modal.close(), save_stats(self.stats), self.destroy())); b1.pack(side=tk.LEFT, padx=6)
        b2 = ttk.Button(btns, text="Cancel", command=modal.close); b2.pack(side=tk.LEFT, padx=6)
        modal.center_and_resize(); modal.fade_in()

if __name__ == "__main__":
    if PYGAME_AVAILABLE:
        try:
            _bg = os.path.join(os.path.dirname(__file__), MUSIC_BG)
            if os.path.exists(_bg):
                pygame.mixer.music.load(_bg); pygame.mixer.music.set_volume(0.12); pygame.mixer.music.play(-1)
        except Exception:
            pass
    app = HangmanApp()
    app.mainloop()
