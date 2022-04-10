"""This script is for learning German."""
#pylint: disable=multiple-statements

from os.path import isfile, abspath, dirname
from os import chdir
from random import shuffle
from collections import ChainMap
from itertools import permutations
from re import sub
import tkinter as tk
from time import sleep

from playsound import playsound

VERBS_DICT = {
    "dürfen": "to be allowed to (may)",
    "können": "to be able to (can)",
    "mögen": "to like",
    "möchten": "would like to",
    "müssen": "to have to (must)",
    "wollen": "to want",
    "sollen": "to ought to (shall)",
    "brauchen": "to need",
    "denken": "to think",
    "wissen": "to know (a fact)",
    "abhängen": "to depend",
    "kennen": "to be familiar with",
    "erkennen": "to recognise",
    "lernen": "to learn",
    "umlernen": "to retrain",
    "verlernen": "to forget (something already learned)",
    "studieren": "to study",
    "verstehen": "to understand",
    "fragen": "to ask (a question)",
    "wiederholen": "to repeat",
    "vergessen": "to forget",
    "erinnern": "to remind",
    "sich erinnern": "to remember",
    "glauben": "to believe",
    "achten": "to pay attention",
    "üben": "to practice",
    "bedeuten": "to mean",
    "erwarten": "to expect",
    "versprechen": "to promise",
    "empfehlen": "to recommend",
    "antworten": "to answer",
    "lehren / unterrichten": "to teach",
    "erklären": "to explain",
    "melden": "to report",
    "vergleichen": "to compare",
    "zustimmen": "to agree",
    "helfen": "to help",
    "teilen": "to share",
    "bieten / anbieten": "to offer",
    "verbieten": "to forbid",
    "lügen": "to lie (falshood)",
    "verraten": "to betray",
    "hören": "to hear / to listen",
    "sprechen": "to speak",
    "riechen": "to smell",
    "reden": "to talk",
    "sagen": "to say",
    "lesen": "to read",
    "schreiben": "to write",
    "buchstabieren": "to spell",
    "erzählen": "to tell / to narrate",
    "sehen": "to see",
    "aussehen": "to look like",
    "schauen": "to look",
    "anschauen / sich ansehen": "to watch / to look at",
    "beobachten": "to observe",
    "zeichnen": "to draw",
    "zeigen": "to show",
    "machen": "to make / to do",
    "tun": "to do",
    "rufen": "to call",
    "anrufen": "to phone",
    "bleiben": "to stay",
    "gehen": "to go",
    "laufen": "to walk / to run",
    "rennen": "to run",
    "fahren": "to drive",
    "stehen": "to stand",
    "sitzen": "to sit",
    "springen": "to jump",
    "warten": "to wait",
    "fliegen": "to fly",
    "hängen": "to hang",
    "liegen": "to lie (physically)",
    "kommen": "to come",
    "bekommen": "to get",
    "nehmen": "to take",
    "mitnehmen": "to take along",
    "holen": "to fetch",
    "bringen": "to bring",
    "geben": "to give",
    "schenken": "to gift",
    "senden / schicken": "to send",
    "tragen": "to carry",
    "stellen": "to put",
    "packen": "to pack",
    "werfen": "to throw",
    "wegwerfen": "to throw away",
    "bestellen": "to order",
    "kaufen": "to buy",
    "einkaufen": "to shop",
    "verkaufen": "to sell",
    "bezahlen": "to pay",
    "zählen": "to count",
    "kosten": "to cost",
    "verdienen": "to earn",
    "ausgeben": "to spend (money)",
    "spenden": "to donate",
    "suchen": "to search",
    "arbeiten": "to work",
    "wohnen": "to live (reside)",
    "leben": "to be alive",
    "schlafen": "to sleep",
    "einschlafen": "to fall asleep",
    "aufwachen": "to wake up",
    "duschen": "to shower",
    "kochen": "to cook",
    "trinken": "to drink",
    "essen": "to eat",
    "sich entspannen": "to relax oneself",
    "spielen": "to play",
    "reinigen": "to clean",
    "waschen": "to wash",
    "aufräumen": "to tidy up",
    "sich anziehen": "to get dressed",
    "sich ausziehen": "to get undressed",
    "sich rasieren": "to shave oneself",
    "steigen": "to climb / to rise",
    "umsteigen": "to transfer (vehicles)",
    "einsteigen": "to get on",
    "aussteigen": "to get off",
    "losgehen": "to set off",
    "sich beeilen": "to hurry up",
    "verspäten": "to delay",
    "sich verspäten": "to be late",
    "verschlafen": "to oversleep",
    "ankommen": "to arrive",
    "abfahren": "to depart",
    "dauern": "to last (take time)",
    "überdauern": "to outlast",
    "reisen": "to travel",
    "besuchen": "to visit / to attend",
    "einladen": "to invite",
    "treffen": "to meet",
    "sich treffen": "to meet up",
    "benutzen": "to use",
    "lösen": "to solve / to remove / to untighten",
    "spannen": "to tension / to tighten",
    "gehören": "to belong",
    "besitzen": "to own",
    "ausmachen": "to turn off",
    "anmachen": "to turn on",
    "laden": "to load",
    "hochladen": "to upload",
    "herunterladen": "to download",
    "aufladen": "to charge (battery)",
    "schließen": "to close",
    "aufschließen": "to unlock",
    "öffnen": "to open",
    "ziehen": "to pull / to move",
    "bauen": "to build",
    "sich interessieren": "to be interested in",
    "träumen": "to dream",
    "lieben": "to love",
    "hassen": "to hate",
    "sich fühlen": "to feel [czuć się]",
    "spüren": "to sense",
    "erleben": "to experience",
    "sich freuen": "to be happy about [cieszyć się że / na]",
    "versuchen": "to try (a task)",
    "probieren": "to try (a thing)",
    "aufgeben": "to give up",
    "verlieren": "to lose",
    "gewinnen": "to win",
    "erreichen": "to achieve / to reach",
    "vorhaben": "to intend",
    "hoffen": "to hope",
    "wünschen": "to wish",
    "beenden": "to finish",
    "beginnen / anfangen": "to begin",
    "wählen / auswählen": "to choose / to select"}

ADVERBS_DICT = {
    "dann": "then",
    "also": "so",
    "auch": "as well / also / too",
    "fast": "almost / nearly",
    "etwas": "something / a bit",
    "etwa": "about / roughly",
    "dort": "there [tam]",
    "noch": "still / yet",
    "jetzt": "now",
    "aber": "but",
    "oder": "or",
    "man": "(some)one",
    "bald": "soon",
    "nur": "just / only",
    "ohne": "without",
    "statt": "instead of",
    "ziemlich": "pretty / quite",
    "genau": "exactly",
    "deshalb / deswegen": "therefore",
    "immer": "always",
    "manchmal": "sometimes",
    "sofort": "immediately",
    "vielleicht": "perhaps",
    "genug": "enough",
    "wieder": "again",
    "wider": "against",
    "obwohl": "although",
    "ob": "whether",
    "dass": "that [że]",
    "trotz": "despite",
    "weder noch": "neither nor",
    "nie / niemals": "never",
    "bereits / schon": "already",
    "wenn / als": "when",
    "denn / weil": "because",
    "besonders": "especially",
    "oft": "often",
    "selten": "rarely",
    "sehr": "very",
    "kaum": "hardly",
    "eigentlich": "actually",
    "wirklich": "really",
    "wo": "where?",
    "woher": "where from?",
    "wohin": "where to?",
    "wann": "when?",
    "was": "what?",
    "wer": "who?",
    "wie": "how?",
    "warum / wieso": "why?"}

####################################################################################################

def translate_words(dictionaries, direction):
    # Setting up the window
    for widget in window.winfo_children():
        widget.destroy()
    prompt_label, feedback_label, entry = tk.Label(), tk.Label(), tk.Entry()
    prompt_label.pack() ; feedback_label.pack() ; entry.pack()

    dictionaries = list(ChainMap(*dictionaries).items())
    shuffle(dictionaries)
    if direction == "german to english":
        # Removing all round and square brackets, and everything inside them
        dictionaries = [(sub(r"s*[\[\(].+[\]\)]s*", "", item[1]), item[0])
                        for item in dictionaries]
    else:
        button_ä = tk.Button(text="ä", command=lambda: entry.insert(tk.END, "ä"))
        button_ü = tk.Button(text="ü", command=lambda: entry.insert(tk.END, "ü"))
        button_ö = tk.Button(text="ö", command=lambda: entry.insert(tk.END, "ö"))
        button_ß = tk.Button(text="ß", command=lambda: entry.insert(tk.END, "ß"))
        button_ä.pack() ; button_ü.pack() ; button_ö.pack() ; button_ß.pack()

    for words in dictionaries:
        # Complex as to deal with answers that contain more than two words, separated by "/".
        answer_pieces = words[0].split(" / ")
        rearranged = permutations(answer_pieces, len(answer_pieces))
        right_answers = [" / ".join(item) for item in rearranged]
        prompt_label.configure(text=f"Translate '{words[1]}':\n")

        window.wait_variable(pause_var) # Wait until I press the Enter key
        answer = entry.get()
        if answer in right_answers:
            feedback_label.configure(text="Correct.")
        else:
            feedback_label.configure(text=f"Wrong - the right answer is '{words[0]}'")
        for item in answer_pieces:
            sound_name = abspath(f"vicki-{item.replace(' ', '_')}.mp3")
            if isfile(sound_name):
                playsound(sound_name)
                sleep(0.25)

        window.wait_variable(pause_var)
        entry.delete(0, tk.END)
        feedback_label.configure(text="")

    prompt_label.configure(text="All finished.")

####################################################################################################

if __name__ == "__main__":
    chdir(dirname(abspath(__file__)))
    window = tk.Tk()
    window.geometry("500x400")
    welcome_label = tk.Label(text="Choose what to practice.")
    welcome_label.pack()
    ger_to_eng = tk.Button(text="German to English", command=lambda:
                           translate_words([VERBS_DICT, ADVERBS_DICT], "german to english"))
    ger_to_eng.pack()
    eng_to_ger = tk.Button(text="English to German", command=lambda:
                           translate_words([VERBS_DICT, ADVERBS_DICT], "english to german"))
    eng_to_ger.pack()
    pause_var = tk.StringVar()
    window.bind("<Return>", lambda event: pause_var.set(1))
    window.mainloop()

#TODO: translate sentences, test verb conjugation and tenses

####################################################################################################

    # Use https://freetts.com/Home/GermanTTS#ads for pronunciation sound files, Vicki voice
    #from re import sub, search
    #import tkinter as tk
    #from os import rename
    #from glob import glob
    #all_files = glob("C:\\Users\\daiwe\\Downloads\\better_german-*.mp3")
    #all_files = sorted(all_files, key=lambda x: int(search(r"german-(\d+)\.mp3", x).group(1)))
    #names = iter(["empfehlen","abfahren","selten","dann","einladen","woher","fragen","hören","bleiben","erzählen","umlernen","statt","bauen","rufen","sich entspannen","verbieten","kaum","herunterladen","spenden","abhängen","riechen","wissen","mitnehmen","helfen","buchstabieren","wenn","als","genau","sich interessieren","warten","erklären","denken","spüren","werfen","sich freuen","manchmal","trinken","warum","wieso","versuchen","einschlafen","träumen","wegwerfen","sich treffen","laufen","also","wie","bieten","anbieten","fliegen","hoffen","wider","verraten","sich verspäten","verlieren","bekommen","sitzen","lesen","spannen","wollen","treffen","man","stehen","aussteigen","leben","verkaufen","lügen","was","arbeiten","wählen","auswählen","fast","dass","dürfen","aufwachen","sich erinnern","ob","schreiben","sich beeilen","erwarten","aufräumen","dort","schlafen","möchten","erkennen","ziehen","verlernen","achten","verspäten","einsteigen","aufladen","besonders","öffnen","wünschen","schauen","sehen","sollen","zählen","verschlafen","lernen","reden","holen","geben","weder noch","tun","sprechen","erleben","bezahlen","zeichnen","tragen","packen","stellen","dauern","können","erreichen","sofort","lösen","bestellen","sagen","umsteigen","beginnen","anfangen","waschen","wer","ohne","aufschließen","studieren","aber","bringen","aussehen","anschauen","sich ansehen","rennen","wieder","etwa","kosten","hängen","gehören","sich rasieren","suchen","immer","senden","schicken","oder","verstehen","etwas","sich fühlen","teilen","mögen","springen","bald","kochen","sich anziehen","sehr","nur","benutzen","anmachen","melden","machen","essen","gewinnen","ausgeben","einkaufen","versprechen","vorhaben","hochladen","wohnen","nie","niemals","vergleichen","brauchen","auch","vielleicht","hassen","anrufen","bereits","schon","wirklich","fahren","antworten","aufgeben","sich ausziehen","spielen","liegen","wann","trotz","beenden","besuchen","vergessen","kennen","laden","oft","üben","lehren","unterrichten","reinigen","verdienen","kommen","schließen","kaufen","reisen","müssen","ziemlich","beobachten","zeigen","ankommen","steigen","gehen","duschen","nehmen","wohin","wo","ausmachen","noch","jetzt","deshalb","deswegen","denn","weil","glauben","lieben","überdauern","probieren","eigentlich","schenken","losgehen","wiederholen","genug","zustimmen","bedeuten","obwohl","besitzen","erinnern"])
    #for file in all_files:
    #    part_name = "\\".join(file.split("\\")[:-1])
    #    rename(file, f'{part_name}\\vicki-{next(names).replace(" ", "_")}.mp3')
