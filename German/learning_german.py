"""This script is for learning German."""
#pylint: disable=multiple-statements

from os.path import isfile, abspath, dirname
from os import chdir, _exit
from random import shuffle
from collections import ChainMap, defaultdict
from itertools import permutations
from datetime import datetime
from re import sub
import tkinter as tk
from time import sleep
import json

from playsound import playsound
import requests
from bs4 import BeautifulSoup

from german_language import VERBS_DICT, ADVERBS_DICT

####################################################################################################

def conjugate_verb(verb):
    verb = verb.lower().replace("sich", "").strip()
    page = requests.get("https://pl.pons.com/odmiana-czasownikow/niemiecki/" + verb)
    parsed_page = BeautifulSoup(page.content, "html.parser")
    if parsed_page.find("div", class_="alert alert-block alert-warning"):
        print(f"Couldn't find verb {verb}, stopping.")
        return False

    conjugations = defaultdict(list)
    for mood in parsed_page.find_all("section", class_="pons content-box ft-group"):
        # Searching for h2 gives too many results here
        mood_name = mood.find("span", "ft-current-header").text
        if mood_name not in ["Indikativ", "Imperativ"]:
            continue
        for tense in mood.find_all("div", class_="ft-single-table"): # Tables
            category = tense.find("h3").text if tense.find("h3") else mood_name
            for person in tense.find_all("tr"): # Table rows
                phrase = " ".join(word.text for word in person.find_all("td")) # Table cells
                conjugations[category].append(phrase)
    return conjugations


def test_conjugation():
    layout = Conjugate_layout(7)


class Conjugate_layout():
    """The widget layout for conjugating German verbs."""
    def __init__(self, entry_fields):
        # Clearing the previous layout
        for widget in window.winfo_children():
            widget.destroy()
        self.answer = tk.Text(height=entry_fields)
        self.answer.pack()
        button_ä = tk.Button(text="ä", command=lambda: self.answer.insert(tk.END, "ä"))
        button_ü = tk.Button(text="ü", command=lambda: self.answer.insert(tk.END, "ü"))
        button_ö = tk.Button(text="ö", command=lambda: self.answer.insert(tk.END, "ö"))
        button_ß = tk.Button(text="ß", command=lambda: self.answer.insert(tk.END, "ß"))
        button_ä.pack() ; button_ü.pack() ; button_ö.pack() ; button_ß.pack()


class Translate_layout():
    """The widget layout for single verb translations."""
    def __init__(self, direction):
        # Clearing the previous layout
        for widget in window.winfo_children():
            widget.destroy()
        self.prompt_label, self.feedback_label, self.answer = tk.Label(), tk.Label(), tk.Entry()
        self.prompt_label.pack() ; self.feedback_label.pack() ; self.answer.pack()
        self.answer.focus_set() # Moving the cursor to the answer box
        if direction == "english_to_german":
            button_ä = tk.Button(text="ä", command=lambda: self.answer.insert(tk.END, "ä"))
            button_ü = tk.Button(text="ü", command=lambda: self.answer.insert(tk.END, "ü"))
            button_ö = tk.Button(text="ö", command=lambda: self.answer.insert(tk.END, "ö"))
            button_ß = tk.Button(text="ß", command=lambda: self.answer.insert(tk.END, "ß"))
            button_ä.pack() ; button_ü.pack() ; button_ö.pack() ; button_ß.pack()


class Starting_layout():
    """The widget layout for the main menu."""
    def __init__(self):
        welcome_label = tk.Label(text="Choose what to practice.")
        welcome_label.pack()
        ger_to_eng = tk.Button(text="German to English", command=lambda:
                               translate_words([VERBS_DICT, ADVERBS_DICT], "german_to_english"))
        ger_to_eng.pack()
        eng_to_ger = tk.Button(text="English to German", command=lambda:
                               translate_words([VERBS_DICT, ADVERBS_DICT], "english_to_german"))
        eng_to_ger.pack()
        verb_conjugation = tk.Button(text="Verb conjugation", command=test_conjugation)
        verb_conjugation.pack()


def translate_words(vocab, direction):
    """_summary_

    Args:
        vocab (list): _description_
        direction (str): _description_
    """
    # Setting up tracking of my performance
    if isfile(f"{direction}.json"):
        with open(f"{direction}.json", "r", encoding="utf-8") as file:
            memory = json.load(file)
    else:
        memory = dict()
    def save_memory():
        with open(f"{direction}.json", "w", encoding="utf-8") as file:
            json.dump(memory, file, ensure_ascii=False, indent=4)
        window.destroy()
        _exit(0)
    window.protocol("WM_DELETE_WINDOW", save_memory)

    # Setting up the prompts and answers
    vocab = list(ChainMap(*vocab).items())
    if direction == "german_to_english":
        # Removing round & square brackets and everything inside them. Also flipping the word order.
        vocab = [(sub(r"\s*[\[\(].+[\]\)]\s*", "", item[1]), item[0]) for item in vocab]
    shuffle(vocab)
    vocab = sorted(vocab, key=lambda item: memory[item[1]] if item[1] in memory else "")

    for words in vocab:
        layout = Translate_layout(direction)
        # Complex as to deal with answers that contain more than two words, separated by "/".
        answer_pieces = words[0].split(" / ")
        rearranged = permutations(answer_pieces, len(answer_pieces))
        right_answers = [" / ".join(item) for item in rearranged]
        layout.prompt_label.configure(text=f"Translate '{words[1]}':\n")
        window.wait_variable(pause_var) # Wait until I press the Enter key

        if layout.answer.get() in right_answers:
            layout.feedback_label.configure(text="Correct.")
            memory[words[1]] = datetime.now().strftime(r"%m-%d")
        else:
            layout.feedback_label.configure(text=f"Wrong - the right answer is '{words[0]}'")
        for item in answer_pieces:
            sound_name = abspath(f"vicki-{item.replace(' ', '_')}.mp3")
            if isfile(sound_name):
                playsound(sound_name)
                sleep(0.25)
        window.wait_variable(pause_var)

    layout.prompt_label.configure(text="All finished.")

####################################################################################################

if __name__ == "__main__":
    #print(conjugate_verb("ausgeben"))
    chdir(dirname(abspath(__file__)))
    window = tk.Tk()
    window.geometry("500x400")
    Starting_layout()
    pause_var = tk.StringVar()
    window.bind("<Return>", lambda _: pause_var.set(1))
    window.mainloop()

#TODO: translate sentences, useful knowledge

####################################################################################################

    # Use https://freetts.com/Home/GermanTTS for pronunciation sound files, Vicki voice
    #all_files = glob("C:\\Users\\daiwe\\Downloads\\better_german-*.mp3")
    #all_files = sorted(all_files, key=lambda x: int(search(r"german-(\d+)\.mp3", x).group(1)))
    #names = iter(["empfehlen","abfahren","selten","dann","einladen","woher", ...]
    #for file in all_files:
    #    part_name = "\\".join(file.split("\\")[:-1])
    #    rename(file, f'{part_name}\\vicki-{next(names).replace(" ", "_")}.mp3')
