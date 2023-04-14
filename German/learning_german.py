"""This script is for learning German. It should work both on Windows and
Linux. Developed with Python 3.7.9."""
#pylint: disable=multiple-statements

from os.path import isfile, abspath, dirname
from os import chdir, _exit
from random import shuffle
from collections import ChainMap, defaultdict
from functools import partial
from statistics import mean, StatisticsError
from itertools import permutations, chain, count, cycle
from datetime import datetime
from glob import glob
from re import sub, search
import tkinter as tk
from time import sleep
import json

from pygame import mixer #* The playsound library did not work with special German characters
import requests
from bs4 import BeautifulSoup

from german_language import VERBS_DICT, ADVERBS_DICT, NOUNS_DICT, ADJECTIVES_DICT, TIPS, \
    DECLENSION_AFFIXES, DECLENSION_DICT, DECLENSION_ORDER, PREPOSITIONS_DICT

CORE_VERBS = ("dürfen", "können", "mögen", "müssen", "wollen", "sollen", "werden", "haben", "sein",
              "machen", "gehen", "fahren", "geben", "sehen")
CONJUGATION_CATEGORIES = ("Präsens", "Präteritum", "Perfekt", "Plusquamperfekt", "Futur I",
                          "Futur II", "Imperativ")
# Needs to be the same as found on https://pl.pons.com/odmiana-czasownikow/niemiecki
PRONOUNS = ("ich", "du", "er/sie/es", "wir", "ihr", "sie")

# Replaces all whitespace characters with (at most) single consecutive space. Also removes trailing
# and leading spaces. Can't ensures that slashes are flanked by one space on each side, because that
# would cause problems with "er/sie/es" during verb conjugation.
trim = lambda string: sub(r"\s+", " ", string.strip())

####################################################################################################

class Starting_layout():
    """The widget layout for the main menu."""
    def __init__(self):
        all_vocab = [VERBS_DICT, ADVERBS_DICT, NOUNS_DICT, ADJECTIVES_DICT, PREPOSITIONS_DICT]
        tk.Label(text="Choose what to practice.").pack()
        tk.Button(text="Tips and rules", command=show_tips).pack()
        tk.Button(text="Listening", command=test_listening).pack()
        tk.Button(text="Pronouns and articles", command=test_declension).pack()

        tk.Button(text="German to English", command=lambda:
                  translate(all_vocab, "ger_to_eng")).pack()
        tk.Button(text="English to German", command=lambda:
                  translate(all_vocab, "eng_to_ger", get_cats(), self.plural_nouns.get())).pack()
        tk.Button(text="Adjectives", command=lambda:
                  translate([ADJECTIVES_DICT], "eng_to_ger")).pack()
        tk.Button(text="Nouns", command=lambda:
                  translate([NOUNS_DICT], "eng_to_ger", tuple(), self.plural_nouns.get())).pack()

        self.plural_nouns = tk.BooleanVar()
        tk.Checkbutton(text="Enable plural noun forms.", variable=self.plural_nouns).pack()
        tk.Button(text="Verb conjugation", command=lambda: test_conjugation(get_cats())).pack()
        tk.Button(text="Core verbs", command=lambda: test_conjugation(get_cats(), "core")).pack()
        tk.Label(text="Toggle which verb conjugations to enable.").pack()

        self.cats, self.cat_buttons = dict(), dict()
        for cat in CONJUGATION_CATEGORIES:
            self.cats[cat] = tk.BooleanVar()
            self.cat_buttons[cat] = tk.Checkbutton(text=cat, variable=self.cats[cat])
            self.cat_buttons[cat].pack()
        # These categories are enabled by default.
        for cat in CONJUGATION_CATEGORIES[0:3:2]:
            self.cats[cat].set(True)

        def get_cats(): # Turning the 'cats' dictionary into a tuple of enabled category names.
            enabled_cats = [cat if value.get() else False for (cat, value) in self.cats.items()]
            return tuple(filter(bool, enabled_cats))


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
            for char in "ÄÖÜäüöß":
                # Need to use partial instead of lambda, to avoid the cell-var-from-loop problem.
                tk.Button(horizontal, text=char,
                          command=partial(self.answer.insert, tk.INSERT, char)
                          ).pack(side=tk.RIGHT)


class Memory():
    """An object for keeping track of my learning progress. For longer-term
    storage the information is synced with a memory.json file."""
    def __init__(self):
        self.memory = defaultdict(self.track_new_word)
        if isfile("memory.json"):
            with open("memory.json", "r", encoding="utf-8") as file:
                self.memory.update(json.load(file))
        # The .json file gets updated only when the GUI window is closed.
        window.protocol("WM_DELETE_WINDOW", self.save_to_file)
        # For storing how many correct (1) and wrong (0) answers were given in the current attempt.
        self.current_attempt = []

    @staticmethod
    def track_new_word():
        return {"date added": datetime.now().strftime(r"%Y-%m-%d"), "ans_corr": [], "ans_wrng": []}

    @property
    def current_accuracy(self):
        try:
            return round(mean(self.current_attempt) * 100)
        except StatisticsError:
            return "N/A"

    def record(self, german, correct):
        outcome = "ans_corr" if correct else "ans_wrng"
        self.memory[german][outcome].append(int(datetime.now().timestamp()))

    def get_accuracy(self, words, day_limit=93):
        # Date beyond which correct and incorrect answers do not count for the accuracy measurement.
        cutoff = int(datetime.now().timestamp()) - day_limit * 60 * 60 * 24
        try:
            corr = list(filter(lambda date: date > cutoff, self.memory[words[0]]["ans_corr"]))
            wrng = list(filter(lambda date: date > cutoff, self.memory[words[0]]["ans_wrng"]))
            return round(len(corr) / (len(corr) + len(wrng)), ndigits=1)
        except ZeroDivisionError:
            return 0

    def get_last_correct(self, words):
        try:
            # Rounding to a coarseness of roughly a day.
            return round(max(self.memory[words[0]]["ans_corr"]), ndigits=-5)
        except ValueError:
            return 0

    def save_to_file(self):
        with open("memory.json", "w", encoding="utf-8") as file:
            json.dump(self.memory, file, ensure_ascii=False, indent=4)
        window.destroy()
        _exit(0)

####################################################################################################

def show_tips():
    for widget in window.winfo_children():
        widget.destroy()
    wait_var = tk.BooleanVar()
    tk.Button(text="Next tip", command=lambda: wait_var.set(1)).pack()
    tip_label = tk.Label(wraplength=850, font="size 22")
    tip_label.pack(expand=True) #* This is not a reliable method of centering widgets
    tips = list(TIPS)
    shuffle(tips)
    for tip in tips:
        # Removing excess whitespace from the tips
        tip_label.configure(text=sub(r"(\s*\n\s*)|(\s{2,})", " ", tip))
        window.wait_variable(wait_var)
    tip_label.configure(text="All finished.")


def conjugate_verb(verb):
    """_summary_

    Args:
        verb (str): _description_

    Returns:
        dict: _description_
    """
    url_verb = verb.lower().replace("sich", "").strip()
    page = requests.get("https://pl.pons.com/odmiana-czasownikow/niemiecki/" + url_verb)
    parsed_page = BeautifulSoup(page.content, "html.parser")
    if parsed_page.find("div", class_="alert alert-block alert-warning"):
        print(f"Couldn't find verb '{url_verb}', stopping.")
        return False

    # Some verbs have multiple forms of conjugation (e.g. with and without 'sich'), which are stored
    # on different webpages. Here the right page is found and loaded.
    alternate_conjug = parsed_page.find("h2", class_="ft-variant-links-label")
    if alternate_conjug:
        print(f"'{url_verb}' has multiple forms.")
        hyperlinks = alternate_conjug.parent.find_all("a")
        if "sich " in verb.lower():
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
                # Removing poetic & outdated versions of words
                phrase = sub(r" / poet\.lubprzest\..+", "", phrase)
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
    elif verbs == "core":
        verbs = list(CORE_VERBS)
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
            # Moving the cursor to the end of the first line
            layout.answer.mark_set(tk.INSERT, "1.99")
            window.wait_variable(layout.wait_var)

            raw_answer = layout.answer.get("1.0", tk.END) # All text in the text box
            # Splitting into rows and removing excess whitespace (including empty rows).
            cleaned_answer = filter(bool, [trim(row) for row in raw_answer.split("\n")])
            if set(cleaned_answer) == set(right_answer):
                layout.feedback_label.configure(text="Correct.")
            else:
                layout.feedback_label.configure(text="Wrong, the right answer is:\n" +
                                                "\n".join(right_answer))
            layout.button_next.configure(text="Continue to next question.")
            window.wait_variable(layout.wait_var)

    if len(verbs) > 1:
        layout.prompt_label.configure(text="All finished.")


def translate(vocab, direction, conjugate=tuple(), plural_nouns=True):
    """_summary_

    Args:
        vocab (list): _description_
        direction (str): _description_
        conjugate (tuple, optional): _description_
        plural_nouns (bool, optional): _description_
    """
    # Setting up the prompts and answers
    vocab = list(ChainMap(*vocab).items())
    shuffle(vocab)
    # Placing words answered correctly a long time ago earlier.
    vocab = sorted(vocab, key=memory.get_last_correct)
    # Placing words with better answer accuracy earlier.
    vocab = sorted(vocab, key=memory.get_accuracy)
    if direction == "ger_to_eng":
        # Removing round & square brackets and everything inside them. Also flipping the word order.
        vocab = [(sub(r"\s*[\[\(].+[\]\)]\s*", "", item[1]), item[0]) for item in vocab]
    countdown = count(len(vocab), step=-1)

    for words in vocab:
        layout = Exercise_layout("enter", tk.Entry(width=38),
                                 ger_char=bool(direction == "eng_to_ger"))
        # Complex as to deal with answers that contain more than two words, separated by "/".
        answer_pieces = words[0].split(" / ")
        if (words[0] in NOUNS_DICT) and not plural_nouns:
            answer_pieces = answer_pieces[0:1] # Just the single form of the noun
        rearranged = permutations(answer_pieces, len(answer_pieces))
        right_answers = [" / ".join(item) for item in rearranged]
        layout.prompt_label.configure(text=f"Translate '{words[1]}'\n{next(countdown)} words left" +
                                           f"\nYour current accuracy is {memory.current_accuracy}%")
        window.wait_variable(layout.wait_var)

        if trim(layout.answer.get()) in right_answers:
            layout.feedback_label.configure(text="Correct.")
            memory.record(words[0 if direction == "eng_to_ger" else 1], True)
            memory.current_attempt.append(1)
        else:
            layout.feedback_label.configure(text=f"Wrong, the right answer is '{right_answers[0]}'")
            memory.record(words[0 if direction == "eng_to_ger" else 1], False)
            memory.current_attempt.append(0)

        for item in answer_pieces:
            sound_name = abspath(f"vicki-{item.replace(' ', '_')}.mp3")
            if isfile(sound_name):
                mixer.music.load(sound_name)
                mixer.music.play()
                # The mixer does not stop code execution for the duration of the audio file, so a
                # sufficiently long sleep period needs to be implemented here. This step used to
                # also work with mixer.sound(sound_name).play(), but by 8th April 2023 it stopped.
                sleep(1.1)
        window.wait_variable(layout.wait_var)

        if (words[0] in VERBS_DICT) and conjugate:
            test_conjugation(conjugate, answer_pieces)

    layout.prompt_label.configure(text="All finished.")


def test_listening():
    """_summary_
    """
    all_vocab = ChainMap(VERBS_DICT, ADVERBS_DICT, NOUNS_DICT, ADJECTIVES_DICT, PREPOSITIONS_DICT)
    audio_files = glob("vicki-*.mp3")
    shuffle(audio_files)
    for audio_file in audio_files:
        sound = mixer.Sound(abspath(audio_file))
        extra_button = tk.Button(text="Click to hear the word again.", command=sound.play)
        layout = Exercise_layout("enter", tk.Entry(), extra_button=extra_button)
        layout.prompt_label.configure(text="Write down the word you heard.")
        #TODO: Eliminate the popping sound. Can be done by fading the audio file out, 3ms is enough.
        sound.play()
        window.wait_variable(layout.wait_var)

        right_answer = search(r"vicki-(.+).mp3", audio_file).group(1).replace("_", " ")
        if trim(layout.answer.get()) == right_answer:
            response = "Correct."
        else:
            response = f"Wrong, the right answer is '{right_answer}'"
        for ger, eng in all_vocab.items():
            if right_answer in ger.split(" / "):
                response += f"\nIt means '{eng}'"
                break
        layout.feedback_label.configure(text=response)
        window.wait_variable(layout.wait_var)

    layout.prompt_label.configure(text="All finished.")


def test_declension():
    """_summary_
    """
    vocab = list(DECLENSION_DICT.items())
    # Always testing person pronouns (last item in DECLENSION_DICT) first.
    test_first = [vocab.pop(-2)]
    shuffle(vocab)
    for eng, ger in test_first + vocab:
        if len(ger) > 4: # Semi-arbitrary cutoff value
            right_answer = ger
        else:
            which_affix = "alternate" if "alt affix" in ger else "standard"
            affixes = iter(chain(*DECLENSION_AFFIXES[which_affix]))
            # By joining the list 'extra' into one string it becomes easier to search via RegEx.
            plural = search(r"plural = (\S+)", "\t".join(ger))

            right_answer = []
            for _ in range(3): # Nominativ / Akkusativ / Dativ
                for gender in DECLENSION_ORDER:
                    if (plural is not None) and (gender == "plural"):
                        answer_piece = plural.group(1) + next(affixes)
                    else:
                        answer_piece = ger[0] + next(affixes)
                    right_answer.append("-" if "-" in answer_piece else answer_piece)

        layout = Exercise_layout("click", tk.Text(height=3, width=35))
        one_third = int(len(right_answer) / 3)
        if eng in ["personal pronouns", "reflexive pronouns"]:
            layout.prompt_label.configure(text=f"Declenate '{eng}'")
            # Populating the text box with personal pronouns in Nominativ, to act as labels.
            layout.answer.insert(tk.INSERT, "     ".join(ger[:one_third]) + "\n")
        else:
            layout.prompt_label.configure(text=f"Declenate '{eng}'\n{'   '.join(DECLENSION_ORDER)}")
        #TODO: Add grammatical case labels for the text box.
        window.wait_variable(layout.wait_var)

        raw_answer = layout.answer.get("1.0", tk.END) # All text in the text box
        if trim(raw_answer) == " ".join(right_answer):
            layout.feedback_label.configure(text="Correct.")
        else:
            whitespace = cycle(["\n"] + ["\t"] * (one_third - 1))
            # Presenting the correct answer in a grid format through the use of whitespace.
            display_answer = "".join(chain(*zip(whitespace, right_answer)))
            layout.feedback_label.configure(text=f"Wrong, the right answer is:{display_answer}")
        layout.button_next.configure(text="Continue to next question.")
        window.wait_variable(layout.wait_var)

    layout.prompt_label.configure(text="All finished.")

####################################################################################################

if __name__ == "__main__":
    chdir(dirname(abspath(__file__)))
    window = tk.Tk()
    window.geometry("900x850")
    window.option_add("*font", "size 19") # Changing the default font size
    Starting_layout()
    mixer.init() # This is necessary for playing audio files
    memory = Memory()
    window.mainloop()

#TODO: translate sentences

####################################################################################################

    # Use https://freetts.com/Home/GermanTTS for pronunciation sound files, Vicki voice
    # Use semicolons to separate words. Analyse > Label Sounds, then File > Export > Export Multiple
    #from os import rename
    #all_files = glob("C:\\Users\\daiwe\\Downloads\\vicki-*.mp3")
    #all_files = sorted(all_files, key=lambda x: int(search(r"vicki-(\d+)\.mp3", x).group(1)))
    #names = iter(["die Zukunft", "die Vergangenheit", "die Vergangenheiten", "die Geschichte", "die Geschichten", "die Zeit", "die Zeiten", "der Morgen", "die Morgen", "der Winter", "die Winter", "der Frühling", "die Frühlinge", "der Sommer", "die Sommer", "der Herbst", "die Herbste", "das Jahr", "die Jahre", "der Monat", "die Monate", "die Woche", "die Wochen", "der Tag", "die Tage", "die Stunde", "die Stunden", "die Minute", "die Minuten", "der Mensch", "die Menschen", "die Leute", "der Beruf", "die Berufe", "das Geld", "die Gelder", "der Satz", "die Sätze", "die Ziffer", "die Ziffern", "die Zahl", "die Zahlen", "die Nummer", "die Nummern", "die Anzahl", "das Stäbchen", "die Stäbchen", "das Wasser", "die Wässer", "das Buch", "die Bücher", "die Straße", "die Straßen", "die Stadt", "die Städte"])
    #for file in all_files:
    #    part_name = "\\".join(file.split("\\")[:-1])
    #    rename(file, f'{part_name}\\vicki-{next(names).replace(" ", "_")}.mp3')
