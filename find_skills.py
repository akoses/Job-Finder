import pandas as pd
from bs4 import BeautifulSoup
indeed = pd.read_csv("indeed_jobs.csv")
linkedin = pd.read_csv("linkedin_jobs.csv")
import string
import spacy
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

pattern1 = [{"TEXT": "You", "OP": "+"}]
pattern2 = [{"TEXT": "Your"}]
pattern3 = [{ "POS": "AUX", "IS_TITLE": True}]
pattern4 = [{"POS": "VERB", "IS_TITLE": True}]
pattern5 = [{"POS": "ADV", "IS_TITLE": True}]
pattern6 = [{"POS": "ADJ", "IS_TITLE": True, }]
pattern7 = [{"TEXT": "Candidate", "OP": "+"}]
pattern8 = [{"TEXT": "College"}]
pattern9 = [{"TEXT": "University"}]
pattern10 = [{"LIKE_NUM": True}, {"LOWER": "years"}]
pattern11 = [{"LIKE_NUM": True}, {"LOWER": "year"}]
pattern12 = [{"LEMMA": "bachelor"}, {"POS": "NOUN"}]
pattern13 = [{"LEMMA": "master"}, {"POS": "NOUN"}]
pattern14 = [{"LEMMA": "doctor"}, {"POS": "NOUN"}]
pattern15 = [{"LOWER": "associate"}, {"POS": "NOUN"}]
pattern16 = [{"LOWER": "experience"}]
pattern17 = [{"LOWER": "degree"}, {"LOWER": "in"}]


matcher.add("you_title", [pattern1])
matcher.add("your_title", [pattern2])
matcher.add("you_verb", [pattern4])
matcher.add("you_adv", [pattern5])
matcher.add("you_adj", [pattern6])
matcher.add("you_aux", [pattern3])
matcher.add("you_candidate", [pattern7])
matcher.add("you_college", [pattern8])
matcher.add("you_university", [pattern9])
matcher.add("you_years", [pattern10])
matcher.add("you_year", [pattern11])
matcher.add("you_bachelor", [pattern12])
matcher.add("you_master", [pattern13])
matcher.add("you_doctoral", [pattern14])
matcher.add("you_associate", [pattern15])
matcher.add("you_experience", [pattern16])
matcher.add("you_tags", [pattern17])


def find_skills(text):
    description = BeautifulSoup(text, 'html.parser')
    tags = find_tags(description)
    docs = [nlp(doc.translate(str.maketrans('', '', string.punctuation))) for doc in tags]
    found_docs = set()

    for doc in docs:
        matches = matcher(doc)
        for _ in matches:
            if len(doc) < 80:
                found_docs.add(doc)
    return list(found_docs)



def find_tags(text):
    docs = []
    lis = text.find_all('li')
    pis = text.find_all('p')
    divs = text.find_all('div')

    if len(lis) > 0 and len(pis) > 0:
        docs.extend(list(map(lambda x: x.get_text(), lis)))
        docs.extend(list(map(lambda x: x.get_text(), pis)))
    elif len(pis) > 0:
        docs.extend(list(map(lambda x: x.get_text(), pis)))
    elif len(lis) > 0:
        docs.extend(list(map(lambda x: x.get_text(), lis)))
    elif len(divs) > 0:
        for div in divs:
            docs.extend(div.get_text().split('\n'))
    else:
        return []
    return docs


