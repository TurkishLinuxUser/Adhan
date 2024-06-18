import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from playsound import playsound
import threading
import json
import pystray
from PIL import Image
import os 

home_dir = os.path.expanduser("~")
filename = f"{home_dir}/.local/share/adhan/settings.json"


try:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    
    default_settings = {
        "city": "Brussels",
        "country": "Belgium",
        "language": "EN"
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(default_settings, f, ensure_ascii=False, indent=4)


with open(filename, 'r', encoding='utf-8') as f:
    data = json.load(f)
lng_value = data.get('language')
cityval = data.get('city')
coval = data.get('country')

class LanguageManager:
    def __init__(self, filename):
        self.current_language = lng_value 
        self.languages = {}
        self.load_languages(filename)

    def load_languages(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            self.languages = json.load(f)

    def get_text(self, key):
        if self.current_language in self.languages and key in self.languages[self.current_language]:
            return self.languages[self.current_language][key]
        else:
            return ""

    def switch_language(self, language_code):
        self.current_language = language_code

    def save_settings(self, filename, settings):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def load_settings(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings
        except FileNotFoundError:
            return None

home_dir = os.path.expanduser("~")
lang_manager = LanguageManager(f"{home_dir}/.local/share/adhan/languages.json")

class EzanProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title(lang_manager.get_text("program_title"))
        self.root.geometry("400x300")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        
        self.settings_file = "settings.json"

        
        self.prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        self.prayer_times = {name: tk.StringVar() for name in self.prayer_names}
        self.prayer_triggered = {name: False for name in self.prayer_names}  

        
        self.load_countries_and_cities()

        
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title(lang_manager.get_text("settings"))
        self.settings_window.withdraw()  

        
        self.language_var = tk.StringVar(self.settings_window)
        self.language_var.set(lang_manager.current_language)  
        ttk.Label(self.settings_window, text=lang_manager.get_text("language") + ":").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.language_dropdown = ttk.Combobox(self.settings_window, textvariable=self.language_var, values=list(lang_manager.languages.keys()))
        self.language_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("city") + ":").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(self.settings_window, text=lang_manager.get_text("country") + ":").grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.city_var = tk.StringVar(self.settings_window)
        self.city_entry = tk.Entry(self.settings_window, textvariable=self.city_var)
        self.city_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.country_var = tk.StringVar(self.settings_window)
        self.country_entry = tk.Entry(self.settings_window, textvariable=self.country_var)
        self.country_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ttk.Button(self.settings_window, text=lang_manager.get_text("save"), command=self.save_settings_and_close).grid(row=3, columnspan=2, pady=10)

        
        self.create_widgets()

        
        self.load_saved_settings()

        
        self.update_prayer_times()

        
        self.check_time()

    def load_countries_and_cities(self):
        
        with open('countries.json', 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        
        self.countries = list(countries_data.keys())
        self.cities = countries_data

    def create_widgets(self):
        
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")  

        
        ttk.Label(main_frame, text=lang_manager.get_text("program_title"), font=("Helvetica", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        
        for i, prayer_name in enumerate(self.prayer_names):
            ttk.Label(main_frame, text=lang_manager.get_text(prayer_name) + ":", font=("Helvetica", 12), anchor="w").grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            ttk.Label(main_frame, textvariable=self.prayer_times[prayer_name], font=("Helvetica", 12), anchor="w").grid(row=i+1, column=1, padx=10, pady=5, sticky="w")

        
        ttk.Button(main_frame, text=lang_manager.get_text("settings"), command=self.open_settings).grid(row=len(self.prayer_names)+1, column=0, columnspan=2, pady=10)

        
        main_frame.grid_rowconfigure(0, weight=1)  
        main_frame.grid_columnconfigure(0, weight=1) 
        self.root.grid_rowconfigure(0, weight=1) 
        self.root.grid_columnconfigure(0, weight=1) 

    def open_settings(self):
        self.settings_window.deiconify()  

    def save_settings_and_close(self):
        city = self.city_var.get().strip()  
        country = self.country_var.get().strip()  

        
        if country not in self.countries or city not in self.cities[country]:
            messagebox.showerror(lang_manager.get_text("program_title"), lang_manager.get_text("invalid_city_country"))
            return

        
        selected_language = self.language_var.get()
        lang_manager.switch_language(selected_language)

        
        settings = {
            "city": city,
            "country": country,
            "language": selected_language
        }
        lang_manager.save_settings(self.settings_file, settings)

        
        today = datetime.now().strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}&method=2"

        
        self.update_prayer_times(url)

        
        self.settings_window.withdraw()

        
        self.root.title(lang_manager.get_text("program_title"))
        self.create_widgets()

    def load_saved_settings(self):
        settings = lang_manager.load_settings(self.settings_file)
        if settings:
            self.city_var.set(settings["city"])
            self.country_var.set(settings["country"])
            self.language_var.set(settings["language"])

    def update_prayer_times(self, url=None):
        if not url:
            
            city = cityval
            country = coval
            url = f"https://api.aladhan.com/v1/timingsByCity/{datetime.now().strftime('%d-%m-%Y')}?city={city}&country={country}&method=2"

        try:
            response = requests.get(url)
            data = response.json()
            timings = data["data"]["timings"]

            
            prayer_times = {
                "fajr": timings["Fajr"],
                "dhuhr": timings["Dhuhr"],
                "asr": timings["Asr"],
                "maghrib": timings["Maghrib"],
                "isha": timings["Isha"]
            }

            
            for prayer_name in self.prayer_names:
                self.prayer_times[prayer_name].set(prayer_times[prayer_name])
                self.prayer_triggered[prayer_name] = False  

            
            self.prayer_times_data = prayer_times

        except requests.exceptions.RequestException as e:
            print("API'den namaz saatleri alınamadı:", e)

        
        self.root.after(30000, self.update_prayer_times) 

    def check_time(self):
        current_time = datetime.now().strftime("%H:%M")

        for prayer_name, time in self.prayer_times_data.items():
            if current_time == time and not self.prayer_triggered[prayer_name]:
                threading.Thread(target=playsound, args=("ezan_sesi.mp3",)).start()
                self.show_window()  
                self.prayer_triggered[prayer_name] = True  

        
        self.root.after(1000, self.check_time)  

    def hide_window(self):
        self.root.withdraw()  

    def show_window(self):
        self.root.deiconify()


def main():
    root = tk.Tk()
    ezan_programi = EzanProgrami(root)

    
    image = Image.open("icon128x128.png")
    menu = pystray.Menu(
        pystray.MenuItem(
            "Show", lambda icon, item: ezan_programi.show_window()
        ),
        pystray.MenuItem(
            "Quit", lambda icon, item: [icon.stop(), root.quit()]
        )
    )
    icon = pystray.Icon("EzanProgrami", image, "Ezan Programı", menu)

    
    threading.Thread(target=icon.run, daemon=True).start()

    
    root.mainloop()

if __name__ == "__main__":
    main()
