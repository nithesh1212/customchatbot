import os
from bson import ObjectId
import json
import requests
from pandas.io.json import json_normalize

from datetime import datetime
from app.stories.models import Channel

from jinja2 import Undefined, Template

from flask import Blueprint, request, send_file, abort
from app import app

from app.commons import errorCodes
from app.commons.logger import logger
from app.commons import buildResponse
from app.core.intentClassifier import IntentClassifier
from app.core import sequenceLabeler
from app.stories.models import Story
from requests import session

#Prod Bot
#botEmail = "marvel@sparkbot.io"  # bot's email address
#accessToken = "YzI4YTRiMDctM2EwYy00ZTczLWFjMGQtNTc2ZTBhMWUwNTA4N2YxZjNhZWYtYjYz"  # Bot's access token


#host = "https://api.ciscospark.com/v1/"  # end point provided by the CISCO Spark to communicate between their services
#headers = {"Authorization": "Bearer %s" % accessToken, "Content-Type": "application/json"}

#local bot
botEmail = "demobotforspark@webex.bot"  # bot's email address
accessToken = "ZjI5ZWMzNzMtYjNiOC00NTc3LWI3Y2ItYzE1YzEzZjE3YjM1NDJiZmM3NmMtMjlm"  # Bot's access token
host = "https://api.ciscospark.com/v1/"  # end point provided by the CISCO Spark to communicate between their services
#headers = {"Authorization": "Bearer %s" % accessToken, "Content-Type": "application/json"}

class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return 'undefined'

    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = __int__ = \
        __float__ = __complex__ = __pow__ = __rpow__ = \
        _fail_with_undefined_error


endpoint = Blueprint('api', __name__, url_prefix='/api')

session = requests.session()
session.__setattr__('parameterStatus', False)

index=0;

paramDict={}


def callApi(url, type, parameters, headerData, isJson=False,isHeader=False ):
    print(url, type, parameters, isJson, isHeader, headerData)

    if "GET" in type:
        if isJson and isHeader:
            print(parameters)
            response = requests.get(url, json=json.loads(parameters),headers=json.loads(headerData))
        elif isJson:
            print(parameters)
            response = requests.get(url, json=json.loads(parameters))
        elif isHeader:
            print(parameters)
            response = requests.get(url, headers=json.loads(headerData))
        elif len(parameters)==0:
            response = requests.get(url)
        else:
            response = requests.get(url, params=parameters)
    elif "POST" in type:
        if isJson and isHeader:
            print(parameters)
            response = requests.post(url, json=json.loads(parameters),headers=json.loads(headerData))
        elif isJson:
            print(parameters)
            response = requests.post(url, json=json.loads(parameters))
        elif isHeader:
            print(parameters)
            response = requests.post(url, headers=json.loads(headerData))
        elif len(parameters)==0:
            response = requests.post(url)
        else:
            response = requests.post(url, params=parameters)

    elif "PUT" in type:
        if isJson and isHeader:
            print(parameters)
            response = requests.put(url, json=json.loads(parameters),headers=json.loads(headerData))
        elif isJson:
            print(parameters)
            response = requests.put(url, json=json.loads(parameters))
        elif isHeader:
            print(parameters)
            response = requests.put(url, headers=json.loads(headerData))
        elif len(parameters)==0:
            response = requests.put(url)
        else:
            response = requests.put(url, params=parameters)

    elif "DELETE" in type:
        response = requests.delete(url)
    else:
        raise Exception("unsupported request method.")
    result = response.text
    print(result)
    return result


def is_json(myjson):
    try:
     json.loads(myjson)
    except:
        return False
    return True


# Request Handler
@endpoint.route('/v1', methods=['POST'])
def api():
    print("Inside /api/.v1")
    requestJson = request.get_json(silent=True)
    resultJson = requestJson
    print("Test.....", requestJson)
    print("Bot Iddddddddddddddddddddddddddddddd",requestJson.get("botId"))
    if requestJson:


        context = {}
        context["context"] = requestJson["context"]

        if app.config["DEFAULT_WELCOME_INTENT_NAME"] in requestJson.get(
                "input"):
            print("--------------insideif------------------")
            story = Story.objects(
                intentName=app.config["DEFAULT_WELCOME_INTENT_NAME"]).first()
            print("Story" , story)
            resultJson["complete"] = True
#            resultJson["intent"]["name"] = story.storyName
            resultJson["intent"]["storyId"] = str(story.id)
            resultJson["input"] = requestJson.get("input")
            template = Template(
                story.speechResponse,
                undefined=SilentUndefined)
            resultJson["speechResponse"] = template.render(**context)

            logger.info(requestJson.get("input"), extra=resultJson)
            return buildResponse.buildJson(resultJson)
        print("OutSide if")

        intentClassifier = IntentClassifier()
        try:
            storyId = intentClassifier.predict(requestJson.get("input"))
            print("Story Id",storyId)
        except AttributeError:
            resultJson["speechResponse"]="Question not available"
            return buildResponse.buildJson(resultJson)
        story = Story.objects.get(id=ObjectId(storyId))

        if story.parameters:
            print("Inside story.params")
            parameters = story.parameters
        else:
            print("No paramters")
            parameters = []

        if ((requestJson.get("complete") is None) or (
                requestJson.get("complete") is True)):
            print("Check whether complete is none or true")
            resultJson["intent"] = {
                "name": story.intentName,
                "storyId": str(story.id)
            }
            print(resultJson["intent"])

            if parameters:
                print("Check whether parametrs are present are not")
                extractedParameters = sequenceLabeler.predict(
                    storyId, requestJson.get("input"))
                print("Extracted parameters",extractedParameters)
                missingParameters = []
                resultJson["missingParameters"] = []
                resultJson["extractedParameters"] = {}
                resultJson["parameters"] = []
                for parameter in parameters:
                    print("If parameters are present")
                    resultJson["parameters"].append({
                        "name": parameter.name,
                        "type": parameter.type,
                        "required": parameter.required
                    })
                    print("Result JSON...",resultJson)

                    if parameter.required:
                        print("Check whether parameter is required are not")
                        if parameter.name not in extractedParameters.keys():
                            print("Check whether paramter name is present in extracted paramters")
                            resultJson["missingParameters"].append(
                                parameter.name)
                            missingParameters.append(parameter)
                            print("Result JSON2",resultJson)

                resultJson["extractedParameters"] = extractedParameters
                print("F Result json",resultJson)

                if missingParameters:
                    print("Check whether missing parameters is present or not")
                    resultJson["complete"] = False
                    currentNode = missingParameters[0]
                    resultJson["currentNode"] = currentNode["name"]
                    resultJson["speechResponse"] = currentNode["prompt"]
                    print("Inside missingparameters if ",resultJson)
                else:
                    resultJson["complete"] = True
                    context["parameters"] = extractedParameters
            else:
                resultJson["complete"] = True

        elif (requestJson.get("complete") is False):
            if "cancel" not in story.intentName:
                storyId = requestJson["intent"]["storyId"]
                story = Story.objects.get(id=ObjectId(storyId))
                resultJson["extractedParameters"][requestJson.get(
                    "currentNode")] = requestJson.get("input")

                resultJson["missingParameters"].remove(
                    requestJson.get("currentNode"))

                if len(resultJson["missingParameters"]) == 0:
                    resultJson["complete"] = True
                    context = {}
                    context["parameters"] = resultJson["extractedParameters"]
                    context["context"] = requestJson["context"]
                else:
                    missingParameter = resultJson["missingParameters"][0]
                    resultJson["complete"] = False
                    currentNode = [
                        node for node in story.parameters if missingParameter in node.name][0]
                    resultJson["currentNode"] = currentNode.name
                    resultJson["speechResponse"] = currentNode.prompt
            else:
                resultJson["currentNode"] = None
                resultJson["missingParameters"] = []
                resultJson["parameters"] = {}
                resultJson["intent"] = {}
                resultJson["complete"] = True

        if resultJson["complete"]: 
            if story.apiTrigger:
                isJson = False
                isHeader=False
                parameters = resultJson["extractedParameters"]

                urlTemplate = Template(story.apiDetails.url, undefined=SilentUndefined)
                renderedUrl = urlTemplate.render(**context)
                if story.apiDetails.isJson and story.apiDetails.isHeader:
                    isJson = True
                    isHeader= True
                    requestTemplate = Template(story.apiDetails.jsonData,story.apiDetails.headerData, undefined=SilentUndefined)
                    parameters = requestTemplate.render(**context)
                elif story.apiDetails.isJson:
                    isJson = True
                    requestTemplate = Template(story.apiDetails.jsonData,
                                               undefined=SilentUndefined)
                    parameters = requestTemplate.render(**context)
                elif story.apiDetails.isHeader:
                    isHeader = True
                    requestTemplate = Template(story.apiDetails.headerData,
                                               undefined=SilentUndefined)
                    parameters = requestTemplate.render(**context)
                try:
                    result = callApi(renderedUrl,
                                     story.apiDetails.requestType,
                                     parameters,story.apiDetails.headerData,isJson,isHeader)
                except Exception as e:
                    print(e)
                    resultJson["speechResponse"] = "Service is not available. "
                else:
                    print(result)
                    context["result"] = result
                    template = Template(story.speechResponse, undefined=SilentUndefined)
                    resultJson["speechResponse"] = template.render(**context)
            else:
                context["result"] = {}
                template = Template(story.speechResponse, undefined=SilentUndefined)
                resultJson["speechResponse"] = template.render(**context)
        logger.info(requestJson.get("input"), extra=resultJson)
        return buildResponse.buildJson(resultJson)
    else:
        return abort(400)


# Text To Speech
@endpoint.route('/tts')
def tts():
    voices = {
        "american": "file://commons/fliteVoices/cmu_us_eey.flitevox"
    }
    os.system(
        "echo \"" +
        request.args.get("text") +
        "\" | flite -voice " +
        voices["american"] +
        "  -o sound.wav")
    path_to_file = "../sound.wav"
    return send_file(
        path_to_file,
        mimetype="audio/wav",
        as_attachment=True,
        attachment_filename="sound.wav")




@endpoint.route('/spark/<botId>',methods=['POST'])

def sparkapi(botId):
    #session=requests.session()

    print("Bot Id",botId)
    channel=Channel.objects.get(botId=ObjectId(botId))
    print("Channel",channel)
    headers = {"Authorization": "Bearer %s" % channel.botAccessToken, "Content-Type": "application/json"}

    print("Spark APi Call")
    print("Request JSON ",request.json)
    messageId=request.json.get('data').get('id')
    print("Message Id ",messageId)
    roomId=request.json.get('data').get('roomId')
    print("Room Id ",roomId)
    email=request.json.get('data').get('personEmail')
    print("Email ",email)

    if email!=channel.botEmail:
        print("Inside first if")
        print("--------------------------------")
        if(session.__getattribute__('parameterStatus') and len(session.__getattribute__('parameters'))>=0):
            print("?????????????????????????????????")



            #print("In first if Parameter Status", session.__getattribute__('parameterStatus'))
            #print("In first if Parameters ", session.__getattribute__('parameters'));
            #print("Length of parameters ",len(session.__getattribute__('parameters')))
            paramList=list(session.__getattribute__('parameters'))
            tempParamList=list(session.__getattribute__('parameters'))
            paramLength=len(session.__getattribute__('parameters'))
            #print("Lengtrh....",paramLength)
            #print("Param List",paramList)
            #print("Param List type ", type(paramList))

            if(paramLength!=0):
                parameter=paramList[index]
                print(paramList[index].name)

            messageDetails = requests.get(host + "messages/" + messageId, headers=headers)
            print("Message Details JSON ", messageDetails)
            message = messageDetails.json().get('text')
            print("Message ", message)
            paramDict[parameter.name]=message;
            session.__setattr__('finParam',paramDict)
            if(paramLength > 1):
                payload = {"roomId": roomId, "text": paramList[index+1].prompt, "personEmail": email}
                response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                        data=json.dumps(payload),
                                        headers=headers)


            del paramList[index]

            #print("Length111111 ",len(paramList))
            session.__setattr__('parameters',paramList)

            print()
            #print("Dict.....",session.__getattribute__('finParam'))
            #print("Session parameters length??????? ",len(session.__getattribute__('parameters')))
           #     print(paramLength)
            paramListLength = len(paramList)
            if(paramListLength==0):
                print(paramDict)
                print(list(session.__getattribute__('tempparameters')))
                tempParam=list(session.__getattribute__('tempparameters'))
                story = Story.objects.get(id=ObjectId(session.__getattribute__('storyId')))
                if(story.apiTrigger==True):
                    apiDetails= story.apiDetails
                    print("URL ",apiDetails.url)
                    print("Testing..........")
                    print(type(apiDetails.url))
                    apiURL=apiDetails.url
                    #len1=apiURL.find("?")

                    if story.apiDetails.requestType=="GET":
                     actapi =apiURL+"?"+str(tempParam[0].name)+"="+str(paramDict[tempParam[0].name])
                    else:
                        actapi=apiURL
                    print("before Loop", actapi)
                    print("Length13456789",len(tempParam))
                    temParamLen = len(tempParam)
                    if story.apiDetails.requestType == "GET":

                        for i in range(1,temParamLen-1):
                            actapi+=actapi+"&"+str(tempParam[i])+"="+str(paramDict[tempParam[i]])

                        result = callApi(actapi,
                                     story.apiDetails.requestType,
                                     story.apiDetails.jsonData, story.apiDetails.isJson)
                    else:
                        result = callApi(actapi,
                                         story.apiDetails.requestType,
                                         json.dumps(paramDict), story.apiDetails.isJson)

                    print("Before json..........")

                    if is_json(result):
                        resDict = json.loads(result);

                        if isinstance(resDict, dict) and 'listName' in resDict:
                            resDict = resDict['listName']

                        print("Sdfghjhgfc ", resDict)

                        print("Type of redDict ", type(resDict))
                        print("Keys ", resDict.keys());
                        print("Type of keys", type(resDict.keys))
                        print("Values ", resDict.values())
                        print("Type of values", type(resDict.values))

                        for key in resDict.keys():
                            print("Key", key)

                        for value in resDict.values():
                            print("Value", value)

                        print(type(json.dumps(json.loads(result), indent=4, sort_keys=True)))

                        print("Speech Response", story.speechResponse);

                        resStrong = story.speechResponse
                        lis1 = resStrong.splitlines();
                        print(lis1)
                        data = json.loads(result)
                        tempString = ""
                        try:
                            for id in lis1:
                                tempString += "**" + id + "**" + ": "
                                tempString += data[id] + ""
                                tempString += "<br>"
                        except:
                            payload = {"roomId": roomId, "markdown": "JSON could not be parsed Please verify configuration", "personEmail": email}
                            response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                        data=json.dumps(payload),
                                                        headers=headers)
                            print(response.text)
                            return response.status_code

                        print("Before")
                        print(type(data))
                        print(type(data.keys()))
                        print(data.values())
                        for key in data.keys():
                            print("Key ", key)
                            print("Value", data[key])
                        print("After")
                        # print (json_normalize(data['flight']))

                        session.__setattr__('storyId', '')
                        session.__setattr__('parameterStatus', False)
                        session.__setattr__('parameters', '')
                        print("testtttttttttttttt,..........", session.__getattribute__('storyId'))

                        if (result):
                            payload = {"roomId": roomId, "markdown": tempString, "personEmail": email}
                            response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                        data=json.dumps(payload),
                                                        headers=headers)
                            print(response.text)
                            return response.status_code
                        session.__setattribute__('tempparameters', '')
                    else:
                        payload = {"roomId": roomId, "markdown": result, "personEmail": email}
                        response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                    data=json.dumps(payload),
                                                    headers=headers)
                        print(response.text)

                        session.__setattribute__('tempparameters', '')
                        session.__setattr__('storyId', '')
                        session.__setattr__('parameterStatus', False)
                        session.__setattr__('parameters', '')

                        return response.status_code

            #return response.status_code


            print("Updated param list length ",len(paramList))





        else:
            print("++++++++++++++++++===========")
            messageDetails = requests.get(host + "messages/" + messageId, headers=headers)
            print("Message Details JSON ",messageDetails)
            message=messageDetails.json().get('text')
            print("Message ",message)
            intentClassifier = IntentClassifier()
            try:
                storyId = intentClassifier.predict(message)
                story = Story.objects.get(id=ObjectId(storyId))
            except:
                payload = {"roomId": roomId, "text": "Sorry! i cant find your question", "personEmail": email}
                response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                            data=json.dumps(payload),
                                            headers=headers)
                print(response.status_code)
                return response.status_code
            if (story.parameters):
                session.__setattr__('parameterStatus', True)
                session.__setattr__('parameters',story.parameters)
                session.__setattr__('tempparameters',story.parameters)
                session.__setattr__('storyId',storyId)
                for parameter in story.parameters:
                    payload = {"roomId": roomId, "text": str(parameter.prompt),
                               "personEmail": email}
                    response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                data=json.dumps(payload),
                                                headers=headers)

                    return response.status_code
            elif (story.apiTrigger and not story.parameters):
                print("In else if where parameters=0 and apitrigger true")
                result1 = callApi(story.apiDetails.url,
                                 story.apiDetails.requestType,
                                 story.apiDetails.jsonData, story.apiDetails.isJson)
                print("Before json..........")

                if is_json(result1):

                    resDict = json.loads(result1);

                    if isinstance(resDict, dict) and 'listName' in resDict:
                        resDict = resDict['listName']

                    print("Sdfghjhgfc ", resDict)

                    print("Type of redDict ", type(resDict))
                    print("Keys ", resDict.keys());
                    print("Type of keys", type(resDict.keys))
                    print("Values ", resDict.values())
                    print("Type of values", type(resDict.values))

                    for key in resDict.keys():
                        print("Key", key)

                    for value in resDict.values():
                        print("Value", value)

                    print(type(json.dumps(json.loads(result1), indent=4, sort_keys=True)))

                    print("Speech Response", story.speechResponse);

                    resStrong = story.speechResponse
                    lis1 = resStrong.splitlines();
                    print(lis1)
                    data = json.loads(result1)
                    tempString = ""
                    for id in lis1:
                        tempString += "**" + id + "**" + ": "
                        tempString += str(data[id]) + ""
                        tempString += "<br>"
                    print("Before")
                    print(type(data))
                    print(type(data.keys()))
                    print(data.values())
                    for key in data.keys():
                        print("Key ", key)
                        print("Value", data[key])
                    print("After")

                    if (result1):
                        payload = {"roomId": roomId, "markdown": tempString, "personEmail": email}
                        response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                    data=json.dumps(payload),
                                                    headers=headers)
                        print(response.text)
                        return response.status_code

                    # print (json_normalize(data['flight']))
                else:
                    payload = {"roomId": roomId, "markdown": result1, "personEmail": email}
                    response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                data=json.dumps(payload),
                                                headers=headers)
                    print(response.text)
                    return response.status_code

            payload = {"roomId": roomId, "text": story.speechResponse,
                       "personEmail": email}

            response = requests.request("POST", "https://api.ciscospark.com/v1/messages/", data=json.dumps(payload),
                                        headers=headers)
            print("In send message response", response.status_code)

            return response.status_code
        return ""
    elif(email==channel.botEmail and session.__getattribute__('parameterStatus')==True):
        print("in second if Parameter Status",session.__getattribute__('parameterStatus'))
        print("in second ifParameters ",session.__getattribute__('parameters'));
        return ""
    else:
        print("+++++++++++++++++++++++++++")
        return""




