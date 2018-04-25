from mongoengine import *
from bson.objectid import ObjectId
import csv
import html2text
from app.core import sequenceLabeler
from app.core.intentClassifier import IntentClassifier

#import app.core.nlp as nlp
from nltk.tag.perceptron import PerceptronTagger
from nltk import word_tokenize


# Load and initialize Perceptron tagger
tagger = PerceptronTagger()



def posTagger(sentence):
    tokenizedSentence = word_tokenize(sentence)
    posTaggedSentence = tagger.tag(tokenizedSentence)
    return posTaggedSentence


def posTagAndLabel(sentence):
    taggedSentence = posTagger(sentence)
    taggedSentenceJson = []
    for token, postag in taggedSentence:
        taggedSentenceJson.append([token, postag, "O"])
    return taggedSentenceJson


def sentenceTokenize(sentences):
    tokenizedSentences = word_tokenize(sentences)
    tokenizedSentencesPlainText = ""
    for t in tokenizedSentences:
        tokenizedSentencesPlainText += " " + t
    return tokenizedSentencesPlainText


# CSV to JSON Conversion
csvfile = open('C:\\Users\\syerupal\\Desktop\\ai-chatbot-framework-master\\csvupload.csv', 'r')
reader = csv.DictReader(csvfile)
header = ["storyName", "intentName", "apiTrigger", "speechResponse", "labelledSentences", "parameters"]


class LabeledSentences(EmbeddedDocument):
    id = ObjectIdField(required=True, default=lambda: ObjectId())
    data = ListField(required=True)


class Parameter(EmbeddedDocument):
    id = ObjectIdField(default=lambda: ObjectId())
    name = StringField(required=True)
    required = BooleanField(default=False)
    type = StringField(required=False)
    prompt = StringField()


class ApiDetails(EmbeddedDocument):
    url = StringField()
    requestType = StringField(
        choices=[
            "POST",
            "GET",
            "DELETE",
            "PUT"],
    )
    isJson = BooleanField(default=False)
    jsonData = StringField(default="{}")


class Story(Document):
    storyName = StringField(max_length=100, required=True, unique=True)
    intentName = StringField(required=True)
    apiTrigger = BooleanField(required=True)
    apiDetails = EmbeddedDocumentField(ApiDetails)
    speechResponse = StringField(required=True)
    parameters = ListField(EmbeddedDocumentField(Parameter))
    labeledSentences = EmbeddedDocumentListField(LabeledSentences)


apiDetails1 = ApiDetails(

    url='', requestType='GET'
)

connect("iky-ai", host="localhost", port=27017)

parameter1 = []

ls = LabeledSentences()

for each in reader:
    row = {}
    for field in header:
        list2 = []
        if field == "labelledSentences":
            list1 = []
            list1.append(each[field])
            sentences = list1[0]
            cleanSentences = html2text.html2text(sentences)
            result = posTagAndLabel(cleanSentences)
            print("Result",result)

           # data = "sentences=" + list1[0]
            #headers = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            #response = requests.post("http://localhost:8001/core/posTagAndLabel", data=data, headers=headers)
            #print(response.json())
            ls.data = result
            break;
        row[field] = each[field]

    list2.append(ls)
    csvStories = Story(storyName=row['storyName'], intentName=row['intentName'], apiTrigger=False,
                       speechResponse=row['speechResponse'], parameters=parameter1, labeledSentences=list2)
    csvStories.save();

    for story in Story.objects(storyName=row['storyName']):
        sequenceLabeler.train(ObjectId(story.id))
        print("After Sequence labeller")
        IntentClassifier().train()
        print("Build Successfull")
        print(ObjectId(story.id))




