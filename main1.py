import os
import time
import threading
import requests
import subprocess
import tkinter as tk
import customtkinter as ctk
import re
from tkinter import filedialog, messagebox, Menu
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor

# --- 🍎 Apple Style Config ---
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")

COLOR_BG = "#F5F5F7"
COLOR_CARD = "#FFFFFF"
COLOR_ACCENT = "#007AFF"
COLOR_TEXT = "#1D1D1F"

# --- 🐧 Arch Terminal Config ---
TERM_BG = "#0c0c0c"
TERM_FG = "#33ff00"
TERM_ERR = "#ff5555"
TERM_INFO = "#8be9fd"
TERM_FONT = ("Consolas", 10)

class ArchTerminal(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=TERM_BG, fg=TERM_FG, insertbackground="white", 
                       font=TERM_FONT, state="disabled", bd=0, highlightthickness=0)
        self.tag_config("SUCCESS", foreground="#50fa7b")
        self.tag_config("ERROR", foreground="#ff5555")
        self.tag_config("INFO", foreground="#8be9fd")
        self.tag_config("WARN", foreground="#ffb86c")
        self.tag_config("PROMPT", foreground="#bd93f9")
        self.tag_config("TIMESTAMP", foreground="#6272a4")

    def write(self, text, tag=None):
        self.configure(state="normal")
        timestamp = time.strftime("[%H:%M:%S]")
        self.insert("end", f"{timestamp} ", "TIMESTAMP")
        self.insert("end", "root@arch:~# ", "PROMPT")
        if tag: self.insert("end", text + "\n", tag)
        else: self.insert("end", text + "\n")
        self.see("end")
        self.configure(state="disabled")

class HybridMangaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manga Downloader - Final Fixed By.Stack Shift")
        self.geometry("950x850")
        self.configure(fg_color=COLOR_BG)
        
        # --- 🖼️ ส่วนที่เพิ่มมา: ตั้งไอคอนโปรแกรม ---
        # ใช้ try/except เพื่อกัน Error กรณีหาไฟล์รูปไม่เจอ
        try:
            self.iconbitmap("icon.ico") 
        except:
            pass 
        # ----------------------------------------

        self.font_title = ("Segoe UI", 24, "bold")
        self.font_bold = ("Segoe UI", 13, "bold")

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10))
        ctk.CTkLabel(self.header_frame, text="Manga Downloader", font=self.font_title, text_color=COLOR_TEXT).pack()

        # MAIN CARD
        self.main_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=15)
        self.main_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # INPUTS
        self.top_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(self.top_frame, text="Paste Links (Right Click to Paste):", font=self.font_bold, text_color=COLOR_TEXT).pack(anchor="w")
        self.url_text_area = ctk.CTkTextbox(self.top_frame, height=80, corner_radius=10, fg_color="#F2F2F7", 
                                            border_width=0, text_color=COLOR_TEXT, font=("Segoe UI", 12))
        self.url_text_area.pack(fill="x", pady=(5, 10))
        self.url_text_area.insert("0.0", "วางลิ้งก์ที่นี่...")
        
        # Context Menu
        self.right_click_menu = Menu(self, tearoff=0)
        self.right_click_menu.add_command(label="Paste", command=self.paste_text)
        self.right_click_menu.add_command(label="Clear", command=self.clear_input)
        
        # Bindings
        self.url_text_area.bind("<Button-3>", self.show_context_menu)
        self.url_text_area.bind("<FocusIn>", self.clear_placeholder)
        # ❌ ลบบรรทัด <Control-v> ออกแล้ว เพื่อไม่ให้วางซ้ำ 2 รอบ

        # Save Path
        self.path_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.path_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(self.path_frame, text="Save to:", font=self.font_bold, text_color=COLOR_TEXT).pack(side="left", padx=(0, 10))
        self.path_entry = ctk.CTkEntry(self.path_frame, height=35, corner_radius=8, fg_color="#F2F2F7", text_color="black")
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.insert(0, os.getcwd())
        self.btn_browse = ctk.CTkButton(self.path_frame, text="Browse Folder", width=100, height=35, fg_color="#E5E5EA", 
                                        text_color="black", hover_color="#D1D1D6", command=self.choose_folder)
        self.btn_browse.pack(side="left", padx=(10, 0))

        # Buttons
        self.btn_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.btn_row.pack(pady=(15, 0))
        self.btn_start = ctk.CTkButton(self.btn_row, text="Download All", command=self.start_download_thread, 
                                       width=180, height=45, corner_radius=22, fg_color=COLOR_ACCENT, font=self.font_bold)
        self.btn_start.pack(side="left", padx=10)
        self.btn_clear = ctk.CTkButton(self.btn_row, text="Clear Input", command=self.clear_input, 
                                       width=120, height=45, corner_radius=22, fg_color="#E5E5EA", 
                                       text_color=COLOR_TEXT, hover_color="#D1D1D6")
        self.btn_clear.pack(side="left", padx=10)

        # BOTTOM SPLIT
        self.bottom_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.bottom_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.bottom_frame.columnconfigure(0, weight=6) 
        self.bottom_frame.columnconfigure(1, weight=4)

        # Left: Arch Terminal
        self.left_panel = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.left_panel, text="Activity Terminal", font=self.font_bold, text_color=COLOR_TEXT).pack(anchor="w")
        self.term_container = ctk.CTkFrame(self.left_panel, fg_color="black", corner_radius=10)
        self.term_container.pack(fill="both", expand=True, pady=(5,0))
        self.terminal = ArchTerminal(self.term_container)
        self.terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # Right: Library
        self.right_panel = ctk.CTkFrame(self.bottom_frame, fg_color="#F9F9FB", corner_radius=10, border_width=1, border_color="#E5E5EA")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.lib_header = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=30)
        self.lib_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.lib_header, text="📂 Folders", font=self.font_bold, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(self.lib_header, text="🔄 Refresh", width=60, height=20, font=("Segoe UI", 10), 
                      fg_color="#E5E5EA", text_color="black", hover_color="#D1D1D6", command=self.refresh_library).pack(side="right")
        self.lib_scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.lib_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.placeholder_active = True
        self.is_running = False
        self.refresh_library()
        self.terminal.write("System Ready. Paste issue fixed.", "INFO")

    # --- Functions ---
    def refresh_library(self):
        for widget in self.lib_scroll.winfo_children(): widget.destroy()
        path = self.path_entry.get()
        if not os.path.exists(path): return
        try:
            items = os.listdir(path)
            folders = [f for f in items if os.path.isdir(os.path.join(path, f))]
            folders.sort()
            for folder in folders: self.create_folder_item(folder, path)
        except: pass

    def create_folder_item(self, folder_name, base_path):
        row = ctk.CTkFrame(self.lib_scroll, fg_color="white", corner_radius=6, height=40)
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="📁", font=("Segoe UI", 14), text_color="#FF9500").pack(side="left", padx=(10, 5), pady=8)
        display_name = (folder_name[:25] + '..') if len(folder_name) > 25 else folder_name
        ctk.CTkLabel(row, text=display_name, font=("Segoe UI", 12), text_color="black").pack(side="left", pady=8)
        full_path = os.path.join(base_path, folder_name)
        cmd = lambda p=full_path: self.open_folder(p)
        ctk.CTkButton(row, text="Open", width=50, height=24, fg_color="#E5E5EA", text_color="black", hover_color="#D1D1D6", font=("Segoe UI", 10), command=cmd).pack(side="right", padx=10, pady=8)

    def open_folder(self, path):
        try: os.startfile(path)
        except: pass

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, "end"); self.path_entry.insert(0, folder); self.refresh_library()

    def show_context_menu(self, event):
        try: self.right_click_menu.tk_popup(event.x_root, event.y_root)
        finally: self.right_click_menu.grab_release()

    def paste_text(self):
        try:
            clip = self.clipboard_get()
            if self.placeholder_active: self.url_text_area.delete("1.0", "end"); self.placeholder_active = False
            self.url_text_area.insert("insert", clip)
        except: pass

    def clear_placeholder(self, event):
        if self.placeholder_active: self.url_text_area.delete("1.0", "end"); self.placeholder_active = False

    def clear_input(self):
        self.url_text_area.delete("1.0", "end")

    # --- CORE LOGIC ---
    def start_download_thread(self):
        if self.is_running: return
        raw_text = self.url_text_area.get("1.0", "end").strip()
        save_path = self.path_entry.get().strip()

        if not raw_text or raw_text == "วางลิ้งก์ที่นี่..." or "http" not in raw_text:
            self.terminal.write("Error: No valid URLs.", "ERROR")
            return
        
        self.is_running = True
        self.btn_start.configure(state="disabled", text="Running...", fg_color="#B4B4B4")
        self.terminal.write("🚀 Starting Process...", "INFO")
        
        threading.Thread(target=self.process_queue, args=(raw_text, save_path)).start()

    def process_queue(self, raw_text, save_root):
        url_list = [line.strip() for line in raw_text.split('\n') if line.strip() and "http" in line]
        
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--log-level=3')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = None
        try:
            self.terminal.write("Initializing WebDriver...", "WARN")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            for i, url in enumerate(url_list):
                self.terminal.write(f"Processing [{i+1}/{len(url_list)}]", "PROMPT")
                self.download_single_url_fast(driver, url, i+1, save_root)
            
            self.terminal.write("✅ ALL TASKS COMPLETED.", "SUCCESS")
            self.refresh_library()
            messagebox.showinfo("Success", "All downloads finished!")

        except Exception as e:
            self.terminal.write(f"CRITICAL ERROR: {e}", "ERROR")
        finally:
            if driver: driver.quit()
            self.is_running = False
            self.btn_start.configure(state="normal", text="Download All", fg_color=COLOR_ACCENT)

    def download_single_url_fast(self, driver, url, index, save_root):
        try:
            self.terminal.write(f"Fetching: {url[:40]}...", "INFO")
            driver.get(url)
            
            page_title = driver.title
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', page_title).strip()
            if not safe_name: safe_name = f"Manga_Set_{index:02d}"
            safe_name = safe_name[:100]

            folder_name = os.path.join(save_root, safe_name)
            if not os.path.exists(folder_name): os.makedirs(folder_name)
            
            self.terminal.write(f"   -> Saving to folder: '{safe_name}'", "INFO")

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height

            images = driver.find_elements(By.TAG_NAME, 'img')
            self.terminal.write(f"   -> Found {len(images)} images.", "WARN")

            download_tasks = []
            for img in images:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src: download_tasks.append(src)
            
            if not download_tasks:
                self.terminal.write("   -> ❌ No images found!", "ERROR")
                return

            count = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i, src in enumerate(download_tasks):
                    futures.append(executor.submit(self.download_image_worker, src, folder_name, i+1))
                
                for future in futures:
                    if future.result():
                        count += 1
                        if count % 5 == 0: self.terminal.write(f"   -> Progress: {count}/{len(download_tasks)}", "INFO")

            self.terminal.write(f"   -> ✅ Saved {count} images", "SUCCESS")
            
        except Exception as e:
            self.terminal.write(f"   -> Failed: {e}", "ERROR")

    def download_image_worker(self, src, folder_path, number):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(src, headers=headers, timeout=10)
            if res.status_code == 200:
                content_type = res.headers.get('content-type', '').lower()
                ext = None
                if 'jpeg' in content_type or 'jpg' in content_type: ext = '.jpg'
                elif 'png' in content_type: ext = '.png'
                elif 'webp' in content_type: ext = '.webp'
                
                if not ext:
                    if '.jpg' in src.lower(): ext = '.jpg'
                    elif '.png' in src.lower(): ext = '.png'
                    elif '.webp' in src.lower(): ext = '.webp'

                if ext:
                    filename = f"page_{number:03d}{ext}"
                    filepath = os.path.join(folder_path, filename)
                    with open(filepath, 'wb') as f: f.write(res.content)
                    return True
        except: pass
        return False

if __name__ == "__main__":
    app = HybridMangaApp()
    app.mainloop()