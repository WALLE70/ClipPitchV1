import os
import sys
import threading

# 1. Safely import libraries. If one is missing or corrupted, force a popup instead of a silent crash.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import customtkinter as ctk
    import librosa
    import soundfile as sf
    import pygame
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Startup Error", f"Library load failed:\n{e}\n\nCheck your pip installs.")
    sys.exit()

# Set Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PitchShifterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vocal Pitch Studio")
        self.geometry("500x400")
        
        self.file_path = ""
        self.temp_output = "temp_shifted.wav"
        self.is_processing = False

        # 2. Defer audio engine init until inside the app to prevent instant OS-level crashes
        try:
            pygame.mixer.init()
        except Exception as e:
            messagebox.showwarning("Audio Engine Warning", f"Could not initialize playback:\n{e}")

        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Vocal Pitch Studio", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=(20, 10))

        # File Selection
        self.btn_load = ctk.CTkButton(self, text="📂 Load Audio Clip", command=self.load_file, width=200)
        self.btn_load.pack(pady=10)
        
        self.lbl_file = ctk.CTkLabel(self, text="No file selected", text_color="gray")
        self.lbl_file.pack()

        # Pitch Slider
        self.lbl_pitch = ctk.CTkLabel(self, text="Pitch Shift: 0 Semitones", font=("Roboto", 14))
        self.lbl_pitch.pack(pady=(20, 5))
        
        self.slider = ctk.CTkSlider(self, from_=-12, to=12, number_of_steps=24, command=self.update_slider_text)
        self.slider.set(0)
        self.slider.pack(width=300)

        # Action Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=30)
        
        self.btn_play = ctk.CTkButton(self.btn_frame, text="▶️ Play Shifted", command=self.play_audio_thread, fg_color="#28a745", hover_color="#218838")
        self.btn_play.grid(row=0, column=0, padx=10)
        
        self.btn_save = ctk.CTkButton(self.btn_frame, text="💾 Save File", command=self.save_audio_thread)
        self.btn_save.grid(row=0, column=1, padx=10)

        # Status Label
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="orange")
        self.lbl_status.pack()

    def update_slider_text(self, value):
        semitones = int(value)
        self.lbl_pitch.configure(text=f"Pitch Shift: {semitones} Semitones")

    def load_file(self):
        path = filedialog.askopenfilename(title="Select a Sound Clip", filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if path:
            self.file_path = path
            self.lbl_file.configure(text=os.path.basename(path), text_color="white")

    def process_audio(self, output_path):
        try:
            semitones = int(self.slider.get())
            y, sr = librosa.load(self.file_path, sr=None)
            y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
            sf.write(output_path, y_shifted, sr)
            return True
        except Exception as e:
            messagebox.showerror("Processing Error", f"Failed to process audio:\n{str(e)}")
            return False

    def play_audio_thread(self):
        if not self.file_path:
            messagebox.showwarning("Warning", "Load an audio file first!")
            return
        if self.is_processing:
            return
            
        self.is_processing = True
        self.lbl_status.configure(text="Processing audio, please wait...")
        self.btn_play.configure(state="disabled")
        
        threading.Thread(target=self._play_task, daemon=True).start()

    def _play_task(self):
        if self.process_audio(self.temp_output):
            try:
                pygame.mixer.music.load(self.temp_output)
                pygame.mixer.music.play()
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play audio:\n{e}")
            
        self.lbl_status.configure(text="")
        self.btn_play.configure(state="normal")
        self.is_processing = False

    def save_audio_thread(self):
        if not self.file_path:
            messagebox.showwarning("Warning", "Load an audio file first!")
            return
            
        save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV file", "*.wav")])
        if not save_path:
            return
            
        self.is_processing = True
        self.lbl_status.configure(text="Saving audio, please wait...")
        self.btn_save.configure(state="disabled")
        
        threading.Thread(target=self._save_task, args=(save_path,), daemon=True).start()

    def _save_task(self, save_path):
        if self.process_audio(save_path):
            messagebox.showinfo("Success", f"Saved to {save_path}")
            
        self.lbl_status.configure(text="")
        self.btn_save.configure(state="normal")
        self.is_processing = False

if __name__ == "__main__":
    app = PitchShifterApp()
    app.mainloop()