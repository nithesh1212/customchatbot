import app.core.sentenceClassifer as sentenceClassifer
from app.commons.validations import isListEmpty
from app.stories.models import Story
from app import app


class IntentClassifier(object):
    def __init__(self):
        self.PATH = "{}/{}".format(app.config["MODELS_DIR"],
                                   app.config["INTENT_MODEL_NAME"])

    def train(self):
        stories = Story.objects
        if not stories:
            print("If no stories")
            raise Exception("NO_DATA")

        labeledSentences = []
        trainLabels = []

        for story in stories:
            print("In for")
            labeledSentencesTemp = story.labeledSentences
            if not isListEmpty(labeledSentencesTemp):
                print("in if")
                for labeledSentence in labeledSentencesTemp:
                    print("In second for")
                    labeledSentences.append(labeledSentence.data)
                    trainLabels.append([str(story.id)])
            else:
                print("In else")
                continue

        trainFeatures = []
        for labeledSentence in labeledSentences:
            print("In label sent for")
            lq = ""
            for i, token in enumerate(labeledSentence):
                print("In token for")
                if i != 0:
                    lq += " " + token[0]
                else:
                    lq = token[0]
            trainFeatures.append(lq)
            print(self.PATH)
        sentenceClassifer.train(trainFeatures,
                                trainLabels,
                                outpath='.\\model_files\\intent.model', verbose=False)
        return True

    def predict(self, sentence):
        predicted = sentenceClassifer.predict(sentence, self.PATH)
        if not predicted:
            return Story.objects(
                intentName=app.config["DEFAULT_FALLBACK_INTENT_NAME"]).first().id
        else:
            return predicted["class"]
