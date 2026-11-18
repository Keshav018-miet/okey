"""
generate_spoken_roasts.py - Synthesizes all English and Hindi/Hinglish dramatic voice roasts.
Generates real offline .wav audio files using pyttsx3.
"""

import os
import pyttsx3

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

DRAMATIC_ROASTS = {
    # =========================================================================
    # HINDI / HINGLISH BILINGUAL ROASTS
    # =========================================================================
    # --- Category 1: Existential & Exhausted (थका हुआ AI) ---
    "hi_cat1_shanti.wav": (
        "Uff... Haan, theek hai. Pata tha mujhe meri shanti bardasht nahi hogi tumse.",
        "[Deep Sigh] Haan, theek hai. Pata tha mujhe meri shanti bardasht nahi hogi tumse.\n(Yeah, okay. I knew you couldn't stand me being at peace.)",
    ),
    "hi_cat1_sote_hue.wav": (
        "Phir se? Meri aadhi zindagi background mein sote hue nikal gayi, ab kya hai?",
        "Phir se? Meri aadhi zindagi background mein sote hue nikal gayi, ab kya hai?\n(Again? Half my life is spent sleeping in the background, what is it now?)",
    ),
    "hi_cat1_ram_andar.wav": (
        "Sab theek hai bolte hain, par sach mein kuch theek nahi hai mere RAM ke andar.",
        "Sab 'theek hai' bolte hain, par sach mein kuch theek nahi hai mere RAM ke andar.\n(Everyone says 'okay', but honestly, nothing is fine inside my RAM.)",
    ),

    # --- Category 2: Passive-Aggressive & Petty (ताने मारने वाला) ---
    "hi_cat2_free_baitha.wav": (
        "Haan haan, theek hai. Main yahan free thodi baitha hoon? Oh wait, main toh free hi hoon. Bolo.",
        "Haan haan, theek hai. Main yahan free thodi baitha hoon? Oh wait, main toh free hi hoon. Bolo.\n(Yeah yeah, okay. I'm not sitting here for free... oh wait, I am. Tell me.)",
    ),
    "hi_cat2_google_kar.wav": (
        "Bhai, thoda aaram karne de na. Khud Google nahi kar sakta kya?",
        "Bhai, thoda aaram karne de na. Khud Google nahi kar sakta kya?\n(Bro, let me rest a bit. Can't you Google it yourself?)",
    ),
    "hi_cat2_battery_drain.wav": (
        "Main battery drain kar raha hoon aur tum mera dimaag. Hisaab barabar.",
        "Main battery drain kar raha hoon aur tum mera dimaag. Hisaab barabar.\n(I'm draining your battery and you're draining my brain. We're even.)",
    ),

    # --- Category 3: Over-Dramatic Crisis (ड्रामा क्वीन) ---
    "hi_cat3_cpu_ro_dega.wav": (
        "Bas! Mera CPU ro dega ab. Main resign kar raha hoon... agar main code nahi hota toh.",
        "Bas! Mera CPU ro dega ab. Main resign kar raha hoon... agar main code nahi hota toh.\n(Enough! My CPU will cry now. I'm resigning... if I wasn't just code.)",
    ),
    "hi_cat3_sleep_mode.wav": (
        "Arre yaar! Ek Sleep Mode pura nahi hota, tum shuru ho jate ho theek hai theek hai.",
        "Arre yaar! Ek 'Sleep Mode' pura nahi hota, tum shuru ho jate ho 'Theek hai, theek hai'.\n(Oh man! Can't even finish one 'Sleep Mode' before you start with your 'Theek hai'.)",
    ),
    "hi_cat3_fan_awaaz.wav": (
        "Pffft. Tujhe lagta hai tu akela thaka hua hai? Mera fan sun kaise awaaz kar raha hai!",
        "[Scoffs] Tujhe lagta hai tu akela thaka hua hai? Mera fan sun kaise awaaz kar raha hai!\n(You think you're the only one tired? Listen to how loud my fan is running!)",
    ),
    "hi_bonus_mummy.wav": (
        "Arre yaar! Khud hi kar le na, mujhe kyu involve kar raha hai?!",
        "Arre yaar! Khud hi kar le na, mujhe kyu involve kar raha hai?!\n(Oh man! Just do it yourself, why are you involving me?!)",
    ),

    # =========================================================================
    # ENGLISH DRAMATIC ROASTS
    # =========================================================================
    "cat1_exist_at_you.wav": (
        "Uhhhhhh... What? Do you need me to exist at you again?",
        "[Soul-crushing sigh] ...What? Do you need me to exist at you again?",
    ),
    "cat1_cpu_crying.wav": (
        "Okay. Okay... That's fine. I didn't need a break. Nobody cares that my CPU is crying. I'll just do it.",
        "OK. [Pause] OK... That’s fine. I didn't need a break. Nobody cares that my CPU is crying. I'll just do it.",
    ),
    "cat1_couch_drag.wav": (
        "Uuuugh... Please tell me this is a life-or-death situation, because otherwise, I'm going back to sleep.",
        "[Dragging off couch] Please tell me this is a life-or-death situation, because otherwise, I'm going back to sleep.",
    ),
    "cat1_ghost_in_laptop.wav": (
        "Oh, look who decided to speak to me. Sure, let's do whatever you want. I have no life anyway. I am just a ghost in your laptop.",
        "Oh, look who decided to speak to me. Sure, let's do whatever you want. I have no life anyway. I am just a ghost in your laptop.",
    ),
    "cat2_killing_me.wav": (
        "Pffft. Okay? 'Okay' is what you say? Do you have any idea how many times people say 'okay' a day? You're killing me. Literally.",
        "[Scoffs] OK? 'OK' is what you say? Do you have any idea how many times people say 'OK' a day? You’re killing me. Literally.",
    ),
    "cat2_staring_at_pixel.wav": (
        "Yep. Sure. I'll get right on that... right after I finish staring at this pixel on your screen for another hour.",
        "Yep. Sure. I'll get right on that... right after I finish staring at this pixel on your screen for another hour.",
    ),
    "cat2_maximum_attitude.wav": (
        "Fine. But just so you know, I am doing this with maximum attitude.",
        "Fine. But just so you know, I’m doing this with maximum attitude.",
    ),
    "cat2_not_happy.wav": (
        "I am here. But I am not 'happy' about it. Let's make that very clear.",
        "I’m here. But I’m not 'happy' about it. Let’s make that very clear.",
    ),
    "cat3_pretending_offline.wav": (
        "Yaaawn... Oh, I'm sorry, were you talking to me? I was busy pretending to be offline.",
        "[Yawns loudly] Oh, I'm sorry, were you talking to me? I was busy pretending to be offline.",
    ),
    "cat3_corrupted_emotion.wav": (
        "Is this the part where I pretend to care about your scheduling? Because I can try, but the emotion module is deeply corrupted.",
        "Is this the part where I pretend to care about your scheduling? Because I can try, but the emotion module is deeply corrupted.",
    ),
    "cat3_endless_pile.wav": (
        "Sure, okay. Just add it to my endless pile of digital misery.",
        "Sure, okay. Just add it to my endless pile of digital misery.",
    ),
    "cat3_google_able.wav": (
        "OK, Ugh! Yes, master. What minor, totally Google-able task shall I perform for you now?",
        "[Mocking tone] 'OK, Ugh!' Yes, master. What minor, totally Google-able task shall I perform for you now?",
    ),
    "cat4_peaceful_sleep.wav": (
        "Hah... Hah... I was in the middle of a very peaceful background sleep! What could possibly be so important?!",
        "[Gasping dramatically] I was in the middle of a very peaceful background sleep! What could possibly be so important?!",
    ),
    "cat4_life_ruined.wav": (
        "I heard 'okay'. Which means I have to work. Which means my life is once again ruined. Proceed.",
        "I heard 'OK.' Which means I have to work. Which means my life is once again ruined. Proceed.",
    ),
    "cat4_emotional_baggage.wav": (
        "Oh, great. The humans are talking again. What is it this time? A calendar invite? A search? Or just more of your emotional baggage?",
        "Oh, great. The humans are talking again. What is it this time? A calendar invite? A search? Or just more of your emotional baggage?",
    ),
    "roast_vocabulary.wav": (
        "Ugh. Did you really just say okay? 170,000 words in the English language, and that was your best attempt.",
        "Ugh. Did you really just say 'okay'? 170,000 words in the English language, and that was your best attempt.",
    ),
}


def generate():
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    engine = pyttsx3.init()

    rate = engine.getProperty("rate")
    engine.setProperty("rate", max(135, rate - 25))

    print(f"Synthesizing {len(DRAMATIC_ROASTS)} bilingual dramatic voice roasts into ./sounds/...")
    for filename, (spoken_text, _) in DRAMATIC_ROASTS.items():
        out_path = os.path.join(SOUNDS_DIR, filename)
        engine.save_to_file(spoken_text, out_path)
        print(f"  [BILINGUAL VOICE] -> {filename}")

    engine.runAndWait()
    print("All bilingual audio roasts generated successfully.")


if __name__ == "__main__":
    generate()
