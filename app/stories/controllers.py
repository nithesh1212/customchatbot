import os
from bson.json_util import dumps, loads
from flask import Blueprint, request, render_template, Response
from flask import current_app as app
import app.commons.buildResponse as buildResponse
from app.stories.models import Story, Parameter, ApiDetails, update_document,Bot,Channel
from app.stories.models import User
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import base64
from mongoengine import *
from bson.objectid import ObjectId
import csv
import html2text
from app.core import sequenceLabeler
from app.core.intentClassifier import IntentClassifier
from app.stories.models import Bot
import requests
import json

from nltk.tag.perceptron import PerceptronTagger
from nltk import word_tokenize
from app.stories.models import Story,LabeledSentences,Parameter,ApiDetails
from app.core.nlp import posTagAndLabel,posTagger,sentenceTokenize
from app.core import nlp
import ast

# Load and initialize Perceptron tagger
tagger = PerceptronTagger()

UPLOAD_FOLDER = './UploadFiles'
ALLOWED_EXTENSIONS = set(['csv'])
connect("ChatBot", host="localhost", port=27017)



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

session = requests.session()

#userLogin
@stories.route('/login', methods=['POST'])
def login():
    print("Inside stories login")
    requestJson = request.get_json(silent=True)
    resultJson = requestJson
    print("Test.....", requestJson)
    userName=base64.b64decode(resultJson["username"]).decode("utf-8")
    passWord=base64.b64decode(resultJson["password"]).decode("utf-8")
    print("Username ",userName)
    print("Password",passWord)
    try:
        user = User.objects.get(userName=userName)
        session.__setattr__('userid', user.id)
        session.__setattr__('username',user.userName)
        User.objects.get(userName=userName)
    except:
        return "NoUser"
    try:
        User.objects.get(password=passWord)
    except:
        return "NoPass"
    print("User Id", user.id)
    return "validuser"



#Create Bot

@stories.route('/bot', methods=['POST'])
def createBot():

    print("In create Bot")
    content = request.get_json(silent=True)
    print(content)
    bot = Bot()
    story=Story()
    bot.botName = content.get("botName")
    bot.botDescription = content.get("botDescription")
    bot.userId=session.__getattribute__("userid")

    print("userID",bot.userId)
    print("Bot Name", bot.botName)
    print("Bot Desc", bot.botDescription)

    try:
        bot.save()
       # botid= Bot.objects.get(botName=bot.botName)
        print("ID",bot.id)
        #   print("IDddd",ObjectId(bot._id)
        story.botId=bot.id
        story.storyName='init_conversation'+str(bot.id)
        story.intentName='init_conversation'
        story.speechResponse='Hi!!! This is '+bot.botName+' bot, your virtual assisstant. You can configure me as you need. For more options look at menu in right'
        story.apiTrigger=False
        story.save()

    except Exception as e:
        print({"error", str(e)})
        return "botNotcreated"
    return "BotCreated"

@stories.route('/bot')
def getBots():
    userId = session.__getattribute__('userid')
    bots = Bot.objects(userId=ObjectId(userId))
    print(bots)
    return buildResponse.sentJson(bots.to_json())



@stories.route('/form')
def form():
    return render_template('form.html',username=session.__getattribute__('username'))


@stories.route('/createbot')
def createbot():
    print("In create",session.__getattribute__('username'))
    return render_template('chat.html',username=session.__getattribute__('username'))

@stories.route('/home/<botId>')
def home(botId):
    print("BotId",botId)
    session.__setattr__('botid',botId)
    bot=Bot.objects.get(botId=ObjectId(botId))
    #print(intents)
    print("Inside /home session bot idf",session.__getattribute__('botid'))
    return render_template('home.html',botId=botId,botName=bot.botName,username=session.__getattribute__('username'))

@stories.route('/spark/<botId>')
def sparkConfig(botId):
    print("BotId",botId)
    session.__setattr__('botid',botId)
    bot=Bot.objects.get(botId=ObjectId(botId))
    #print(intents)
    print("Inside /home session bot idf",session.__getattribute__('botid'))
    return render_template('spark.html',botId=botId,botName=bot.botName,username=session.__getattribute__('username'))

@stories.route('/sparkwebhook',methods=['POST'])
def sparkwebhook():
    print("Inside webhook")
    content = request.get_json(silent=True)
    content.get('botEmail')
    content.get('botToken')

    headers = {"Authorization": "Bearer %s" % content.get('botToken'), "Content-Type": "application/json"}

    print("headers",headers)
    content1={
	"name": content.get('botEmail')+" webhook",
	"targetUrl": "https://3d6bb6e2.ngrok.io/api/spark/"+content.get('botId'),
	"resource": "messages",
	"event": "created"
}
    print("Content ",content)

    try:
        channel=Channel.objects.get(botAccessToken=content.get('botToken'))
        return "Already"

    except:
        pass

    try:
        response=requests.request("POST", "https://api.ciscospark.com/v1/webhooks",
                     data=json.dumps(content1),
                     headers=headers)
    except :
        print("Enable to create webhook because ")

    print("Bot id in spark webhook",content.get('botId'))


    print("Response ",response)
    responseJson=response.json()
    print("Response JOSn",responseJson)
    print("Response id", responseJson.get('id'))
    channel=Channel()
    channel.botId=ObjectId(content.get('botId'))
    channel.botAccessToken=content.get('botToken')
    channel.botEmail=content.get('botEmail')
    channel.webhookId=responseJson.get('id')
    channel.webhookName=responseJson.get('name')
    channel.channelName='Spark'


    channel.save()
    return "Channel"

@stories.route('/bots/home')
def botHtml():
    userName=session.__getattribute__('username')
    return render_template('bot.html',username=userName)

@stories.route('/upload/<botId>')
def upload(botId):
    session.__setattr__('botid', botId)
    return render_template('UploadFile.html',botId=botId)

'''@stories.route('/create')
def create():
    return render_template('create.html')'''

'''@stories.route('/chat/{}')
def chat():
    return render_template('chat.html')'''


@stories.route('/home/edit/<storyId>', methods=['GET'])
def edit(storyId):
    return render_template('edit.html',
                           storyId=storyId,
                           )

@stories.route('/chat/<botId>', methods=['GET'])
def chat(botId):
    print("Id....",botId)
    session.__setattr__('botid',botId)
    bot=Bot.objects.get(botId=ObjectId(botId))
    print("Bot ",type(bot))
    print("Bot Name",bot.botName)
    print("Bot Description",bot.botDescription)
    print("Bot Id",botId)
    return render_template('chat.html',
                           botId=botId,botName=bot.botName
                           )


@stories.route('/fileupload/<botId>', methods=['GET', 'POST'])
def fileupload(botId):
    print("Bot Id in file upload",session.__getattribute__('botid'))
    if request.method == 'POST':
        # check if the post request has the file part
        print(request.files)
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        print("File Details",file)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print("File Name",filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("File saved to folder")
            #return redirect(url_for('stories_blueprint.fileupload', filename=filename))
            csvfile = open(UPLOAD_FOLDER+'/'+filename, 'r',encoding='utf-8', errors='ignore')
            reader = csv.DictReader(csvfile)
            #print(reader)
            header = ["storyName", "intentName", "apiTrigger", "speechResponse", "labeledSentences", "parameters"]

            parameter1 = []

            ls = LabeledSentences()

            for each in reader:
                row = {}
                labelSent=[]
                ls=LabeledSentences()
                for field in header:
                    #print("Field",field)
                    list2 = []
                    if field =="labeledSentences":
                        #print("Inside labeled send")
                        #print("Row[fiel}",each[field])
                        cleanSentences = html2text.html2text(each[field])
                        #print("After clean Sentences")
                        #labelSen.data=posTagAndLabel(cleanSentences)
                        data=nlp.posTagAndLabel(cleanSentences)
                        print("Type of data",type(data))
                        ls.data = data
                        #print("Result ", labelSent)
                        #print("Type", type(labelSent))
                    row[field] = each[field]
                    #print("row field",row[field])

                list2.append(ls)
                csvStories = Story(storyName=row['storyName'],intentName=row['intentName'],apiTrigger=False,speechResponse=row['speechResponse'],parameters=parameter1,labeledSentences=list2,botId=botId)
                csvStories.save();
                print(row['storyName'],"Story Saved in DB")


            for story in Story.objects():
                        try:
             #               print("Object Id",ObjectId(story.id))
                            sequenceLabeler.train(ObjectId(story.id))
                            print("Build Successfull")
                            print(ObjectId(story.id))
                        except:
                            print("In sequence labeller excpetion")

            IntentClassifier().train()



            #return redirect(url_for('stories_blueprint.fileupload', filename=filename))
    return ''

@stories.route('/read', methods=['POST'])
def createStory():
    content = request.get_json(silent=True)

    story = Story()
    story.storyName = content.get("storyName")
    story.intentName = content.get("intentName")
    story.speechResponse = content.get("speechResponse")
    story.botId=content.get("botId")

    if content.get("apiTrigger") is True:
        story.apiTrigger = True
        apiDetails = ApiDetails()
        isJson = content.get("apiDetails").get("isJson")
        isHeader= content.get("apiDetails").get("isHeader")
        print("Is header",isHeader)
        apiDetails.isJson = isJson
        apiDetails.isHeader=isHeader
        if isJson:
            apiDetails.jsonData = content.get("apiDetails").get("jsonData")
        if isHeader:
            print("Is header data",content.get("apiDetails").get("headerData"))
            apiDetails.headerData = content.get("apiDetails").get("headerData")


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

    story.save()
    print("Story Saved")
    return buildResponse.sentOk()


@stories.route('/read1',methods=['GET'])
def readStories():
    print("BotId session in /read1",session.__getattribute__('botid'))
    bid=session.__getattribute__('botid')
    print("JSON",request.get_json(silent=True))
    stories = Story.objects(botId=ObjectId(bid))
    print("Stories json",stories.to_json)
    return buildResponse.sentJson(stories.to_json())

@stories.route('/<storyId>')
def readStory(storyId):
    print("In read Story")
    print("Story id",storyId)
    return Response(response=dumps(
        Story.objects.get(
            id=ObjectId(
                storyId)).to_mongo().to_dict()),
        status=200,
        mimetype="application/json")


@stories.route('/<storyId>', methods=['PUT'])
def updateStory(storyId):
    print("Inside update story")
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

@stories.route('/create/<botId>')
def create(botId):
    session.__setattr__('botid',botId)
    print("Bottttttttttttttttttttttt",botId)
    print("Bot Object Id",ObjectId(botId))
    bot=Bot.objects.get(botId=ObjectId(botId))
    return render_template('create.html',botId=bot.botId,botName=bot.botName,username=session.__getattribute__('username'))

@stories.route('/logout')
def logout():
    session.__setattr__('userid','');
    return render_template('index.html')



