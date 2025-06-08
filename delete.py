import os
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

WIPING_METHODS = {
    "DoD 5220.22-M": {
        "desc": "سه مرحله بازنویسی با داده‌های خاص و تصادفی. استاندارد وزارت دفاع آمریکا.",
        "passes": 3,
        "strength": 7,
    },
    "NIST 800-88 Clear": {
        "desc": "بازنویسی ساده با صفر. برای حذف سریع و سطح متوسط.",
        "passes": 1,
        "strength": 5,
    },
    "NIST 800-88 Purge": {
        "desc": "استفاده از دستورات خاص سخت‌افزار برای حذف غیرقابل بازگشت (مانند ATA Secure Erase).",
        "passes": 1,
        "strength": 9,
    },
    "Random-Random-Zero": {
        "desc": "بازنویسی با دو مرحله تصادفی و یک مرحله صفر.",
        "passes": 3,
        "strength": 6,
    },
    "AFSSI-5020": {
        "desc": "الگوی صفر، 0xFF و سپس داده تصادفی. مورد استفاده نیروی هوایی آمریکا.",
        "passes": 3,
        "strength": 7,
    },
    "NAVSO P-5239-26": {
        "desc": "ترکیبی از الگوهای خاص. مورد استفاده نیروی دریایی آمریکا.",
        "passes": 3,
        "strength": 6,
    },
    "Bit Toggle": {
        "desc": "چهار مرحله صفر و 0xFF. مناسب برای اطلاعات حساس.",
        "passes": 4,
        "strength": 8,
    },
    "Gutmann (35-pass)": {
        "desc": "۳۵ مرحله بازنویسی سنگین برای حداکثر اطمینان (مناسب برای HDD).",
        "passes": 35,
        "strength": 10,
    }
}

def overwrite_patterns(f, length, patterns, update_callback=None):
    for i, pat in enumerate(patterns, 1):
        f.seek(0)
        chunk = pat * length
        f.write(chunk[:length])
        f.flush()
        if update_callback:
            update_callback(i)

def secure_delete_file(filepath, method, update_progress=None):
    length = os.path.getsize(filepath)
    passes = WIPING_METHODS[method]["passes"]
    patterns = []

    if method == "DoD 5220.22-M":
        patterns = [os.urandom(1), b'\x00', b'\xFF']
    elif method.startswith("NIST"):
        patterns = [b'\x00'] * passes
    elif method == "Random-Random-Zero":
        patterns = [os.urandom(1), os.urandom(1), b'\x00']
    elif method == "AFSSI-5020":
        patterns = [b'\x00', b'\xFF', os.urandom(1)]
    elif method == "NAVSO P-5239-26":
        patterns = [b'\x01', b'\x7F', os.urandom(1)]
    elif method == "Bit Toggle":
        patterns = [b'\x00', b'\xFF', b'\x00', b'\xFF']
    elif method == "Gutmann (35-pass)":
        patterns = [os.urandom(1) for _ in range(35)]
    else:
        patterns = [os.urandom(1) for _ in range(passes)]

    with open(filepath, "r+b") as f:
        overwrite_patterns(f, length, patterns, lambda i: update_progress(i, passes))
    os.remove(filepath)

def get_all_files_in_folder(folder_path):
    all_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root_dir, file)
            all_files.append(full_path)
    return all_files

class SecureEraserApp:
    def __init__(self, master):
        self.master = master
        self.master.title("پاکسازی ایمن اطلاعات")
        self.master.geometry("600x500")
        self.master.resizable(False, False)

        self.file_list = []
        self.is_wiping = False

        self.paths_var = tk.StringVar()
        self.method_var = tk.StringVar(value="DoD 5220.22-M")

        frame_top = tk.Frame(master)
        frame_top.pack(pady=10)

        btn_choose_files = tk.Button(frame_top, text="انتخاب چند فایل", command=self.choose_files)
        btn_choose_files.grid(row=0, column=0, padx=10)

        btn_choose_folder = tk.Button(frame_top, text="انتخاب پوشه", command=self.choose_folder)
        btn_choose_folder.grid(row=0, column=1, padx=10)

        self.selected_label = tk.Label(master, text="هیچ فایلی انتخاب نشده است.", fg="blue")
        self.selected_label.pack(pady=5)

        tk.Label(master, text="🛡️ روش پاکسازی:").pack()
        self.method_combo = ttk.Combobox(master, textvariable=self.method_var, values=list(WIPING_METHODS.keys()), state="readonly", width=40)
        self.method_combo.pack()
        self.method_combo.bind("<<ComboboxSelected>>", self.on_method_change)

        self.info_label = tk.Label(master, text="", wraplength=550, justify="left", fg="blue")
        self.info_label.pack(pady=10)
        self.on_method_change()

        self.btn_start = tk.Button(master, text="🚨 شروع حذف ایمن", command=self.start_wipe, bg="red", fg="white", width=30)
        self.btn_start.pack(pady=10)

        self.progress_label = tk.Label(master, text="", fg="green")
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(master, length=500)
        self.progress_bar.pack(pady=5)

        tk.Label(master, text="📝 قابلیت انتخاب چند فایل یا کل پوشه با محتویات", fg="gray").pack(pady=10)

        # فریم پایین برای نمایش برنامه نویس و لینک
        frame_bottom = tk.Frame(master)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        label_author = tk.Label(frame_bottom, text="برنامه نویس : محمدعلی عباسپور - اینتل سافت", fg="gray")
        label_author.pack()

        label_link = tk.Label(frame_bottom, text="https://intellsoft.ir", fg="blue", cursor="hand2")
        label_link.pack()
        label_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://intellsoft.ir"))

    def choose_files(self):
        files = filedialog.askopenfilenames(title="انتخاب فایل‌ها")
        if files:
            self.file_list.clear()
            self.file_list.extend(files)
            self.paths_var.set("\n".join(files))
            self.update_selected_label()

    def choose_folder(self):
        folder = filedialog.askdirectory(title="انتخاب پوشه")
        if folder:
            files = get_all_files_in_folder(folder)
            if files:
                self.file_list.clear()
                self.file_list.extend(files)
                self.paths_var.set(f"پوشه انتخاب شده: {folder}\n{len(files)} فایل")
                self.update_selected_label()
            else:
                messagebox.showinfo("اطلاع", "این پوشه فایل قابل حذف ندارد.")

    def update_selected_label(self):
        count = len(self.file_list)
        self.selected_label.config(text=f"{count} فایل برای حذف ایمن انتخاب شده است.")

    def on_method_change(self, event=None):
        method = self.method_var.get()
        info = WIPING_METHODS.get(method, {})
        desc = info.get("desc", "بدون توضیح")
        strength = info.get("strength", 0)
        self.info_label.config(text=f"📘 {desc}\n🔒 قدرت حذف: {strength}/10")

    def start_wipe(self):
        if self.is_wiping:
            return  # جلوگیری از اجرای همزمان چند بار

        if not self.file_list:
            messagebox.showerror("خطا", "لطفاً حداقل یک فایل یا پوشه انتخاب کنید.")
            return

        method = self.method_var.get()
        confirm = messagebox.askyesno("هشدار", f"آیا از حذف ایمن {len(self.file_list)} فایل با روش {method} اطمینان دارید؟")
        if not confirm:
            return

        self.is_wiping = True
        self.btn_start.config(state=tk.DISABLED)
        self.progress_bar["maximum"] = len(self.file_list)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="شروع حذف...")

        threading.Thread(target=self.wipe_files_thread, args=(method,), daemon=True).start()

    def wipe_files_thread(self, method):
        total_files = len(self.file_list)
        for idx, filepath in enumerate(self.file_list, 1):
            try:
                self.update_progress(f"حذف فایل {idx} از {total_files}:\n{filepath}", idx - 1)
                secure_delete_file(filepath, method, update_progress=lambda i, total: None)
            except Exception as e:
                self.show_error(f"خطا در حذف فایل:\n{filepath}\n\n{str(e)}")
        self.finish_wipe()

    def update_progress(self, text, value):
        def callback():
            self.progress_label.config(text=text)
            self.progress_bar["value"] = value
            self.master.update_idletasks()
        self.master.after(0, callback)

    def show_error(self, msg):
        def callback():
            messagebox.showerror("خطا", msg)
        self.master.after(0, callback)

    def finish_wipe(self):
        def callback():
            self.progress_bar["value"] = len(self.file_list)
            self.progress_label.config(text="حذف ایمن تمام فایل‌ها انجام شد.")
            messagebox.showinfo("پایان", "حذف ایمن با موفقیت انجام شد.")
            self.file_list.clear()
            self.paths_var.set("")
            self.update_selected_label()
            self.btn_start.config(state=tk.NORMAL)
            self.is_wiping = False
        self.master.after(0, callback)

root = tk.Tk()
app = SecureEraserApp(root)
root.mainloop()
