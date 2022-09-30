# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import csv

import re
from collections import Counter


def words(text): return re.findall(r'\w+', text.lower())

WORDS = Counter(words(open('data/Course_List.csv').read()))

def P(word, N=sum(WORDS.values())):
    return WORDS[word] / N

def correction(word): 
    return max(candidates(word), key=P)

def candidates(word): 
    return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

def known(words): 
    return set(w for w in words if w in WORDS)

def edits1(word):
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word): 
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))

# Separate the word
def whitespaceRemove(text):
  text = text.split()
  c_text = ""
  for i in range(len(text)):
    text[i]=correction(text[i])
  n = len(text)
  for i in range(n):
    if(i==n-1):
      c_text+=text[i]
    else:
      c_text+=text[i]
      c_text+=" "
  return c_text

class ActionCourseSearch(Action):

    def name(self) -> Text:
        return "action_course_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        courseName = tracker.get_slot("course")
        degreeLevel = tracker.get_slot("course_level")
        details = ""

        # read the CSV file
        output = []
        with open('data/Course_List.csv','r',encoding = "utf-8") as file:
            reader = csv.DictReader(file)
            # get a list of  desired course
            for row in reader:
                if(row['Subject'].lower()==courseName.lower() and row['CourseLevel'].lower()==degreeLevel.lower()):
                    output.append(row)


        # Spelling correction and check
        if(len(output)==0):
            with open('data/Course_List.csv','r',encoding = "utf-8") as file:
                reader = csv.DictReader(file)
                courseName = whitespaceRemove(courseName)
                degreeLevel = whitespaceRemove(degreeLevel)
                for row in reader:
                    if(row['Subject'].lower()==courseName.lower() and row['CourseLevel'].lower()==degreeLevel.lower()):
                        output.append(row)


        # Match one word of subject name
        if(len(output)==0):
            with open('data/Course_List.csv','r',encoding = "utf-8") as file:
                reader = csv.DictReader(file)
                courseName = whitespaceRemove(courseName)
                degreeLevel = whitespaceRemove(degreeLevel)
                for row in reader:
                    if(row['CourseLevel'].lower()==degreeLevel.lower()):
                        sub = row['Subject'].lower()
                    sub = sub.split()
                    cN = courseName.split()
                f = 0
                for x in sub:
                    for y in cN:
                        if(x==y):
                            f = 1
                            break
                if f==1:
                    output.append(row)


        ln = len(output)

        if output: 
            c = 0
            for item in output:
                if(len(item['CourseLevel'])>0):
                    details+="\n- "+"This is "+item['CourseLevel']+" Program."
                if(len(item['Qualification'])>0):
                    details+="\n- "+"After successfully completion "+item['Subject']+" you will achieve "+item['Qualification']+ " Qualification."
                if(len(item['School'])>0):
                    details+="\n- "+"This subject is thought under "+item['School']+ " School"
                if(len(item['Location'])>0):
                    details+="\n- "+"The class will be conducted in our "+item['Location']
                if(len(item['Link'])>0):
                    details+="\n"+"For details visit: "+item['Link']
                c+=1
                if(c<ln):
                    details+="\n\n\n"+"***You might interest this course also:***"    
        else: # the list is empty
            details = f"I could not find any subjects in {courseName} \n"
            details+="For details course list you can visit this link: https://www.lsbu.ac.uk/study/course-finder?collection=LSBU_Courses_new&query=!nullsearch&start_rank=1&sort=relevance&f.Level_new|courseLevel=undergraduate"
        dispatcher.utter_message(details)
        return [SlotSet("details",details)]