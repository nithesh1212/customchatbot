import os
from bson.json_util import dumps, loads
from flask import Blueprint, request, render_template, Response
from flask import current_app as app
import app.commons.buildResponse as buildResponse
from app.stories.models import Story, Parameter, ApiDetails, update_document
from app.core.intentClassifier import IntentClassifier
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from mongoengine import *
import requests
from mongoengine import *
from bson.objectid import ObjectId
import csv
import html2text
from app.core import sequenceLabeler
from app.core.intentClassifier import IntentClassifier

from nltk.tag.perceptron import PerceptronTagger
from nltk import word_tokenize
from app.stories.models import Story,LabeledSentences,Parameter,ApiDetails
from app.core.nlp import posTagAndLabel,posTagger,sentenceTokenize

# Load and initialize Perceptron tagger
tagger = PerceptronTagger()

UPLOAD_FOLDER = '.\\UploadFiles'
ALLOWED_EXTENSIONS = set(['csv'])
connect("iky-ai", host="localhost", port=27017)



apiDetails1 = ApiDetails(

        url='', requestType='GET'
    )


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


stories = Blueprint('stories_blueprint', __name__,
                    url_prefix='/stories',
                    template_folder='templates')

# Create Stories


@stories.route('/home')
def home():
    return render_template('home.html')

@stories.route('/upload')
def upload():
    return render_template('UploadFile.html')


@stories.route('/edit/<storyId>', methods=['GET'])
def edit(storyId):
    return render_template('edit.html',
                           storyId=storyId,
                           )
@stories.route('/fileupload', methods=['GET', 'POST'])
def fileupload():
    if request.method == 'POST':
        # check if the post request has the file part
        print(request.files)
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #return redirect(url_for('stories_blueprint.fileupload', filename=filename))
            csvfile = open(UPLOAD_FOLDER+'\\'+filename, 'r')
            reader = csv.DictReader(csvfile)
            print(reader)
            header = ["storyName", "intentName", "apiTrigger", "speechResponse", "labelledSentences", "parameters"]

            parameter1 = []

            ls = LabeledSentences()

            for each in reader:
                row = {}
                for field in header:
                    print("Field",field)
                    list2 = []
                    if field == "labelledSentences":
                        list1 = []
                        list1.append(each[field])
                        sentences = list1[0]
                        cleanSentences = html2text.html2text(sentences)
                        result = posTagAndLabel(cleanSentences)
                        print("Result", result)

                        # data = "sentences=" + list1[0]
                        # headers = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                        # response = requests.post("http://localhost:8001/core/posTagAndLabel", data=data, headers=headers)
                        # print(response.json())
                        ls.data = result
                    row[field] = each[field]
                    print("row field",row[field])

                list2.append(ls)
                csvStories = Story(storyName=row['storyName'],intentName=row['intentName'],apiTrigger=False,speechResponse=row['speechResponse'],parameters=parameter1,labeledSentences=list2)
                csvStories.save();

                for story in Story.objects(storyName=row['storyName']):
                        sequenceLabeler.train(ObjectId(story.id))
                        print("After Sequence labeller")
                        IntentClassifier().train()
                        print("Build Successfull")
                        print(ObjectId(story.id))


                        print("Done")

            #return redirect(url_for('stories_blueprint.fileupload', filename=filename))
    return ''

@stories.route('/', methods=['POST'])
def createStory():
    content = request.get_json(silent=True)

    story = Story()
    story.storyName = content.get("storyName")
    story.intentName = content.get("intentName")
    story.speechResponse = content.get("speechResponse")

    if content.get("apiTrigger") is True:
        story.apiTrigger = True
        apiDetails = ApiDetails()
        isJson = content.get("apiDetails").get("isJson")
        apiDetails.isJson = isJson
        if isJson:
            apiDetails.jsonData = content.get("apiDetails").get("jsonData")

        apiDetails.url = content.get("apiDetails").get("url")
        apiDetails.requestType = content.get("apiDetails").get("requestType")
        story.apiDetails = apiDetails
    else:
        story.apiTrigger = False

    if content.get("parameters"):
        for param in content.get("parameters"):
            parameter = Parameter()
            update_document(parameter, param)
            story.parameters.append(parameter)
    try:
        story.save()
    except Exception as e:
        return buildResponse.buildJson({"error": str(e)})
    return buildResponse.sentOk()


@stories.route('/')
def readStories():
    stories = Story.objects(apiTrigger=True)
    return buildResponse.sentJson(stories.to_json())


@stories.route('/<storyId>')
def readStory(storyId):
    return Response(response=dumps(
        Story.objects.get(
            id=ObjectId(
                storyId)).to_mongo().to_dict()),
        status=200,
        mimetype="application/json")


@stories.route('/<storyId>', methods=['PUT'])
def updateStory(storyId):
    jsondata = loads(request.get_data())
    story = Story.objects.get(id=ObjectId(storyId))
    story = update_document(story, jsondata)
    story.save()
    return 'success', 200


@stories.route('/<storyId>', methods=['DELETE'])
def deleteStory(storyId):
    Story.objects.get(id=ObjectId(storyId)).delete()
    try:
        intentClassifier = IntentClassifier()
        intentClassifier.train()
    except BaseException:
        pass

    try:
        os.remove("{}/{}.model".format(app.config["MODELS_DIR"], storyId))
    except OSError:
        pass
    return buildResponse.sentOk()
