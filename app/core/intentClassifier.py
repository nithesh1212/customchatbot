import app.core.sentenceClassifer as sentenceClassifer
from app.commons.validations import isListEmpty
from app.stories.models import Story
from app import app
import requests
session=requests.session()


class IntentClassifier(object):
    def __init__(self):
        self.PATH = "{}/{}".format(app.config["MODELS_DIR"],
                                   app.config["INTENT_MODEL_NAME"])

    def train(self):
        print("Inside intent classifier train")
        stories = Story.objects()
        if not stories:
            #print("If no stories")
            raise Exception("NO_DATA")

        labeledSentences = []
        trainLabels = []

        for story in stories:
            labeledSentencesTemp = story.labeledSentences
            if not isListEmpty(labeledSentencesTemp):
                for labeledSentence in labeledSentencesTemp:
                    labeledSentences.append(labeledSentence.data)
                    trainLabels.append([str(story.id)])
            else:
                continue

        trainFeatures = []
        for labeledSentence in labeledSentences:
            lq = ""
            for i, token in enumerate(labeledSentence):
                if i != 0:
                    lq += " " + token[0]
                else:
                    lq = token[0]
            trainFeatures.append(lq)
            #print(self.PATH)
            #print("Train features",trainFeatures)
            #print("train labels",trainLabels)
            try:
                sentenceClassifer.train(trainFeatures,
                                trainLabels,
                                outpath="model_files\intent.model", verbose=False)
            except:
                print("In intent Classifier exception ")
                print("\n")
                print("")
            #print("Model1",model1)
        return True

    def predict(self, sentence):
        print("Sentence ",sentence)
        predicted = sentenceClassifer.predict(sentence, self.PATH)
        print("Predicted",predicted)
#        print("Predicted",predicted["class"])
        print("Path ",self.PATH)
        if not predicted:
            return Story.objects(
                intentName=app.config["DEFAULT_FALLBACK_INTENT_NAME"]).first().id
        else:
            #print("Predicted class",predicted["class"])
            return predicted["class"]
