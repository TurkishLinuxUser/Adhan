import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Scrollbar
import requests
from datetime import datetime
import threading
import json
import logging
import pystray
from PIL import Image, ImageTk, ImageFilter
import sys
import signal
import shutil
import os
import pygame
import atexit
import tempfile

def check_if_running(pid_file):
    if os.path.isfile(pid_file):
        print(f"Another instance is already running. {pid_file}.")
        sys.exit(1)
    else:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

def remove_pid_file(pid_file):
    if os.path.isfile(pid_file):
        os.remove(pid_file)


program_data_dir = os.path.join(os.getenv('APPDATA'), 'Adhan')
if not os.path.exists(program_data_dir):
    os.makedirs(program_data_dir)

pid_file = os.path.join(program_data_dir, 'adhan.pid')

check_if_running(pid_file)

atexit.register(remove_pid_file, pid_file)


pygame.init()

filename = os.path.join(program_data_dir, "settings.json")

try:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    default_settings = {
        "city": "Brussels",
        "country": "Belgium",
        "language": "EN",
        "azan": "Masjid al-Haram",
        "font": "fonts/Roboto-Regular.ttf"
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(default_settings, f, ensure_ascii=False, indent=4)


def getvalues():
    global lng_value, cityval, coval, azanval, pfont
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lng_value = data.get('language')
    cityval = data.get('city')
    coval = data.get('country')
    azanval = data.get('azan')
    pfont = data.get('font')

getvalues()


class Log:
    def __init__(self, logfilename=f'{os.path.join(program_data_dir, "adhan.log")}'):
        self.filename = logfilename
        self._initialize_logging()

    def _initialize_logging(self):
        logging.basicConfig(filename=self.filename, level=logging.INFO)

    def write_to_log(self, message):
        logging.info(message)

    def find_in_log(self, keyword):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                for line in file:
                    if keyword in line:
                        return line.strip()
        return None

    def append_to_log(self, message):
        with open(self.filename, 'a') as file:
            file.write(message + '\n')

    def create_log_file(self):
        if not os.path.exists(self.filename):
            open(self.filename, 'w').close()



class WelcomeWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Welcome!")
        self.root.geometry("500x200")

        self.current_page = 0
        self.pages = [
            "Welcome! Before we continue, there are some things you need to know.",
            """Since I made this program by myself, there may be some problems and omissions. If you encounter any problems, please send us an e-mail with details. If there is a feature you would like to see in the program, don't hesitate to let us know! 
            
Mail: turkishlinuxuser@outlook.com""",
            "If there is an error, you can review the adhan.log file in the program directory. This will most likely help to resolve your error.",
            "Enter the name of your City and Country in English in the Settings so that the program can correctly pull data from the API.",
            "Finally, if you are willing to translate the program into other languages, please contact us: turkishlinuxuser@outlook.com"
        ]

        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self.root, text="", wraplength=460, justify=tk.CENTER)
        self.label.pack(pady=20, padx=20, anchor=tk.CENTER)


        self.update_text(self.pages[self.current_page])

        if self.current_page < len(self.pages) - 1:
            self.next_button = tk.Button(self.root, text="Next", command=self.show_next_page)
            self.next_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    def update_text(self, text):
        self.label.config(text=text, anchor='center')

    def show_next_page(self):
        self.current_page += 1
        self.update_text(self.pages[self.current_page])

        if self.current_page == len(self.pages) - 1:
            self.next_button.config(text="Finish", command=self.finish_welcome)

    def finish_welcome(self):
        self.root.destroy()




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

lang_manager = LanguageManager(f"{os.path.join(program_data_dir, "languages.json")}")




class EzanProgrami:
    def __init__(self, root):
        self.log = Log()
        self.root = root
        self.root.title(lang_manager.get_text("program_title"))
        self.root.geometry("400x300")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)


        self.settings_file = f'{os.path.join(program_data_dir, "settings.json")}'
        
        self.image = Image.open(f"{os.path.join(program_data_dir, "icons/icon512x512.png")}")
        self.menu = pystray.Menu (
            pystray.MenuItem("Show", lambda icon, item: self.show_window()),
            pystray.MenuItem("Quit", lambda icon, item: self.quit_program())
        )

        self.icon = pystray.Icon("EzanProgrami", self.image, "Adhan Times", self.menu)
        threading.Thread(target=self.icon.run, daemon=True).start()
        

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title(lang_manager.get_text("settings"))
        self.settings_window.protocol("WM_DELETE_WINDOW", self.hide_settings_window)
        self.settings_window.geometry("330x200")
        self.settings_window.withdraw()

        self.language_var = tk.StringVar(self.settings_window)
        self.language_var.set(lang_manager.current_language)
        ttk.Label(self.settings_window, text=lang_manager.get_text("language") + ":").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.language_dropdown = ttk.Combobox(self.settings_window, textvariable=self.language_var, values=list(lang_manager.languages.keys()))
        self.language_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, text=lang_manager.get_text("city") + ":").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(self.settings_window, text=lang_manager.get_text("country") + ":").grid(row=3, column=0, padx=10, pady=5, sticky="w")

        
        self.get_azan_list()

        
        
        self.azan_var = tk.StringVar(self.settings_window)
        self.azan_var.set(lang_manager.current_azan)
        ttk.Label(self.settings_window, text=lang_manager.get_text("select_azan") + ":").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.azan_dropdown = ttk.Combobox(self.settings_window, textvariable=self.azan_var, values=list(self.azans))
        self.azan_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        
        

        
        photo = tk.PhotoImage(file=f"{os.path.join(program_data_dir, "icons/sound.png")}")  
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

        
        self.prayer_times_data = {}
        self.prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        self.prayer_times = {name: tk.StringVar() for name in self.prayer_names}
        
        self.prayer_triggered = {name: False for name in self.prayer_names}
        
        
        

        self.check_and_update_json_file()

        self.create_widgets()

        self.create_settings_widgets()

        self.load_saved_settings()

        self.check_and_delete_old_json_files()
        
        self.current_date_is()

        self.check_time()
        
        self.run()

        self.check_and_update_log()



        self.current_sound_thread = None

    
    

    def current_date_is(self):
        global datetimenow
        datetimenow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.root.after(1000, self.current_date_is)

    def run(self):
        self.check_and_update_log()  

    def check_and_update_log(self):
        self.log.create_log_file()  
        
        if not self.log.find_in_log('started'):
            self.show_welcome_message()  


    def show_welcome_message(self):
        welcome_wizard = WelcomeWizard()
        self.log.write_to_log('started')  
        welcome_wizard.root.mainloop()


    
    def get_azan_list(self):
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        if not os.path.exists(azan_dir):
            os.makedirs(azan_dir)
        self.azans = [os.path.splitext(f)[0] for f in os.listdir(azan_dir) if f.endswith('.mp3')]
        return self.azans
    
    def add_new_azan(self, event):
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            file_name = os.path.basename(file_path)
            shutil.copy(file_path, os.path.join(azan_dir, file_name))
            self.azan_dropdown['values'] = self.get_azan_list()
            self.azan_var.set(os.path.splitext(file_name)[0])


    def update_azan_list(self):
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        self.azans = [f.split(".mp3")[0] for f in os.listdir(azan_dir) if f.endswith(".mp3")]
        self.azan_dropdown['values'] = self.azans

    def delete_azan(self, event):
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        selected_azan = self.azan_var.get()
        delete_azan_path = f"{os.path.join(azan_dir, selected_azan)}.mp3"
        want_to_delete_azan_text = lang_manager.get_text("want_to_delete_azan").format(selected_azan=selected_azan)
        azan_deleted_text = lang_manager.get_text("azan_deleted").format(selected_azan=selected_azan)
        azan_not_found_text = lang_manager.get_text("azan_not_found").format(selected_azan=selected_azan)
        error_occured_while_text = lang_manager.get_text("error_occured_while")
        select_azan_to_text = lang_manager.get_text("select_azan_to")


        if not selected_azan:
            messagebox.showwarning(lang_manager.get_text("warning"), select_azan_to_text)
            return

        
        answer = messagebox.askyesno(lang_manager.get_text("delete_azan"), want_to_delete_azan_text)

        if answer:
            try:
                os.remove(delete_azan_path)
                messagebox.showinfo(lang_manager.get_text("success"), azan_deleted_text)
                
                self.update_azan_list()
                self.azan_var.set(self.azans[0])
            except FileNotFoundError as e:
                messagebox.showerror(lang_manager.get_text("error"), azan_not_found_text)
                self.log.write_to_log(f"{datetimenow}  - {str(e)}")
            except Exception as e:
                messagebox.showerror(lang_manager.get_text("error"), f"{error_occured_while_text}: {str(e)}")
                self.log.write_to_log(f"{datetimenow}  - {str(e)}")

    def play_selected_azan(self, event):
        selected_azan = self.azan_var.get()
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        sound_file = f"{os.path.join(azan_dir, selected_azan)}.mp3"  
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except Exception as e:
            self.log.write_to_log(f"{datetimenow}  - {str(e)}")  

        self.image_label.unbind("<Button-1>")  
        self.image_label.bind("<Button-1>", self.stop_selected_azan)   
        
            
        
        


    def stop_selected_azan(self, event):
        selected_azan = self.azan_var.get()
        azan_dir = f"{os.path.join(program_data_dir, "azan")}"
        sound_file = f"{os.path.join(azan_dir, selected_azan)}.mp3"  

        try:
            pygame.mixer.music.load(sound_file)
            if pygame.mixer.music.get_busy() and pygame.mixer.music.get_sound() == sound_file:
                pygame.mixer.music.stop()
        
        except Exception as e:
            self.log.write_to_log(f"{datetimenow}  - {str(e)}")

        self.image_label.unbind("<Button-1>")  
        self.image_label.bind("<Button-1>", self.play_selected_azan)   

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        
        
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ttk.Label(main_frame, text=lang_manager.get_text("program_title"), font=(f"{pfont}", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        for i, prayer_name in enumerate(self.prayer_names):
            ttk.Label(main_frame, text=lang_manager.get_text(prayer_name) + ":", font=(f"{pfont}", 12), anchor="w").grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            ttk.Label(main_frame, textvariable=self.prayer_times[prayer_name], font=(f"{pfont}", 12), anchor="e").grid(row=i+1, column=1, padx=10, pady=5, sticky="e")

        ttk.Button(main_frame, text=lang_manager.get_text("settings"), command=self.open_settings).grid(row=len(self.prayer_names)+2, column=0, columnspan=2, pady=10, sticky="w")
        ttk.Button(main_frame, text=lang_manager.get_text("stop_azan"), command=self.stop_ezan_sound).grid(row=len(self.prayer_names)+2, column=1, columnspan=2, pady=10, sticky="e")


        print(self.prayer_times[prayer_name])
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)


    def create_settings_widgets(self):

        self.settings_window.title(lang_manager.get_text("settings"))
        self.settings_window.geometry("430x190")
        self.settings_window.withdraw()


        for widget in self.settings_window.winfo_children():
            widget.destroy()

        ttk.Label(self.settings_window, text=lang_manager.get_text("language") + ":", font=(f"{pfont}", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.language_dropdown = ttk.Combobox(self.settings_window, textvariable=self.language_var, values=list(lang_manager.languages.keys()))
        self.language_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, font=(f"{pfont}", 12), text=lang_manager.get_text("city") + ":").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.city_entry = tk.Entry(self.settings_window, textvariable=self.city_var)
        self.city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, font=(f"{pfont}", 12), text=lang_manager.get_text("country") + ":").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.country_entry = tk.Entry(self.settings_window, textvariable=self.country_var)
        self.country_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(self.settings_window, font=(f"{pfont}", 12), text=lang_manager.get_text("select_azan") + ":").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.azan_dropdown = ttk.Combobox(self.settings_window, textvariable=self.azan_var, values=self.azans)
        self.azan_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")


        photo = tk.PhotoImage(file=f"{os.path.join(program_data_dir, "icons/sound.png")}")
        
        self.image_label = ttk.Label(self.settings_window, image=photo)
        self.image_label.photo = photo
        self.image_label.grid(row=0, column=2, padx=6, pady=5, sticky="ew")
        self.image_label.bind("<Button-1>", self.play_selected_azan)



        
        arti_photo = tk.PhotoImage(file=f"{os.path.join(program_data_dir, "icons/arti.png")}")
        self.arti_image_label = ttk.Label(self.settings_window, image=arti_photo)
        self.arti_image_label.photo = arti_photo
        self.arti_image_label.grid(row=0, column=3, padx=6, pady=5, sticky="ew")
        self.arti_image_label.bind("<Button-1>", self.add_new_azan)




        
        trash_photo = tk.PhotoImage(file=f"{os.path.join(program_data_dir, "icons/trash.png")}")
        self.trash_image_label = ttk.Label(self.settings_window, image=trash_photo)
        self.trash_image_label.photo = trash_photo
        self.trash_image_label.grid(row=0, column=4, padx=6, pady=5, sticky="ew")
        self.trash_image_label.bind("<Button-1>", self.delete_azan)

        ttk.Button(self.settings_window, text=lang_manager.get_text("save"), command=self.save_settings_and_close).grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.settings_window.grid_rowconfigure(0, weight=1)
        self.settings_window.grid_columnconfigure(1, weight=1)





    def open_settings(self):
        if self.settings_window:
            self.settings_window.deiconify()
        
    def save_settings_and_close(self):
        city = self.city_var.get().strip()
        country = self.country_var.get().strip()

        selected_azan = self.azan_var.get()
        selected_language = self.language_var.get()
        lang_manager.switch_language(selected_language)
        lang_manager.switch_azan(selected_azan)
        
        current_settings = lang_manager.load_settings(self.settings_file)

        if current_settings and (current_settings["city"] != city or current_settings["country"] != country):
            file_name1 = f"prayer_times_{datetime.now().strftime('%Y-%m-%d')}.json"
            file_name = os.path.join(program_data_dir, file_name1)
            if os.path.exists(file_name):
                os.remove(file_name)

        settings = {
            "city": city,
            "country": country,
            "language": selected_language,
            "azan": selected_azan
        }

        try:
            lang_manager.save_settings(self.settings_file, settings)

            self.load_saved_settings()
            
            self.settings_window.withdraw()

            
            self.root.title(lang_manager.get_text("program_title"))
            self.create_widgets()
            self.create_settings_widgets()

            
            self.update_prayer_times()
        
            

            

        except requests.exceptions.RequestException as e:
            messagebox.showerror(lang_manager.get_text("program_title"), lang_manager.get_text("api-error"))
            self.log.write_to_log(f"{datetimenow}  - {str(e)}")

    def load_saved_settings(self):
        getvalues()
        settings = lang_manager.load_settings(self.settings_file)
        if settings:
            self.city_var.set(settings["city"])
            self.country_var.set(settings["country"])
            self.language_var.set(settings["language"])



    def update_prayer_times(self, url=None):
        file_name1 = f"prayer_times_{datetime.now().strftime('%Y-%m-%d')}.json"
        file_name = os.path.join(program_data_dir, file_name1)

        if not url:
            try:
                city = cityval
                country = coval
                udate = datetime.now().strftime('%d-%m-%Y')
                url = f"https://api.aladhan.com/v1/timingsByCity/{udate}?city={city}&country={country}&method=2"
                print(city)
                print(country)
                print(url)
            except Exception as e:
                messagebox.showerror(lang_manager.get_text('error'), lang_manager.get_text('response_error'))
                self.log.write_to_log(f"{datetimenow}  - {str(e)}")

        if os.path.exists(file_name):
            
            with open(file_name, 'r') as file:
                prayer_times = json.load(file)

            for prayer_name in self.prayer_names:
                self.prayer_times[prayer_name].set(prayer_times[prayer_name])
                self.prayer_times_data[prayer_name] = prayer_times[prayer_name]
                self.prayer_triggered[prayer_name] = False
                self.create_widgets()

        else:
            try:
                
                response = requests.get(url)
                response.raise_for_status()
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
                    self.prayer_times_data[prayer_name] = prayer_times[prayer_name]
                    self.prayer_triggered[prayer_name] = False

                with open(file_name, 'w') as file:
                    json.dump(prayer_times, file)

                self.create_widgets()

            except requests.exceptions.RequestException as e:
                messagebox.showerror(lang_manager.get_text('error'), lang_manager.get_text('api-error'))
                self.log.write_to_log(f"{datetimenow}  - {str(e)}")
            
            except Exception as e:
                messagebox.showerror(lang_manager.get_text('error'), lang_manager.get_text('response_error'))
                self.log.write_to_log(f"{datetimenow}  - {str(e)}")

                self.root.after(600000, self.update_prayer_times)

        self.root.after(3600000, self.update_prayer_times)



    def check_and_delete_old_json_files(self):
        
        directory = f"{program_data_dir}"

        current_date = datetime.now().strftime('%Y-%m-%d')

        
        files = os.listdir(directory)

        for file in files:
            if file.startswith("prayer_times_") and file.endswith(".json"):
                
                file_date = file.split("_")[2].split(".")[0]

                
                file_datetime = datetime.strptime(file_date, '%Y-%m-%d')

                
                if file_datetime.date() != datetime.now().date():
                    os.remove(os.path.join(directory, file))




    def check_and_update_json_file(self):
        
        file_name1 = f"prayer_times_{datetime.now().strftime('%Y-%m-%d')}.json"
        file_name = os.path.join(program_data_dir, file_name1)
        print(file_name)
        if os.path.exists(file_name):
                
            self.update_prayer_times()
            with open(file_name, 'r') as file:
                prayer_times = json.load(file)
                self.prayer_times_data = prayer_times
        else:
            
            self.update_prayer_times()
        self.root.after(3600000, self.check_and_update_json_file)


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

        
        adhan1 = f"azan/{azanval}.mp3"  
        adhan = os.path.join(program_data_dir, adhan1)  
        pygame.mixer.music.load(adhan)
        pygame.mixer.music.play()

    
    def stop_ezan_sound(self):
        adhan1 = f"azan/{azanval}.mp3"  
        adhan = os.path.join(program_data_dir, adhan1)
        pygame.mixer.music.load(adhan)
        if pygame.mixer.music.get_busy() and pygame.mixer.music.get_sound() == adhan:
            pygame.mixer.music.stop()
            
            self.root.withdraw()


    def hide_window(self):
        self.root.withdraw()

    def hide_settings_window(self):
        self.settings_window.withdraw()

    def show_window(self):
        self.root.deiconify()

    def quit_program(self):
        self.root.quit()
        os.kill(os.getpid(), signal.SIGTERM)
        remove_pid_file(pid_file)



def main():
    root = tk.Tk()
    ezan_programi = EzanProgrami(root)
    root.mainloop()

if __name__ == "__main__":
    main()
