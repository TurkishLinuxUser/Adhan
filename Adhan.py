


import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from playsound import playsound
import threading
import json
import pystray
from PIL import Image
import sys
import signal
import os
import pygame


pygame.init()

home_dir = os.path.expanduser("~")
filename = f"{home_dir}/.local/share/adhan/settings.json"

try:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    default_settings = {
        "city": "Brussels",
        "country": "Belgium",
        "language": "EN",
        "azan": "Masjid al-Haram"
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(default_settings, f, ensure_ascii=False, indent=4)

with open(filename, 'r', encoding='utf-8') as f:
    data = json.load(f)
lng_value = data.get('language')
cityval = data.get('city')
coval = data.get('country')
azanval = data.get('azan')

class LanguageManager:
    def __init__(self, filename):
        self.current_language = lng_value 

        self.current_azan = azanval

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
        

    def switch_azan(self, azan_code):
        self.current_azan = azan_code

home_dir = os.path.expanduser("~")
lang_manager = LanguageManager(f"{home_dir}/.local/share/adhan/languages.json")







class EzanProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title(lang_manager.get_text("program_title"))
        self.root.geometry("400x300")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        home_dir = os.path.expanduser("~")
        self.settings_file = f"{home_dir}/.local/share/adhan/settings.json"

        
        
        home_dir = os.path.expanduser("~")
        self.image = Image.open(f"{home_dir}/.local/share/adhan/icons/icon512x512.png")
        self.menu = pystray.Menu (
            pystray.MenuItem("Show", lambda icon, item: self.show_window()),
            pystray.MenuItem("Quit", lambda icon, item: self.quit_program())
        )

        self.icon = pystray.Icon("EzanProgrami", self.image, "Adhan Times", self.menu)
        threading.Thread(target=self.icon.run, daemon=True).start()
        



        

        self.prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        self.prayer_times = {name: tk.StringVar() for name in self.prayer_names}
        self.prayer_triggered = {name: False for name in self.prayer_names}

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title(lang_manager.get_text("settings"))
        self.settings_window.geometry("330x200")
        self.settings_window.withdraw()

        self.language_var = tk.StringVar(self.settings_window)
        self.language_var.set(lang_manager.current_language)
        ttk.Label(self.settings_window, text=lang_manager.get_text("language") + ":").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.language_dropdown = ttk.Combobox(self.settings_window, textvariable=self.language_var, values=list(lang_manager.languages.keys()))
        self.language_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("city") + ":").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(self.settings_window, text=lang_manager.get_text("country") + ":").grid(row=3, column=0, padx=10, pady=5, sticky="w")

        

        self.azans = ["Ahmad Al Nafees", "Mishary Rashid Alafasy", "Dubai's One Tv", "Hafiz Mustafa Ozcan", "Masjid al-Haram"]
        self.azan_var = tk.StringVar(self.settings_window)
        self.azan_var.set(lang_manager.current_azan)
        ttk.Label(self.settings_window, text=lang_manager.get_text("select_azan") + ":").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.azan_dropdown = ttk.Combobox(self.settings_window, textvariable=self.azan_var, values=list(self.azans))
        self.azan_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        
        

        
        photo = tk.PhotoImage(file=f"{home_dir}/.local/share/adhan/icons/sound.png")  
        self.image_label = tk.Label(self.settings_window, image=photo)
        self.image_label.photo = photo  
        self.image_label.grid(row=0, column=2, pady=5)
        self.image_label.bind("<Button-1>", self.play_selected_azan)  


        




        self.city_var = tk.StringVar(self.settings_window)
        self.city_entry = tk.Entry(self.settings_window, textvariable=self.city_var)
        self.city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.country_var = tk.StringVar(self.settings_window)
        self.country_entry = tk.Entry(self.settings_window, textvariable=self.country_var)
        self.country_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ttk.Button(self.settings_window, text=lang_manager.get_text("save"), command=self.save_settings_and_close).grid(row=4, columnspan=2, pady=15, padx=10, sticky="ew")

        self.create_widgets()

        self.create_settings_widgets()

        self.load_saved_settings()

        self.update_prayer_times()

        self.check_time()


        self.current_sound_thread = None

        


    def play_selected_azan(self, event):
        selected_azan = self.azan_var.get()
        sound_file = f"{home_dir}/.local/share/adhan/azan/{selected_azan}.mp3"  
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error: {e}")     

        self.image_label.unbind("<Button-1>")  
        self.image_label.bind("<Button-1>", self.stop_selected_azan)   
        
            
        
        


    def stop_selected_azan(self, event):
        selected_azan = self.azan_var.get()
        sound_file = f"{home_dir}/.local/share/adhan/azan/{selected_azan}.mp3"  

        try:
            pygame.mixer.music.load(sound_file)
            if pygame.mixer.music.get_busy() and pygame.mixer.music.get_sound() == sound_file:
                pygame.mixer.music.stop()
        
        except Exception as e:
            print(f"Error: {e}")
        
        self.image_label.unbind("<Button-1>")  
        self.image_label.bind("<Button-1>", self.play_selected_azan)   

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ttk.Label(main_frame, text=lang_manager.get_text("program_title"), font=("Helvetica", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        for i, prayer_name in enumerate(self.prayer_names):
            ttk.Label(main_frame, text=lang_manager.get_text(prayer_name) + ":", font=("Helvetica", 12), anchor="w").grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            ttk.Label(main_frame, textvariable=self.prayer_times[prayer_name], font=("Helvetica", 12), anchor="w").grid(row=i+1, column=1, padx=10, pady=5, sticky="w")

        ttk.Button(main_frame, text=lang_manager.get_text("settings"), command=self.open_settings).grid(row=len(self.prayer_names)+2, column=0, columnspan=2, pady=10, sticky="w")
        ttk.Button(main_frame, text=lang_manager.get_text("stop_azan"), command=self.stop_ezan_sound).grid(row=len(self.prayer_names)+2, column=1, columnspan=2, pady=10, sticky="e")

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)



    def create_settings_widgets(self):

        self.settings_window.title(lang_manager.get_text("settings"))
        self.settings_window.geometry("330x190")
        self.settings_window.withdraw()


        for widget in self.settings_window.winfo_children():
            widget.destroy()

        ttk.Label(self.settings_window, text=lang_manager.get_text("language") + ":").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.language_dropdown = ttk.Combobox(self.settings_window, textvariable=self.language_var, values=list(lang_manager.languages.keys()))
        self.language_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("city") + ":").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.city_entry = tk.Entry(self.settings_window, textvariable=self.city_var)
        self.city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("country") + ":").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.country_entry = tk.Entry(self.settings_window, textvariable=self.country_var)
        self.country_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("select_azan") + ":").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.azan_dropdown = ttk.Combobox(self.settings_window, textvariable=self.azan_var, values=self.azans)
        self.azan_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        photo = tk.PhotoImage(file=f"{home_dir}/.local/share/adhan/icons/sound.png")
        
        self.image_label = ttk.Label(self.settings_window, image=photo)
        self.image_label.photo = photo
        self.image_label.grid(row=0, column=2, padx=6, pady=5, sticky="ew")
        self.image_label.bind("<Button-1>", self.play_selected_azan)

        ttk.Button(self.settings_window, text=lang_manager.get_text("save"), command=self.save_settings_and_close).grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.settings_window.grid_rowconfigure(0, weight=1)
        self.settings_window.grid_columnconfigure(1, weight=1)


    def open_settings(self):
        self.settings_window.deiconify()
        
    def save_settings_and_close(self):
        city = self.city_var.get().strip()
        country = self.country_var.get().strip()

        selected_azan = self.azan_var.get()
        selected_language = self.language_var.get()
        lang_manager.switch_language(selected_language)
        lang_manager.switch_azan(selected_azan)

        settings = {
            "city": city,
            "country": country,
            "language": selected_language,
            "azan": selected_azan
        }

        
        today = datetime.now().strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}&method=2"

        try:
            
            response = requests.get(url)
            response.raise_for_status()  

            
            lang_manager.save_settings(self.settings_file, settings)
            self.settings_window.withdraw()
            self.root.title(lang_manager.get_text("program_title"))
            self.create_widgets()

            self.create_settings_widgets()

            
            self.update_prayer_times(url)

        except requests.exceptions.RequestException as e:
            
            messagebox.showerror(lang_manager.get_text("program_title"), lang_manager.get_text("api-error"))

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

            
            self.root.after(3600000, self.update_prayer_times)

        except requests.exceptions.RequestException as e:
            print("API'den namaz saatleri alınamadı:", e)
            
            self.root.after(300000, self.update_prayer_times)

    def check_time(self):
        current_time = datetime.now().strftime("%H:%M")

        for prayer_name, time in self.prayer_times_data.items():
            if current_time == time and not self.prayer_triggered[prayer_name]:
                threading.Thread(target=self.play_ezan_sound).start()
                self.show_window()
                self.prayer_triggered[prayer_name] = True

        
        self.root.after(1000, self.check_time)


    def play_ezan_sound(self):
        if pygame.mixer.music.get_busy():
            return  

        
        adhan = f"{home_dir}/.local/share/adhan/azan/{azanval}.mp3"  
        pygame.mixer.music.load(adhan)
        pygame.mixer.music.play()

    
    def stop_ezan_sound(self):
        adhan = f"{home_dir}/.local/share/adhan/azan/{azanval}.mp3"  
        pygame.mixer.music.load(adhan)
        if pygame.mixer.music.get_busy() and pygame.mixer.music.get_sound() == adhan:
            pygame.mixer.music.stop()
            
            self.root.withdraw()


    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()

    def quit_program(self):
        
        self.root.quit()
        os.kill(os.getpid(), signal.SIGTERM)


def main():
    root = tk.Tk()
    ezan_programi = EzanProgrami(root)
    root.mainloop()

if __name__ == "__main__":
    main()

