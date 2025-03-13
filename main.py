import os
import configparser
import tkinter as tk
from tkinter import messagebox
import threading
import keyboard
import sounddevice as sd
import soundfile as sf
import pyperclip
import pyautogui
import pystray
from PIL import Image, ImageDraw
from groq import Groq
import math
import time
import winsound  # Built-in Windows module for playing sounds
import numpy as np  # For handling recorded data
import io  # For in-memory file handling

# --- Configuration Helpers ---

CONFIG_FILE = "config.ini"

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def get_api_key():
    config = load_config()
    if 'API' in config and 'key' in config['API']:
        return config['API']['key']
    return None

def get_hotkey():
    config = load_config()
    if 'HOTKEY' in config and 'shortcut' in config['HOTKEY']:
        return config['HOTKEY']['shortcut']
    return "ctrl+space"  # Default hotkey

# --- Global Hotkey Registration ---

hotkey_id = None

def update_hotkey():
    global hotkey_id
    try:
        if hotkey_id is not None:
            keyboard.remove_hotkey(hotkey_id)
        hotkey_id = keyboard.add_hotkey(get_hotkey(), hotkey_handler)
        print("Hotkey updated to:", get_hotkey())
    except Exception as e:
        print("Error updating hotkey:", e)

# --- Tray Icon Image Functions ---

def create_default_icon():
    width, height = 32, 32
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 24, 24), fill='white')
    return image

def create_record_icon():
    width, height = 32, 32
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 24, 24), fill='red')
    return image

def create_spinner_frame(angle):
    width, height = 32, 32
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    center = (16, 16)
    length = 10
    rad = math.radians(angle)
    end_x = center[0] + length * math.cos(rad)
    end_y = center[1] + length * math.sin(rad)
    draw.line([center, (end_x, end_y)], fill='white', width=3)
    return image

def refresh_icon():
    if hasattr(icon, 'update_icon'):
        icon.update_icon()
    elif hasattr(icon, 'update_menu'):
        icon.update_menu()

def set_icon_default():
    global icon
    icon.icon = create_default_icon()
    refresh_icon()

def set_icon_recording():
    global icon
    icon.icon = create_record_icon()
    refresh_icon()

# --- Spinner Animation ---

spinner_active = False
spinner_thread = None

def animate_spinner():
    global spinner_active, icon
    frames = [create_spinner_frame(angle) for angle in range(0, 360, 30)]
    frame_index = 0
    while spinner_active:
        icon.icon = frames[frame_index]
        refresh_icon()
        frame_index = (frame_index + 1) % len(frames)
        time.sleep(0.1)

def start_spinner():
    global spinner_active, spinner_thread
    spinner_active = True
    spinner_thread = threading.Thread(target=animate_spinner, daemon=True)
    spinner_thread.start()

def stop_spinner():
    global spinner_active
    spinner_active = False
    time.sleep(0.15)  # Allow spinner to stop cleanly
    set_icon_default()

# --- Sound Playback Function ---

def play_sound():
    winsound.Beep(440, 150)  # A 440 Hz beep for 150 ms

# --- Settings Window (Tkinter) ---

def show_settings():
    settings_window = tk.Tk()
    settings_window.title("Settings")
    settings_window.resizable(False, False)

    # API Key Section
    tk.Label(settings_window, text="Enter API Key:").pack(padx=10, pady=(10, 5))
    api_key_var = tk.StringVar()
    api_key_entry = tk.Entry(settings_window, textvariable=api_key_var, width=50)
    api_key_entry.pack(padx=10, pady=5)
    current_key = get_api_key()
    if current_key:
        api_key_var.set(current_key)
    else:
        messagebox.showwarning("API Key Not Set", "No API key is set. Please enter your API key.")

    # Hotkey Section with Live Capture
    tk.Label(settings_window, text="Set Hotkey (click here and press desired keys):").pack(padx=10, pady=(10, 5))
    hotkey_var = tk.StringVar()
    hotkey_entry = tk.Entry(settings_window, textvariable=hotkey_var, width=50)
    hotkey_entry.pack(padx=10, pady=5)
    hotkey_var.set(get_hotkey())

    def on_hotkey_focus_in(event):
        event.widget.current_hotkey = []
        hotkey_var.set("")

    def on_hotkey_key(event):
        if not hasattr(event.widget, "current_hotkey"):
            event.widget.current_hotkey = []
        if event.keysym not in event.widget.current_hotkey:
            event.widget.current_hotkey.append(event.keysym)
        mapping = {
            "Control_L": "ctrl", "Control_R": "ctrl",
            "Shift_L": "shift", "Shift_R": "shift",
            "Alt_L": "alt", "Alt_R": "alt",
            "Super_L": "win", "Super_R": "win"
        }
        display_keys = [mapping.get(key, key.lower()) for key in event.widget.current_hotkey]
        hotkey_var.set("+".join(display_keys))
        return "break"

    hotkey_entry.bind("<FocusIn>", on_hotkey_focus_in)
    hotkey_entry.bind("<KeyPress>", on_hotkey_key)

    def save_settings():
        key = api_key_var.get().strip()
        hotkey_str = hotkey_var.get().strip()
        if not key:
            messagebox.showwarning("Invalid Key", "API key cannot be empty.")
            return
        if not hotkey_str:
            messagebox.showwarning("Invalid Hotkey", "Hotkey cannot be empty.")
            return

        config = load_config()
        if 'API' not in config:
            config['API'] = {}
        config['API']['key'] = key

        if 'HOTKEY' not in config:
            config['HOTKEY'] = {}
        config['HOTKEY']['shortcut'] = hotkey_str

        save_config(config)
        messagebox.showinfo("Settings Saved", "Settings saved successfully.")
        update_hotkey()
        settings_window.destroy()

    tk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)
    settings_window.mainloop()

# --- Groq Client Initialization ---

client = None

def init_groq_client():
    key = get_api_key()
    if key:
        os.environ["GROQ_API_KEY"] = key
    else:
        print("Warning: API key is not set. Please set it in the settings.")
    return Groq()

# --- Audio Recording and Processing with Toggle Support ---

# Global variables for recording state
is_recording = False
recording_data = []       # To accumulate audio chunks
recording_stream = None   # The InputStream object
recording_stop_event = threading.Event()

def start_recording():
    global is_recording, recording_data, recording_stream, recording_stop_event
    is_recording = True
    recording_data = []         # Reset recorded data
    recording_stop_event.clear()  # Clear any previous stop event

    def callback(indata, frames, time_info, status):
        recording_data.append(indata.copy())
        if recording_stop_event.is_set():
            raise sd.CallbackStop

    recording_stream = sd.InputStream(callback=callback, channels=1, samplerate=44100)
    recording_stream.start()
    print("Recording started.")

def stop_recording():
    global is_recording, recording_stream, recording_stop_event
    if is_recording:
        recording_stop_event.set()
        time.sleep(0.2)  # Give the callback time to exit gracefully
        recording_stream.stop()
        recording_stream.close()
        is_recording = False
        print("Recording stopped.")
        if recording_data:
            audio_array = np.concatenate(recording_data, axis=0)
            audio_file = io.BytesIO()
            sf.write(audio_file, audio_array, 44100, format='WAV')
            audio_file.seek(0)
            return audio_file
        else:
            print("No audio recorded.")
            return None
    return None

def send_to_api(audio_file):
    global client
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )
        return transcription.text
    except Exception as e:
        print("Error during transcription:", e)
        return ""

def paste_text(text):
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

# --- Hotkey Handler: Toggle Start/Stop Recording ---

def hotkey_handler():
    global is_recording
    if not is_recording:
        play_sound()  # Beep on start
        set_icon_recording()
        start_recording()
    else:
        audio_file = stop_recording()
        if audio_file:
            start_spinner()
            transcript = send_to_api(audio_file)
            stop_spinner()
            if transcript:
                paste_text(transcript)
            else:
                print("No transcript received.")
            audio_file.close()  # Close the BytesIO object
        else:
            print("No audio file to process.")

# --- System Tray Icon Setup ---

def settings_action(icon, item):
    threading.Thread(target=show_settings).start()

def quit_action(icon, item):
    icon.stop()

menu = pystray.Menu(
    pystray.MenuItem('Settings', settings_action),
    pystray.MenuItem('Quit', quit_action)
)

icon = pystray.Icon("GroqTranscriber", create_default_icon(), "Groq Transcriber", menu)

# --- Main Application Logic ---

def start_app():
    global client
    client = init_groq_client()
    update_hotkey()
    print("Hotkey ({}) registered. Listening for input...".format(get_hotkey()))
    keyboard.wait()

if __name__ == "__main__":
    threading.Thread(target=start_app, daemon=True).start()
    icon.run()
