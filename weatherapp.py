import tkinter as tk
from tkinter import messagebox
import urllib.request
import urllib.parse
import json
import threading
import random
import math

# dark pixel palette
D = {
    "bg":      "#1a0a2e",
    "panel":   "#2d1b4e",
    "card":    "#3d2060",
    "border":  "#c77dff",
    "pink":    "#ff6eb4",
    "pink2":   "#ffb3d9",
    "lavender":"#c77dff",
    "yellow":  "#ffe66d",
    "white":   "#f8eeff",
    "text":    "#f8eeff",
    "subtext": "#c77dff",
    "shadow":  "#0d0520",
}

# this is for the colors for the pixel icons
WEATHER_ACCENTS = {
    "clear":        {"color": "#ffe66d", "desc_color": "#ffd000"},
    "clouds":       {"color": "#b0c4de", "desc_color": "#90aac8"},
    "rain":         {"color": "#89cff0", "desc_color": "#5bb8e8"},
    "thunderstorm": {"color": "#cc99ff", "desc_color": "#aa66ff"},
    "snow":         {"color": "#cce8ff", "desc_color": "#99ccff"},
    "mist":         {"color": "#d4b8e0", "desc_color": "#b899cc"},
    "default":      {"color": "#ff6eb4", "desc_color": "#c77dff"},
}

PIXEL_SPRITES = {
    "clear":        ["  ***  ", "*******", "*******", "*******", "  ***  "],
    "clouds":       [" ____  ", " )    )", " )    )", "(      ", " ----  "],
    "rain":         [" ____  ", "/    \\ ", "\\ ~~~ /", " \\__/ ", "/ / / /"],
    "thunderstorm": [" ____  ", "/    \\ ", "\\ ### /", " \\__/  ", "  /!/  "],
    "snow":         ["*  *  *", "  * *  ", "* * * *", "  * *  ", "*  *  *"],
    "mist":         ["~~~~~~~", "       ", "~~~~~~~", "       ", "~~~~~~~"],
    "default":      [" * * * ", "* * * *", " * * * ", "* * * *", " * * * "],
}

def wmo_to_condition(code):
    if code == 0:                               return "clear",        "Clear Sky!"
    elif code in (1, 2, 3):                     return "clouds",       "Partly Cloudy"
    elif code in (45, 48):                      return "mist",         "Misty~"
    elif code in (51,53,55,61,63,65,80,81,82):  return "rain",         "Rainy Day"
    elif code in (71,73,75,77,85,86):           return "snow",         "It's Snowing!"
    elif code in (95,96,99):                    return "thunderstorm", "Thunderstorm!!"
    else:                                       return "default",       "Unknown"


# ─button style
class PixelButton(tk.Canvas):
    def __init__(self, parent, text, command, **kwargs):
        w = kwargs.pop("width", 72)
        h = kwargs.pop("height", 40)
        super().__init__(parent, width=w, height=h,
                         bg=D["bg"], highlightthickness=0, cursor="hand2")
        self._text = text; self._cmd = command; self.w = w; self.h = h
        self._draw(False)
        self.bind("<ButtonPress-1>",   lambda e: self._draw(True))
        self.bind("<ButtonRelease-1>", lambda e: [self._draw(False), self._cmd()])

    def _draw(self, pressed):
        self.delete("all")
        o = 3 if pressed else 0
        s = 0 if pressed else 4
        self.create_rectangle(s, s, self.w-1+s, self.h-1+s,
                               fill=D["shadow"], outline="")
        self.create_rectangle(o, o, self.w-1, self.h-1,
                               fill=D["pink"], outline=D["lavender"], width=2)
        for x, y in [(o+2,o+2),(self.w-3,o+2),(o+2,self.h-3),(self.w-3,self.h-3)]:
            self.create_rectangle(x, y, x+2, y+2, fill=D["white"], outline="")
        self.create_text(self.w//2+o//2, self.h//2+o//2, text=self._text,
                          font=("Courier",11,"bold"), fill=D["white"])


# sprite
class SpriteCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, width=120, height=80,
                          highlightthickness=0, bg=D["card"], **kwargs)
        self._condition = "default"
        self._color = D["pink"]
        self._frame = 0
        self._animate()

    def set_condition(self, condition, color):
        self._condition = condition
        self._color = color

    def _animate(self):
        if not self.winfo_exists(): return
        self.delete("all")
        sprite = PIXEL_SPRITES.get(self._condition, PIXEL_SPRITES["default"])
        px   = 10
        cols = max(len(r) for r in sprite)
        ox   = (120 - cols*px)//2
        oy   = (80  - len(sprite)*px)//2 + int(math.sin(self._frame*0.15)*4)
        for r, row in enumerate(sprite):
            for c, ch in enumerate(row):
                if ch not in (' ', '\n'):
                    x0 = ox+c*px; y0 = oy+r*px
                    self.create_rectangle(x0, y0, x0+px-1, y0+px-1,
                                           fill=self._color, outline="")
        self._frame += 1
        self.after(80, self._animate)


# star field !!!
class StarField(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, bg=D["bg"], **kwargs)
        self._stars = []
        random.seed(7)
        for _ in range(55):
            self._stars.append({
                "x": random.randint(0,480), "y": random.randint(0,640),
                "r": random.choice([1,1,2]), "phase": random.uniform(0,6.28)
            })
        self._twinkle()

    def _twinkle(self):
        if not self.winfo_exists(): return
        self.delete("star")
        for s in self._stars:
            s["phase"] += 0.05
            b = int((math.sin(s["phase"])+1)/2 * 95 + 160)
            col = f"#{b:02x}{int(b*0.7):02x}{min(255,b+40):02x}"
            self.create_oval(s["x"]-s["r"], s["y"]-s["r"],
                              s["x"]+s["r"], s["y"]+s["r"],
                              fill=col, outline="", tags="star")
        self.after(60, self._twinkle)


# main app
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("* Weatherly *")
        self.geometry("480x640")
        self.resizable(False, False)
        self.configure(bg=D["bg"])
        self._build_ui()

    def _build_ui(self):
        self.star_layer = StarField(self, width=480, height=640)
        self.star_layer.place(x=0, y=0)

        title_frame = tk.Frame(self, bg=D["bg"])
        title_frame.place(x=0, y=12, width=480)
        tk.Label(title_frame, text="* WEATHERLY *",
                  font=("Courier",22,"bold"),
                  bg=D["bg"], fg=D["pink"]).pack()
        tk.Label(title_frame, text="~ pixelated weather ~",
                  font=("Courier",9),
                  bg=D["bg"], fg=D["subtext"]).pack()

        # divider
        div_top = tk.Canvas(self, width=420, height=8,
                             bg=D["bg"], highlightthickness=0)
        div_top.place(x=30, y=72)
        self._draw_divider(div_top, D["pink"], D["lavender"])

        # searching cities
        search_bg = tk.Frame(self, bg=D["panel"],
                              highlightbackground=D["border"],
                              highlightthickness=2)
        search_bg.place(x=30, y=88, width=420, height=46)

        self.city_var = tk.StringVar()
        self.entry = tk.Entry(search_bg, textvariable=self.city_var,
                               font=("Courier",13,"bold"), relief="flat",
                               bg=D["panel"], fg=D["pink2"],
                               insertbackground=D["pink"], bd=0)
        self.entry.pack(side="left", fill="both", expand=True, ipady=8, padx=(12,0))
        self.entry.bind("<Return>", lambda e: self._fetch())

        PixelButton(search_bg, text="GO!", command=self._fetch,
                    width=72, height=40).pack(side="right", padx=4, pady=2)

        # card
        card_outer = tk.Frame(self, bg=D["border"])
        card_outer.place(x=28, y=148, width=424, height=426)

        self.card = tk.Frame(card_outer, bg=D["card"])
        self.card.place(x=3, y=3, width=418, height=420)

        # more decor
        self.corner_cv = tk.Canvas(self.card, width=418, height=420,
                                    bg=D["card"], highlightthickness=0)
        self.corner_cv.place(x=0, y=0)
        self._draw_corners()

        # sprite
        self.sprite = SpriteCanvas(self.card)
        self.sprite.place(x=149, y=14)

        # city
        self.city_lbl = tk.Label(self.card, text="- - -",
                                  font=("Courier",22,"bold"),
                                  bg=D["card"], fg=D["white"])
        self.city_lbl.place(x=0, y=106, width=418)

        # country
        self.country_lbl = tk.Label(self.card, text="",
                                     font=("Courier",10),
                                     bg=D["card"], fg=D["subtext"])
        self.country_lbl.place(x=0, y=133, width=418)

        # Temp — color changes with weather
        self.temp_lbl = tk.Label(self.card, text="--*C",
                                  font=("Courier",44,"bold"),
                                  bg=D["card"], fg=D["pink"])
        self.temp_lbl.place(x=0, y=150, width=418)

        self.desc_lbl = tk.Label(self.card, text="[ enter a city! ]",
                                  font=("Courier",12,"italic"),
                                  bg=D["card"], fg=D["lavender"])
        self.desc_lbl.place(x=0, y=208, width=418)

        self.div_card = tk.Canvas(self.card, width=360, height=6,
                                   bg=D["card"], highlightthickness=0)
        self.div_card.place(x=29, y=240)
        self._draw_divider(self.div_card, D["pink"], D["lavender"])

        # details
        self.details_frame = tk.Frame(self.card, bg=D["card"])
        self.details_frame.place(x=10, y=254, width=398, height=120)
        self._make_details(D["pink"], D["lavender"], "--", "--", "--")

        # footer, status
        self.status_lbl = tk.Label(self, text="",
                                    font=("Courier",10),
                                    bg=D["bg"], fg=D["pink2"])
        self.status_lbl.place(x=0, y=582, width=480)

        tk.Label(self, text="* powered by open-meteo *",
                  font=("Courier",8),
                  bg=D["bg"], fg=D["panel"]).place(x=0, y=608, width=480)

    # helpers
    def _draw_divider(self, canvas, col_a, col_b):
        canvas.delete("all")
        for i in range(0, int(canvas["width"]), 8):
            canvas.create_rectangle(i, 0, i+6, 6,
                                     fill=(col_a if (i//8)%2==0 else col_b),
                                     outline="")

    def _draw_corners(self):
        c = self.corner_cv; c.delete("corners")
        W, H, sz = 418, 420, 12
        for x1,y1,x2,y2 in [(0,0,sz,sz),(W-sz,0,W,sz),(0,H-sz,sz,H),(W-sz,H-sz,W,H)]:
            c.create_rectangle(x1,y1,x2,y2, fill=D["border"], outline="", tags="corners")
        for x1,y1,x2,y2 in [(4,4,8,8),(W-8,4,W-4,8),(4,H-8,8,H-4),(W-8,H-8,W-4,H-4)]:
            c.create_rectangle(x1,y1,x2,y2, fill=D["card"],   outline="", tags="corners")

    def _make_details(self, accent, border, humidity, wind, feels):
        for w in self.details_frame.winfo_children():
            w.destroy()
        for label, val, unit in [("HUM",humidity,"%"),("WND",wind,"km/h"),("FEL",feels,"*C")]:
            col = tk.Frame(self.details_frame, bg=D["card"],
                            highlightbackground=border, highlightthickness=1)
            col.pack(side="left", expand=True, fill="both", padx=6, pady=4)
            tk.Label(col, text=label, font=("Courier",9,"bold"),
                     bg=D["card"], fg=D["subtext"]).pack(pady=(8,0))
            v = val if val == "--" else f"{val}{unit}"
            tk.Label(col, text=v, font=("Courier",15,"bold"),
                     bg=D["card"], fg=accent).pack()
            tk.Label(col, text="", font=("Courier",8),
                     bg=D["card"], fg=D["subtext"]).pack(pady=(0,8))

    # fetch
    def _fetch(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("oops!", "type a city name first! (>_<)")
            return
        self.status_lbl.configure(text="fetching weather... *  *  *")
        threading.Thread(target=self._api_call, args=(city,), daemon=True).start()

    def _api_call(self, city):
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
            with urllib.request.urlopen(geo_url, timeout=8) as r:
                geo = json.loads(r.read())
            if not geo.get("results"):
                self.after(0, self._show_error, f"'{city}' not found! (>_<)\ntry checking the spelling~")
                return
            res = geo["results"][0]
            lat, lon = res["latitude"], res["longitude"]
            wx_url = (f"https://api.open-meteo.com/v1/forecast?"
                      f"latitude={lat}&longitude={lon}"
                      f"&current=temperature_2m,apparent_temperature,weathercode,"
                      f"windspeed_10m,relativehumidity_2m&windspeed_unit=kmh")
            with urllib.request.urlopen(wx_url, timeout=8) as r:
                wx = json.loads(r.read())
            cur = wx["current"]
            self.after(0, self._display, {
                "city": res["name"], "country": res.get("country",""),
                "temp":  round(cur["temperature_2m"]),
                "feels": round(cur["apparent_temperature"]),
                "humidity": cur["relativehumidity_2m"],
                "wind":  round(cur["windspeed_10m"],1),
                "code":  cur["weathercode"],
            })
        except Exception as ex:
            self.after(0, self._show_error, f"connection error! (>_<)\n{ex}")

    def _display(self, d):
        self.status_lbl.configure(text="")
        condition, desc = wmo_to_condition(d["code"])
        accent = WEATHER_ACCENTS.get(condition, WEATHER_ACCENTS["default"])

        
        self.sprite.set_condition(condition, accent["color"])
        self.temp_lbl.configure(text=f"{d['temp']}*C", fg=accent["color"])
        self.desc_lbl.configure(text=f"[ {desc} ]", fg=accent["desc_color"])
        self._draw_divider(self.div_card, accent["color"], accent["desc_color"])
        self.city_lbl.configure(text=d["city"].upper())
        self.country_lbl.configure(text=f"~ {d['country']} ~")
        self._make_details(accent["color"], accent["desc_color"],
                            str(d["humidity"]), str(d["wind"]), str(d["feels"]))

    def _show_error(self, msg):
        self.status_lbl.configure(text="")
        messagebox.showerror("oh no! (>_<)", msg)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
