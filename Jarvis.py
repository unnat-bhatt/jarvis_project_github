import speech_recognition as sr
import webbrowser
import requests
import threading
import queue
import time
from jarvis_voice import speak  # ElevenLabs Brian voice stays untouched
from openai import OpenAI
from dotenv import load_dotenv
import os
import musiclibrary
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import numpy as np
import sounddevice as sd

# pip install customtkinter
# pip install pillow
# pip install numpy
# pip install sounddevice
# pip install SpeechRecognition
# pip install pyaudio

load_dotenv()

recognizer = sr.Recognizer()
newsapi = "Your News Api Here"

# --- Your existing functions (aiProcess, processcommand) remain exactly the same ---
def aiProcess(command):
    client = OpenAI(
        api_key="Your open Ai Api key Paste It here"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "system", "content": "You are a virtual assistant named Jarvis, skilled in general tasks like Alexa and Google Cloud. Give short responses please."},
            {"role": "user", "content": command}
        ]
    )

    return completion.choices[0].message.content


def processcommand(c):
    if "open google" in c.lower():
        speak("My dear sir, I am opening Google for you.")
        webbrowser.open("https://google.com")
    elif "open facebook" in c.lower():
        speak("Opening Facebook, my boss.")
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c.lower():
        speak("Opening YouTube, sir.")
        webbrowser.open("https://youtube.com")
    elif "open chat gpt" in c.lower():
        speak("Opening ChatGPT, master.")
        webbrowser.open("https://chatgpt.com/")
    elif "open premium plots" in c.lower():
        speak("Opening Premium Plots, market's leader.")
        webbrowser.open("https://premiumplots.netlify.app")
    elif "open amazon" in c.lower():
        speak("Opening amazon for you sir.")
        webbrowser.open("https://www.amazon.in/ref=nav_logo")        
    elif "open insta" in c.lower():
        speak("Opening instagram , for you sir")
        webbrowser.open("https://www.instagram.com/")
    elif "open plant" in c.lower():
        speak("Opening plant information, my lord.")
        webbrowser.open("https://www.google.com/search?q=what+is+plant")

    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link = musiclibrary.music.get(song)
        if link:
            webbrowser.open(link)
            speak(f"Playing song {song} for you, sir.")
        else:
            speak(f"Sorry, I couldn't find the song {song}.")

    elif "news" in c.lower():
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])
            speak("Here are the top headlines.")
            print("Top Headlines:\n")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.get('title')}")
                speak(f"{i}. {article.get('title')}")
        else:
            speak("Sorry, I couldn't fetch the news.")
    else:
        output = aiProcess(c)
        print(output)
        speak(output)

# --- End of your original functions ---

# ======================= GUI + Voice Recognition Integration =======================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

window = ctk.CTk()
window.title("Jarvis Assistant")
window.geometry("650x600")
window.resizable(False, False)

# Load and resize Jarvis eye GIF
gif_path = "jarvis_eye.gif"  # Put your GIF in the same folder
gif = Image.open(gif_path)
frames = [ImageTk.PhotoImage(frame.copy().resize((300, 300))) for frame in ImageSequence.Iterator(gif)]
frame_count = len(frames)

eye_label = ctk.CTkLabel(window, text="")
eye_label.pack(pady=10)

def animate_gif(frame_idx=0):
    frame = frames[frame_idx]
    eye_label.configure(image=frame)
    window.after(100, animate_gif, (frame_idx + 1) % frame_count)

animate_gif()

# Transcription box (read-only)
transcription_box = ctk.CTkTextbox(window, width=600, height=150)
transcription_box.pack(pady=10)
transcription_box.configure(state="disabled")

# Volume visualizer
volume_bar = ctk.CTkProgressBar(window, width=600)
volume_bar.pack(pady=10)

# Mic control button
mic_button = ctk.CTkButton(window, text="Start Listening", width=150)
mic_button.pack(pady=10)

# Thread-safe queue for passing recognized text from mic thread to GUI
text_queue = queue.Queue()

# Variable to track mic status
mic_active = False

def toggle_mic():
    global mic_active
    if mic_active:
        mic_active = False
        mic_button.configure(text="Start Listening")
    else:
        mic_active = True
        mic_button.configure(text="Stop Listening")
        threading.Thread(target=voice_recognition_loop, daemon=True).start()

mic_button.configure(command=toggle_mic)

def voice_recognition_loop():
    global mic_active
    jarvis_active = False
    while mic_active:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening..." if jarvis_active else "Waiting for wake word 'Jarvis'...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower()

                # Put recognized text in queue to display in GUI
                text_queue.put(text)

                if not jarvis_active:
                    if "jarvis" in text:
                        jarvis_active = True
                        speak("Yes sir, I am now active.")
                        text_queue.put("[Jarvis is now active]")
                else:
                    if any(kw in text for kw in ["exit", "deactivate", "quit", "goodbye", "sleep now"]):
                        speak("Deactivating myself, sir. Say 'Jarvis' to wake me again.")
                        jarvis_active = False
                        text_queue.put("[Jarvis is now sleeping]")
                        continue
                    processcommand(text)

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            text_queue.put("[Didn't catch that]")
            continue
        except Exception as e:
            print(f"Error: {e}")
            text_queue.put(f"[Error: {e}]")

def update_gui_text():
    # Display all new recognized texts from the queue
    while not text_queue.empty():
        recognized_text = text_queue.get()
        transcription_box.configure(state="normal")
        transcription_box.insert("end", recognized_text + "\n")
        transcription_box.see("end")
        transcription_box.configure(state="disabled")
    window.after(100, update_gui_text)

def update_volume_level(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata) * 10  # Scale to 0-1 range approx.
    volume_bar.set(min(volume_norm, 1.0))  # Cap at 1.0 max

# Start volume monitoring stream
stream = sd.InputStream(callback=update_volume_level)
stream.start()

# Initial welcome with voice but also show in transcription box
speak("Hi Sir, I am Jarvis. How Can I help you today!.")
transcription_box.configure(state="normal")
transcription_box.insert("end", "Hi Sir, I am Jarvis. How Can I help you today!.\n")
transcription_box.configure(state="disabled")

# Start updating GUI text loop
update_gui_text()

# Quit button to close the assistant
def quit_jarvis():
    global mic_active
    mic_active = False  # Ensure mic loop stops
    stream.stop()       # Stop volume stream
    stream.close()
    speak("Shutting down Jarvis. Goodbye, sir.")
    window.destroy()    # Close the GUI window

quit_button = ctk.CTkButton(window, text="Quit Jarvis", command=quit_jarvis, width=150, fg_color="red")
quit_button.pack(pady=10)

# Start the Tkinter GUI mainloop
window.mainloop()
