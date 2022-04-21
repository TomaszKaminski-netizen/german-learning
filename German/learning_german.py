"""This script is for learning German. It should work both on Windows and
Linux. Developed with Python 3.7.9."""
#pylint: disable=multiple-statements

from os.path import isfile, abspath, dirname
from os import chdir, _exit
from random import shuffle
from collections import ChainMap, defaultdict
from functools import partial
from itertools import permutations, chain
from datetime import datetime
from glob import glob
from re import sub, match
import tkinter as tk
from time import sleep
import json

from playsound import playsound, PlaysoundException
import requests
from bs4 import BeautifulSoup

from german_language import VERBS_DICT, ADVERBS_DICT

CONJUGATION_CATEGORIES = ("Präsens", "Präteritum", "Perfekt", "Plusquamperfekt", "Futur I",
                          "Futur II", "Imperativ")
PRONOUNS = ("ich", "du", "er/sie/es", "wir", "ihr", "sie")

####################################################################################################

class Starting_layout():
    """The widget layout for the main menu."""
    def __init__(self):
        all_vocab = [VERBS_DICT, ADVERBS_DICT]
        tk.Label(text="Choose what to practice.").pack()
        tk.Button(text="German to English", command=lambda:
                  translate_words(all_vocab, "ger_to_eng")).pack()
        tk.Button(text="English to German", command=lambda:
                  translate_words(all_vocab, "eng_to_ger", tuple(self.cats))).pack()
        tk.Button(text="Listening", command=test_listening).pack()
        tk.Button(text="Verb conjugation", command=lambda:
                  test_conjugation(tuple(self.cats))).pack()
        tk.Label(text="Toggle which verb conjugations to practice.").pack()

        self.cats, self.cat_buttons = list(), dict()
        for cat in CONJUGATION_CATEGORIES:
            self.cat_buttons[cat] = tk.Button(text=cat, bg="Red",
                                              command=partial(self.toggle_category, cat))
            self.cat_buttons[cat].pack()
        # These for categories are enabled by default.
        for cat in CONJUGATION_CATEGORIES[:3] + CONJUGATION_CATEGORIES[-1:]:
            self.toggle_category(cat)

    def toggle_category(self, cat):
        """
        Args:
            cat (str): name of the conjugation category of interest
        """
        if cat in self.cats:
            self.cats.remove(cat)
            self.cat_buttons[cat].configure(bg="Red")
        else:
            self.cats.append(cat)
            self.cat_buttons[cat].configure(bg="Green")


class Exercise_layout():
    """The customizable widget layout for various language exercises."""
    #* Note that using 'answer_type=tk.Entry()' as a default argument caused problems.
    def __init__(self, enter_or_click, answer_type, ger_char=True, extra_button=False):
        """
        Args:
            enter_or_click (str): _description_
            answer_type (tkinter object): _description_
            ger_char (bool, optional): _description_. Defaults to True.
            extra_button (bool, optional): _description_. Defaults to False.
        """
        # Clearing the previous layout.
        for widget in window.winfo_children():
            # Selecting only widgets that have been made visible through .pack()
            if widget.winfo_ismapped():
                widget.destroy()

        # Adding text and text fields.
        self.prompt_label, self.feedback_label, self.answer = tk.Label(), tk.Label(), answer_type
        self.prompt_label.pack() ; self.feedback_label.pack() ; self.answer.pack()
        self.answer.focus_set() # Moving the cursor to the answer box.

        # Adding additional buttons.
        if extra_button:
            extra_button.pack()

        # Setting up how to continue / progress through the GUI.
        self.wait_var = tk.BooleanVar()
        if enter_or_click == "enter": # By pressing the enter keyboard key.
            window.bind("<Return>", lambda _: self.wait_var.set(1))
        elif enter_or_click == "click": # By clicking a GUI button.
            self.button_next = tk.Button(text="Submit answer", command=lambda: self.wait_var.set(1))
            self.button_next.pack()

        # Adding buttons for German characters.
        if ger_char:
            horizontal = tk.Frame(window)
            horizontal.pack()
            for char in "äüöß":
                # Need to use partial instead of lambda, to avoid the cell-var-from-loop problem.
                tk.Button(horizontal, text=char,
                          command=partial(self.answer.insert, tk.INSERT, char)
                          ).pack(side=tk.RIGHT)

####################################################################################################

def _playsound(audio):
    """The 'playsound' function from the 'playsound' library experiences random
    bugs, which freeze the GUI window. This function is meant to handle those
    bugs.

    Args:
        audio (str): absolute path to the audio file of interest
    """
    #TODO: Find a way to play audio files with special German characters in them.
    try:
        playsound(audio)
    except PlaysoundException:
        print(f"Error playing '{audio}'")


def conjugate_verb(verb):
    """_summary_

    Args:
        verb (str): _description_

    Returns:
        dict: _description_
    """
    verb = verb.lower().replace("sich", "").strip()
    page = requests.get("https://pl.pons.com/odmiana-czasownikow/niemiecki/" + verb)
    parsed_page = BeautifulSoup(page.content, "html.parser")
    if parsed_page.find("div", class_="alert alert-block alert-warning"):
        print(f"Couldn't find verb {verb}, stopping.")
        return False

    # Some verbs have multiple forms of conjugation (e.g. with and without 'sich'), which are stored
    # on different webpages. Here the right page is found and loaded.
    alternate_conjug = parsed_page.find("h2", class_="ft-variant-links-label")
    if alternate_conjug:
        print(f"'{verb}' has multiple forms.")
        hyperlinks = alternate_conjug.parent.find_all("a")
        if "sich " in verb:
            right_conjug = "Zaimek zwrotny w bierniku"
        else:
            right_conjug = "Koniugacja z czasownikiem" # Haben or sein
        right_link = list(filter(lambda link: link.text.startswith(right_conjug), hyperlinks))
        page = requests.get("https://pl.pons.com" + right_link[0]["href"])
        parsed_page = BeautifulSoup(page.content, "html.parser")

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


def test_conjugation(categories, verbs="all"): #pylint: disable=inconsistent-return-statements
    """_summary_

    Args:
        categories (tuple): _description_
        verbs (str, optional): _description_. Defaults to "all".
    """
    if not categories:
        return False
    if verbs == "all":
        verbs = list(chain(*[key.split(" / ") for key in VERBS_DICT]))
        shuffle(verbs)
    for verb in verbs:
        conjugations = conjugate_verb(verb)
        if not conjugations:
            continue
        for category, right_answer in conjugations.items():
            if category not in categories:
                continue

            layout = Exercise_layout("click", tk.Text(height=len(right_answer), width=40))
            layout.prompt_label.configure(text=f"Conjugate '{verb}' in {category}")
            # Auto-filling pronouns for the Indikativ mood.
            for row in right_answer:
                if row.split()[0] in PRONOUNS:
                    layout.answer.insert(tk.END, row.split()[0] + " \n")
            window.wait_variable(layout.wait_var)

            raw_answer = layout.answer.get("1.0", tk.END) # All text in the text box
            # Splitting into rows and removing excess whitespace (including empty rows).
            cleaned_answer = filter(bool, [row.strip() for row in raw_answer.split("\n")])
            if set(cleaned_answer) == set(right_answer):
                layout.feedback_label.configure(text="Correct.")
            else:
                layout.feedback_label.configure(text="Wrong - the right answer is:\n" +
                                                "\n".join(right_answer))
            layout.button_next.configure(text="Continue to next question.")
            window.wait_variable(layout.wait_var)

    layout.prompt_label.configure(text="All finished.")


def translate_words(vocab, direction, conjugate=()):
    """_summary_

    Args:
        vocab (list): _description_
        direction (str): _description_
        conjugate (tuple, optional): _description_
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
    if direction == "ger_to_eng":
        # Removing round & square brackets and everything inside them. Also flipping the word order.
        vocab = [(sub(r"\s*[\[\(].+[\]\)]\s*", "", item[1]), item[0]) for item in vocab]
    shuffle(vocab)
    vocab = sorted(vocab, key=lambda item: memory[item[1]] if item[1] in memory else "")

    for words in vocab:
        layout = Exercise_layout("enter", tk.Entry(), ger_char=bool(direction == "eng_to_ger"))
        # Complex as to deal with answers that contain more than two words, separated by "/".
        answer_pieces = words[0].split(" / ")
        rearranged = permutations(answer_pieces, len(answer_pieces))
        right_answers = [" / ".join(item) for item in rearranged]
        layout.prompt_label.configure(text=f"Translate '{words[1]}':\n")
        window.wait_variable(layout.wait_var)

        if layout.answer.get() in right_answers:
            layout.feedback_label.configure(text="Correct.")
            memory[words[1]] = datetime.now().strftime(r"%m-%d")
        else:
            layout.feedback_label.configure(text=f"Wrong - the right answer is '{words[0]}'")
        for item in answer_pieces:
            sound_name = abspath(f"vicki-{item.replace(' ', '_')}.mp3")
            if isfile(sound_name):
                _playsound(sound_name)
                sleep(0.25)
        window.wait_variable(layout.wait_var)

        if (words[0] in VERBS_DICT) and conjugate:
            test_conjugation(conjugate, answer_pieces)

    layout.prompt_label.configure(text="All finished.")


def test_listening():
    """_summary_
    """
    audio_files = glob("vicki-*.mp3")
    shuffle(audio_files)
    for audio_file in audio_files:
        extra_button = tk.Button(text="Click to hear the word again.",
                                 command=partial(_playsound, abspath(audio_file)))
        layout = Exercise_layout("enter", tk.Entry(), extra_button=extra_button)
        layout.prompt_label.configure(text="Write down the word you heard.")
        _playsound(abspath(audio_file))
        window.wait_variable(layout.wait_var)

        right_answer = match(r"vicki-(.+).mp3", audio_file).group(1).replace("_", " ")
        if layout.answer.get() == right_answer:
            response = "Correct."
        else:
            response = f"Wrong - the right answer is '{right_answer}'"
        all_vocab = ChainMap(VERBS_DICT, ADVERBS_DICT)
        for ger, eng in all_vocab.items():
            if right_answer in ger.split(" / "):
                response += f"\nIt means '{eng}'"
                break
        layout.feedback_label.configure(text=response)
        window.wait_variable(layout.wait_var)

    layout.feedback_label.configure(text="All finished.")

####################################################################################################

if __name__ == "__main__":
    chdir(dirname(abspath(__file__)))
    window = tk.Tk()
    window.geometry("700x700")
    window.option_add("*font", "size 19") # Changing the default font size
    Starting_layout()
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
