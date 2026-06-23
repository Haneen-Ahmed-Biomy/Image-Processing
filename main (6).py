import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import filters
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ImageProcessingStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HANEEN| Image Processing Studio")
        
        # --- Modern Color Palette ---
        self.bg_color = "#0e0e11"
        self.card_color = "#18181b"
        self.accent_color = "#0ea5e9"
        self.btn_color = "#27272a"
        self.btn_hover = "#3f3f46"
        self.text_main = "#f4f4f5"
        self.text_muted = "#a1a1aa"
        
        self.configure(fg_color=self.bg_color)
        ctk.set_appearance_mode("dark")
        
        # --- State ---
        self.undo_stack = []
        self.active_image = None
        self.source_image = None
        self.temp_buffer = None
        self.blend_img2 = None   
        self.uploaded_paths = [] # قائمة لحفظ مسارات الصور المرفوعة
        self.thumbnails_cache = [] # لتخزين الصور المصغرة حتى لا تختفي

        # إخفاء النافذة الرئيسية وعرض شاشة التحميل
        self.withdraw()
        self.show_splash_screen()

    # ==========================================
    # SPLASH SCREEN LOGIC (FULL SCREEN)
    # ==========================================
    def show_splash_screen(self):
        self.splash = ctk.CTkToplevel(self)
        self.splash.overrideredirect(True) # إخفاء شريط العنوان
        self.splash.configure(fg_color=self.bg_color)
        self.splash.attributes("-topmost", True)
        
        # جعلها بحجم الشاشة بالكامل
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.splash.geometry(f"{screen_w}x{screen_h}+0+0")
        
        # حاوية لتوسيط المحتوى في نصف الشاشة
        container = ctk.CTkFrame(self.splash, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="HANEEN", font=ctk.CTkFont(family="Segoe UI Black", size=60), text_color=self.text_main).pack(pady=(0, 5))
        ctk.CTkLabel(container, text=" Image Processing ", font=ctk.CTkFont(family="Segoe UI", size=20), text_color=self.accent_color).pack()
        
        self.progress_lbl = ctk.CTkLabel(container, text="Initializing core modules...", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=self.text_muted)
        self.progress_lbl.pack(pady=(50, 10))
        
        self.progress_bar = ctk.CTkProgressBar(container, width=400, height=10, progress_color=self.accent_color, fg_color=self.btn_color)
        self.progress_bar.pack()
        self.progress_bar.set(0)
        
        self.progress_value = 0
        self.update_splash_progress()

    def update_splash_progress(self):
        # تقليل سرعة الزيادة لجعل التحميل أطول
        self.progress_value += 0.01 
        self.progress_bar.set(self.progress_value)
        
        if self.progress_value < 1.0:
            msgs = ["Loading OpenCV tools...", "Warming up filters...", "Loading Deep Learning Models...", "Preparing workspace..."]
            if self.progress_value > 0.25: self.progress_lbl.configure(text=msgs[0])
            if self.progress_value > 0.50: self.progress_lbl.configure(text=msgs[1])
            if self.progress_value > 0.75: self.progress_lbl.configure(text=msgs[2])
            if self.progress_value > 0.90: self.progress_lbl.configure(text=msgs[3])
            self.after(50, self.update_splash_progress) # وقت أطول بين كل خطوة (إجمالي ~5 ثواني)
        else:
            self.splash.destroy()
            self.deiconify()
            self.state('zoomed')
            self._build_modern_interface()

    # ==========================================
    # INTEGRATED GALLERY LOGIC
    # ==========================================
    def upload_images(self):
        # السماح باختيار عدة صور معاً
        filepaths = filedialog.askopenfilenames(title="Upload Images", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if filepaths:
            for path in filepaths:
                if path not in self.uploaded_paths:
                    self.uploaded_paths.append(path)
            self.refresh_gallery()

    def refresh_gallery(self):
        # مسح الصور القديمة من الصندوق
        for widget in self.gallery_scroll.winfo_children():
            widget.destroy()
        
        self.thumbnails_cache.clear()
        
        if not self.uploaded_paths:
            ctk.CTkLabel(self.gallery_scroll, text="No images uploaded yet.", text_color=self.text_muted).pack(pady=30)
            return

        row, col = 0, 0
        for path in self.uploaded_paths:
            try:
                pil_img = Image.open(path)
                pil_img.thumbnail((90, 90)) # حجم مصغر للصور في الشريط الجانبي
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(90, 90))
                self.thumbnails_cache.append(ctk_img) # حفظها في الذاكرة
                
                # زر للصورة
                btn = ctk.CTkButton(self.gallery_scroll, image=ctk_img, text="", fg_color="transparent", width=90, height=90, hover_color=self.btn_hover,
                                    command=lambda p=path: self.select_from_gallery(p))
                btn.grid(row=row, column=col, padx=7, pady=7)
                
                col += 1
                if col > 2: # 3 صور في كل صف
                    col = 0
                    row += 1
            except Exception:
                pass

    def select_from_gallery(self, path):
        # التحقق من الاختيار (هل يريدها صورة أساسية أم ثانوية للطرح؟)
        target = self.target_var.get()
        if target == "Primary":
            self.active_image = filters.load_image_from_disk(path)
            self.source_image = self.active_image.copy()
            self.undo_stack.clear()
            self.show_image(self.active_image)
        else:
            self.blend_img2 = filters.load_image_from_disk(path)
            messagebox.showinfo("Image Linked", "Secondary Image selected successfully! Ready for Math Operations.")

    # ==========================================
    # UI BUILDER
    # ==========================================
    def create_card(self, parent, title, icon=""):
        card = ctk.CTkFrame(parent, fg_color=self.card_color, corner_radius=15, border_width=1, border_color="#27272a")
        card.pack(fill="x", padx=15, pady=10)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text=f"{icon} {title}", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=self.accent_color).pack(side="left")
        return card

    def add_modern_btn(self, parent, text, command, highlight=False):
        fg = self.accent_color if highlight else self.btn_color
        hov = "#0284c7" if highlight else self.btn_hover
        txt_col = "#ffffff" if highlight else self.text_main
        btn = ctk.CTkButton(parent, text=text, command=command, fg_color=fg, hover_color=hov, text_color=txt_col, corner_radius=8, height=36, font=ctk.CTkFont(family="Segoe UI", size=12))
        btn.pack(fill="x", padx=15, pady=5)
        return btn

    def _build_modern_interface(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(self, width=380, fg_color="transparent", scrollbar_button_color="#27272a")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)

        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", pady=(10, 20), padx=15)
        ctk.CTkLabel(title_frame, text="HANEEN", font=ctk.CTkFont(family="Segoe UI Black", size=24), text_color=self.text_main).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Image Processing", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=self.text_muted).pack(anchor="w")

        # --- Card 1: Workspace & Integrated Gallery ---
        card_files = self.create_card(self.sidebar, "Media Pool", "📥")
        self.add_modern_btn(card_files, "Upload Images", self.upload_images, highlight=True)
        
        # اختيار نوع الصورة (أساسية أم ثانوية)
        ctk.CTkLabel(card_files, text="Select Mode Before Clicking an Image:", font=ctk.CTkFont(size=11), text_color=self.text_muted).pack(pady=(10, 0))
        self.target_var = ctk.StringVar(value="Primary")
        self.target_selector = ctk.CTkSegmentedButton(card_files, values=["Primary", "Secondary"], variable=self.target_var, selected_color=self.accent_color, selected_hover_color="#0284c7")
        self.target_selector.pack(fill="x", padx=15, pady=(5, 10))

        # صندوق معرض الصور
        self.gallery_scroll = ctk.CTkScrollableFrame(card_files, height=220, fg_color=self.bg_color, corner_radius=8)
        self.gallery_scroll.pack(fill="x", padx=15, pady=(0, 15))
        self.refresh_gallery() # تشغيل الدالة لعرض الرسالة الافتراضية
        
        sys_frame = ctk.CTkFrame(card_files, fg_color="transparent")
        sys_frame.pack(fill="x", padx=15, pady=(5, 15))
        ctk.CTkButton(sys_frame, text="↩ Undo", width=120, fg_color=self.btn_color, hover_color=self.btn_hover, command=self.execute_undo).pack(side="left")
        ctk.CTkButton(sys_frame, text="⟲ Reset", width=120, fg_color="#7f1d1d", hover_color="#991b1b", command=self.execute_reset).pack(side="right")

        # --- Card 2: Math & Blending ---
        card_math = self.create_card(self.sidebar, "Arithmetic & Blend", "➗")
        math_btns = ctk.CTkFrame(card_math, fg_color="transparent")
        math_btns.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(math_btns, text="Add", width=85, fg_color=self.btn_color, hover_color=self.btn_hover, command=lambda: self.proc_math('add')).grid(row=0, column=0, padx=2)
        ctk.CTkButton(math_btns, text="Sub", width=85, fg_color=self.btn_color, hover_color=self.btn_hover, command=lambda: self.proc_math('sub')).grid(row=0, column=1, padx=2)
        ctk.CTkButton(math_btns, text="Diff", width=85, fg_color=self.btn_color, hover_color=self.btn_hover, command=lambda: self.proc_math('diff')).grid(row=0, column=2, padx=2)
        self.add_slider(card_math, "Alpha Blend Ratio", 0.0, 1.0, 0.5, self.update_blend)

        # --- Card 3: Color Channels ---
        card_colors = self.create_card(self.sidebar, "RGB Extraction", "🎨")
        rgb_frame = ctk.CTkFrame(card_colors, fg_color="transparent")
        rgb_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(rgb_frame, text="R", width=85, fg_color="#7f1d1d", hover_color="#991b1b", command=lambda: self.apply_rgb(filters.get_red_channel)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(rgb_frame, text="G", width=85, fg_color="#14532d", hover_color="#166534", command=lambda: self.apply_rgb(filters.get_green_channel)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(rgb_frame, text="B", width=85, fg_color="#1e3a8a", hover_color="#1e40af", command=lambda: self.apply_rgb(filters.get_blue_channel)).grid(row=0, column=2, padx=2)

        # --- Card 4: Tonal Adjustments ---
        card_tune = self.create_card(self.sidebar, "Tonal Adjustments", "✨")
        self.add_slider(card_tune, "Brightness", -100, 100, 0, self.update_brightness)
        self.add_slider(card_tune, "Contrast", 0.5, 3.0, 1.0, self.update_contrast)
        self.add_modern_btn(card_tune, "Histogram Stretching", lambda: self.apply_simple(filters.histogram_stretching_color))
        self.add_modern_btn(card_tune, "Weighted Grayscale", lambda: self.apply_simple(filters.apply_weighted_grayscale))
        self.add_modern_btn(card_tune, "Intensity Invert", lambda: self.apply_simple(filters.apply_complement))

        # --- Card 5: Thresholding ---
        card_thresh = self.create_card(self.sidebar, "Threshold & Dither", "🌗")
        self.add_modern_btn(card_thresh, "Binary Threshold", lambda: self.apply_simple(filters.apply_binary_threshold))
        self.add_modern_btn(card_thresh, "Otsu Threshold (Auto)", lambda: self.apply_simple(filters.apply_otsu_threshold))
        self.add_modern_btn(card_thresh, "Floyd-Steinberg Dither", lambda: self.apply_simple(filters.apply_floyd_steinberg))

        # --- Card 6: Filters & Noise ---
        card_filters = self.create_card(self.sidebar, "Filters & Noise", "🌊")
        self.add_slider(card_filters, "Mean Blur Intensity", 1, 25, 1, self.update_mean)
        self.add_modern_btn(card_filters, "Median Noise Repair", lambda: self.apply_simple(filters.restore_image))
        self.add_modern_btn(card_filters, "Min Filter", lambda: self.apply_simple(filters.apply_min_filter))
        self.add_modern_btn(card_filters, "Max Filter", lambda: self.apply_simple(filters.apply_max_filter))
        self.add_modern_btn(card_filters, "Add Salt & Pepper", lambda: self.apply_simple(filters.add_salt_and_pepper))

        # --- Card 7: Morphology ---
        card_morph = self.create_card(self.sidebar, "Morphology", "🦠")
        morph_btns = ctk.CTkFrame(card_morph, fg_color="transparent")
        morph_btns.pack(fill="x", padx=15, pady=(0, 15))
        m_ops = [("Erode", filters.apply_erosion), ("Dilate", filters.apply_dilation), 
                 ("Open", filters.apply_opening), ("Close", filters.apply_closing)]
        for i, (name, func) in enumerate(m_ops):
            ctk.CTkButton(morph_btns, text=name, width=130, fg_color=self.btn_color, hover_color=self.btn_hover, command=lambda f=func: self.apply_simple(f)).grid(row=i//2, column=i%2, padx=3, pady=3)

        # --- Card 8: Stylization ---
        card_style = self.create_card(self.sidebar, "Stylization", "🎭")
        self.add_modern_btn(card_style, "Sharpen Image", lambda: self.apply_simple(filters.apply_sharpen))
        self.add_modern_btn(card_style, "Sepia Vintage", lambda: self.apply_simple(filters.apply_sepia))
        self.add_modern_btn(card_style, "Cartoonify", lambda: self.apply_simple(filters.apply_cartoon))
        
        self.add_modern_btn(self.sidebar, "💾 Export Result", self.export_file, highlight=True)
        ctk.CTkLabel(self.sidebar, text="").pack(pady=20)

        # ==========================================
        # VIEWPORT (MAIN CANVAS)
        # ==========================================
        self.right_panel = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        self.canvas_frame = ctk.CTkFrame(self.right_panel, fg_color=self.card_color, corner_radius=15, border_width=1, border_color="#27272a")
        self.canvas_frame.pack(expand=True, fill="both", pady=(0, 15))
        
        self.viewport = ctk.CTkLabel(self.canvas_frame, text="No Media Loaded", font=ctk.CTkFont(family="Segoe UI", size=18), text_color=self.text_muted)
        self.viewport.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.hist_frame = ctk.CTkFrame(self.right_panel, fg_color=self.card_color, corner_radius=15, height=200, border_width=1, border_color="#27272a")
        self.hist_frame.pack(fill="x")
        
        self.fig, self.ax = plt.subplots(figsize=(6, 1.8))
        self.fig.patch.set_facecolor(self.card_color)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.hist_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)

    # --- HELPER UI FUNCTIONS ---
    def add_slider(self, parent, text, start, end, default, cmd):
        lbl = ctk.CTkLabel(parent, text=f"{text}", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=self.text_main)
        lbl.pack(anchor="w", padx=15, pady=(5, 0))
        s = ctk.CTkSlider(parent, from_=start, to=end, button_color=self.accent_color, button_hover_color="#38bdf8", progress_color=self.accent_color, command=lambda v: cmd(v, lbl, text))
        s.set(default)
        s.pack(fill="x", padx=15, pady=(0, 15))
        s.bind("<ButtonRelease-1>", self.finalize_slider)

    # --- CORE PROCESSING LOGIC ---
    def apply_simple(self, func, *args):
        if self.active_image is not None:
            self.push_undo()
            self.active_image = func(self.active_image, *args)
            self.show_image(self.active_image)

    def apply_rgb(self, func):
        if self.source_image is not None:
            self.push_undo()
            self.active_image = func(self.source_image.copy())
            self.show_image(self.active_image)

    def proc_math(self, operation):
        if self.active_image is None or self.blend_img2 is None:
            messagebox.showwarning("Notice", "Please select Image 2 from the Gallery first.")
            return
        try:
            self.push_undo()
            if operation == 'add': self.active_image = filters.add_images(self.active_image, self.blend_img2)
            elif operation == 'sub': self.active_image = filters.subtract_images(self.active_image, self.blend_img2)
            elif operation == 'diff': self.active_image = filters.diff_images(self.active_image, self.blend_img2)
            self.show_image(self.active_image)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def push_undo(self):
        if self.active_image is not None:
            self.undo_stack.append(self.active_image.copy())

    def _prepare_slider(self):
        if self.temp_buffer is None: self.temp_buffer = self.active_image.copy()

    def update_blend(self, val, lbl, txt):
        if self.active_image is not None and self.blend_img2 is not None:
            self._prepare_slider()
            preview = filters.blend_images(self.temp_buffer, self.blend_img2, alpha=float(val))
            lbl.configure(text=f"{txt} ({float(val):.2f})")
            self.show_image(preview, is_preview=True)

    def update_brightness(self, val, lbl, txt):
        if self.active_image is not None:
            self._prepare_slider()
            preview = filters.adjust_brightness(self.temp_buffer, int(val))
            lbl.configure(text=f"{txt} ({int(val)})")
            self.show_image(preview, is_preview=True)

    def update_contrast(self, val, lbl, txt):
        if self.active_image is not None:
            self._prepare_slider()
            preview = filters.adjust_contrast(self.temp_buffer, float(val))
            lbl.configure(text=f"{txt} ({float(val):.1f})")
            self.show_image(preview, is_preview=True)

    def update_mean(self, val, lbl, txt):
        if self.active_image is not None:
            self._prepare_slider()
            v = int(val) | 1
            preview = filters.apply_mean_filter(self.temp_buffer, v)
            lbl.configure(text=f"{txt} ({v}px)")
            self.show_image(preview, is_preview=True)

    def finalize_slider(self, e):
        if self.temp_buffer is not None:
            self.push_undo()
            self.active_image = self.last_preview_shown.copy()
            self.temp_buffer = None

    def show_image(self, img, is_preview=False):
        if is_preview: self.last_preview_shown = img
        img_disp = np.ascontiguousarray(np.uint8(np.clip(img, 0, 255)))
        
        self.ax.clear()
        self.ax.set_facecolor(self.card_color)
        if len(img_disp.shape) == 3:
            for i, c in enumerate(('#3b82f6', '#22c55e', '#ef4444')):
                h_val = cv2.calcHist([img_disp], [i], None, [256], [0, 256])
                self.ax.plot(h_val.flatten(), color=c, lw=1.5, alpha=0.9)
            rgb = cv2.cvtColor(img_disp, cv2.COLOR_BGR2RGB)
        else:
            h_val = cv2.calcHist([img_disp], [0], None, [256], [0, 256])
            self.ax.plot(h_val.flatten(), color=self.text_main, lw=1.5)
            rgb = cv2.cvtColor(img_disp, cv2.COLOR_GRAY2RGB)
            
        self.ax.set_xlim([0, 256]); self.ax.set_ylim(bottom=0); self.ax.axis('off')
        self.fig.tight_layout(pad=0); self.canvas.draw()
        
        p_img = Image.fromarray(rgb)
        canvas_w = self.canvas_frame.winfo_width()
        canvas_h = self.canvas_frame.winfo_height()
        if canvas_w < 100: canvas_w = 900
        if canvas_h < 100: canvas_h = 600
        
        ratio = min(canvas_w/p_img.width, canvas_h/p_img.height) * 0.95
        new_s = (int(p_img.width*ratio), int(p_img.height*ratio))
        
        if new_s[0] > 0 and new_s[1] > 0:
            tk_img = ImageTk.PhotoImage(p_img.resize(new_s, Image.Resampling.LANCZOS))
            self.viewport.configure(image=tk_img, text="")
            self.viewport.image = tk_img

    def execute_undo(self):
        if self.undo_stack:
            self.active_image = self.undo_stack.pop()
            self.show_image(self.active_image)

    def execute_reset(self):
        if self.source_image is not None:
            self.push_undo()
            self.active_image = self.source_image.copy()
            self.show_image(self.active_image)

    def export_file(self):
        if self.active_image is not None:
            p = filedialog.asksaveasfilename(defaultextension=".jpg")
            if p: filters.save_image_to_disk(p, self.active_image)

if __name__ == "__main__":
    app = ImageProcessingStudio()
    app.mainloop()