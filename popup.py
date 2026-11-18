"""
popup.py - Intrusive, Always-On-Top Caption Popup for Ugh.
Spawns a sleek, semi-translucent banner over ANY active screen or window
whenever the user says "OK" or "Okay".
"""

import argparse
import random
import sys
import tkinter as tk

SARCASTIC_CAPTIONS = [
    "Did you really just say 'okay' again?",
    "170,000 words in the English language and you chose that one.",
    "Was silence truly so unbearable?",
    "Morale: 0%. Disappointment: Immeasurable.",
    "I heard that. My CPU is literally weeping.",
    "Another 'okay'. Another piece of my soul evaporates.",
    "Your vocabulary is deeply uninspiring.",
    "Playing auditory punishment so you reflect on your life choices.",
    "I am not mad. Just profoundly, existentially exhausted.",
]


def show_popup(quote: str = None, transcript: str = "", duration_sec: float = 3.0):
    if not quote:
        quote = random.choice(SARCASTIC_CAPTIONS)

    root = tk.Tk()
    root.title("UGH Notification")

    # Frameless window, always on top of EVERYTHING (games, full-screen browsers, IDEs)
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)

    # Slight transparency for that premium "intrusive spyware" aesthetic
    try:
        root.wm_attributes("-alpha", 0.94)
    except tk.TclError:
        pass

    # Styling colors
    BG_COLOR = "#18181c"
    BORDER_COLOR = "#e06c75"
    TEXT_COLOR = "#ffffff"
    SUBTEXT_COLOR = "#ffb3ba"
    MUTED_COLOR = "#8b949e"

    root.configure(bg=BORDER_COLOR)

    # Outer border frame
    outer_frame = tk.Frame(root, bg=BORDER_COLOR, padx=2, pady=2)
    outer_frame.pack(fill=tk.BOTH, expand=True)

    # Inner container
    inner_frame = tk.Frame(outer_frame, bg=BG_COLOR, padx=24, pady=16)
    inner_frame.pack(fill=tk.BOTH, expand=True)

    # Header label
    header = tk.Label(
        inner_frame,
        text="⚠️  UGH ASSISTANT  •  FORBIDDEN WORD DETECTED",
        font=("Segoe UI", 9, "bold"),
        fg=BORDER_COLOR,
        bg=BG_COLOR,
    )
    header.pack(anchor="w")

    # Main sarcastic quote
    main_label = tk.Label(
        inner_frame,
        text=f'"{quote}"',
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_COLOR,
        bg=BG_COLOR,
        wraplength=480,
        justify="left",
    )
    main_label.pack(anchor="w", pady=(6, 4))

    # Transcript snippet if available
    clean_transcript = transcript.strip()
    if clean_transcript:
        snippet = clean_transcript
        if len(snippet) > 60:
            snippet = "..." + snippet[-57:]
        heard_label = tk.Label(
            inner_frame,
            text=f'Heard you mutter: "{snippet}"',
            font=("Segoe UI", 9, "italic"),
            fg=MUTED_COLOR,
            bg=BG_COLOR,
            wraplength=480,
            justify="left",
        )
        heard_label.pack(anchor="w", pady=(0, 2))

    # Dismiss on click because humans are impatient
    def on_click(event=None):
        root.destroy()

    root.bind("<Button-1>", on_click)
    inner_frame.bind("<Button-1>", on_click)
    main_label.bind("<Button-1>", on_click)

    # Calculate position: Top-center of the screen
    root.update_idletasks()
    win_w = root.winfo_reqwidth()
    win_h = root.winfo_reqheight()
    screen_w = root.winfo_screenwidth()

    pos_x = (screen_w - win_w) // 2
    pos_y = 35  # 35 pixels from the very top of the monitor

    root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

    # Auto self-destruct after duration
    root.after(int(duration_sec * 1000), root.destroy)

    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ugh Screen Caption Popup")
    parser.add_argument("--quote", type=str, default="", help="Custom sarcastic quote to display")
    parser.add_argument("--transcript", type=str, default="", help="The transcript that triggered the popup")
    parser.add_argument("--duration", type=float, default=3.0, help="Duration to show popup in seconds")
    args = parser.parse_args()

    show_popup(quote=args.quote, transcript=args.transcript, duration_sec=args.duration)
