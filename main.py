import os, json
import tkinter as tk
from customtkinter import CTk, CTkLabel, CTkEntry, CTkButton, CTkProgressBar
from tkinter import Label, Button, messagebox, filedialog
import shutil
import threading

file_json = 'data_dir.json'
json_directory = {
    'source_directory': '',
    'destination_directory': ''
}


class Window:
    def __init__(self, title, width, height):
        self.root = CTk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        self.interface = None

        # Добавляем событие на закрытие окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.on_open()

    def run(self):
        self.root.mainloop()

    def on_close(self):
        """ при закрытии приложения выгрузить данные в файл json """
        print("Window is closing")
        global json_directory
        json_directory['source_directory'] = self.interface.entry_source.get()
        json_directory['destination_directory'] = self.interface.entry_destination.get()
        with open(file_json, 'w') as file:
            json.dump(json_directory, file, indent=4)
        self.root.destroy()  # Закрытие окна

    def on_open(self):
        """ при открытии приложения загрузить данные из файла json """
        global json_directory
        print(json_directory)
        if os.path.exists(file_json):
            with open(file_json, 'r') as file:
                json_directory = json.load(file)
        else:
            # default_destination = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Рабочий стол")
            default_destination = os.path.join(os.path.expanduser("~"),
                                               "Desktop")  # Значение по умолчанию для destination_folder
            json_directory['source_directory'] = default_destination
            json_directory['destination_directory'] = default_destination
        print(json_directory)


class Interface:
    def __init__(self, window):
        global json_directory

        self.window = window
        self.window.interface = self

        self.label_source = CTkLabel(window.root, text="Исходный каталог:", font=("Arial", 10))
        self.label_source.pack(pady=(10, 0))

        self.entry_source = CTkEntry(window.root, width=200)
        self.entry_source.insert(0, json_directory['source_directory'])  # Установка значения по умолчанию
        self.entry_source.pack()

        self.button_browse_source = CTkButton(window.root, text="Выбрать исходный каталог", command=self.browse_source)
        self.button_browse_source.pack(pady=(5, 10))

        self.label_destination = CTkLabel(window.root, text="Каталог назначения:", font=("Arial", 10))
        self.label_destination.pack()

        self.entry_destination = CTkEntry(window.root, width=200)
        self.entry_destination.insert(0, json_directory['destination_directory'])  # Установка значения по умолчанию
        self.entry_destination.pack()

        self.button_browse_destination = CTkButton(window.root, text="Выбрать каталог назначения",
                                                   command=self.browse_destination)
        self.button_browse_destination.pack(pady=(5, 10))

        self.button_copy = CTkButton(window.root, text="Скопировать", command=self.copy)
        self.button_copy.pack()

        self.progressbar = CTkProgressBar(window.root, orientation="horizontal", mode="determinate", width=200,
                                          height=5)
        # self.progressbar.pack(pady=(10, 5))

        self.label_progress = CTkLabel(window.root, text="", font=("Arial", 10))
        # self.label_progress.pack()

    def browse_source(self):
        current_folder = self.entry_source.get()
        source_folder = filedialog.askdirectory(initialdir=current_folder)
        if source_folder:
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, source_folder)
            self.progressbar.pack_forget()  # Скрыть прогресс-бар при изменении директории
            self.label_progress.pack_forget()  # Скрыть метку процента при изменении директории

    def browse_destination(self):
        current_folder = self.entry_destination.get()
        destination_folder = filedialog.askdirectory(initialdir=current_folder)
        if destination_folder:
            self.entry_destination.delete(0, tk.END)
            self.entry_destination.insert(0, destination_folder)
            self.progressbar.pack_forget()  # Скрыть прогресс-бар при изменении директории
            self.label_progress.pack_forget()  # Скрыть метку процента при изменении директории

    def copy(self):
        self.progressbar.pack(pady=(10, 5))
        self.label_progress.pack()
        source_folder = self.entry_source.get()
        destination_folder = self.entry_destination.get()

        if not source_folder or not destination_folder:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите исходный и целевой каталоги")
            return

        try:
            backuper = Backuper(source_folder, destination_folder, self.progressbar, self.label_progress)
            thread = threading.Thread(target=backuper.backup)
            thread.start()
            self.window.root.after(100, self.update_progress, backuper)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при копировании каталога: {str(e)}")

    def update_progress(self, backuper):
        current_progress = backuper.get_progress()
        if current_progress is not None:
            self.progressbar.set(current_progress / 100)  # ["value"] = current_progress
            self.label_progress.configure(text=f"{current_progress}%")
        if current_progress < 100:
            # Call update_progress again after a short delay
            self.window.root.after(100, self.update_progress, backuper)


class Backuper:
    def __init__(self, source_folder, destination_folder, progressbar, label_progress):
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.progressbar = progressbar
        self.label_progress = label_progress
        self.total_files = sum(len(files) for _, _, files in os.walk(self.source_folder))
        self.current_progress = 0

    def backup(self):
        try:
            new_destination_folder = os.path.join(self.destination_folder, os.path.basename(self.source_folder))
            for root, dirs, files in os.walk(self.source_folder):
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(new_destination_folder, os.path.relpath(src_file, self.source_folder))
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)  # Создаем подкаталоги, если они отсутствуют
                    shutil.copy2(src_file, dst_file)  # Копируем файл
                    self.current_progress += 1  # Увеличиваем текущий прогресс на 1
                    # self.update_progress() # Обновление progress bar плсде каждого копирования файла
            messagebox.showinfo("Успех", f"Каталог {self.source_folder} успешно скопирован в {self.destination_folder}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при копировании каталога: {str(e)}")

    def get_progress(self):
        return int((self.current_progress / self.total_files) * 100) if self.total_files > 0 else None


if __name__ == "__main__":
    window = Window("Приложение для копирования каталогов", 400, 300)
    interface = Interface(window)
    window.run()
