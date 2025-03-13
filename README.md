# Groq Transcriber

**Groq Transcriber** is a lightweight, system tray application that allows users to record audio, transcribe it using the Groq API, and paste the transcribed text into any application. It supports hotkey toggling for recording and provides a simple settings interface for configuring the API key and hotkey. Its basically a bare bones super whisper clone.

## Features
- **Hotkey Toggle**: Start and stop recording with a customizable hotkey (default: `ctrl+alt+r`).
- **System Tray Integration**: Runs in the background with a tray icon for easy access to settings and quitting.
- **In-Memory Audio Processing**: Avoids temporary files by handling audio data in memory, ensuring smooth operation.
- **API Integration**: Uses the Groq API for fast and accurate transcription.
- **Clipboard Support**: Automatically copies the transcription to the clipboard and pastes it using `ctrl+v`.

## Installation

### Prerequisites
- Python 3.6 or higher
- A Groq API key (sign up at [Groq's website](https://groq.com/))

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/groq-transcriber.git
   cd groq-transcriber
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, install the dependencies manually:

   ```bash
   pip install sounddevice soundfile groq pystray pillow pyperclip pyautogui keyboard numpy
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage
### Set Up API Key
- Right-click the tray icon and select **"Settings"**.  
- Enter your Groq API key and save.

### Recording Audio
- Press the hotkey (default: `ctrl+space`) to start recording.  
- Press the hotkey again to stop recording and process the audio.

### Transcription
- The recorded audio is transcribed using the Groq API.  
- The transcribed text is automatically pasted into the active application.

### Customizing Hotkey
- In the settings window, click on the hotkey field and press your desired key combination to set a new hotkey.
