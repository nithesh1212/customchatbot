import os
from bson import ObjectId
import json
import requests

from datetime import datetime

from jinja2 import Undefined, Template

from flask import Blueprint, request, send_file, abort
from app import app

from app.commons import errorCodes
from app.commons.logger import logger
from app.commons import buildResponse
from app.core.intentClassifier import IntentClassifier
from app.core import sequenceLabeler
from app.stories.models import Story

botEmail = "marvel@sparkbot.io"  # bot's email address
accessToken = "YzI4YTRiMDctM2EwYy00ZTczLWFjMGQtNTc2ZTBhMWUwNTA4N2YxZjNhZWYtYjYz"  # Bot's access token
host = "https://api.ciscospark.com/v1/"  # end point provided by the CISCO Spark to communicate between their services
#server = "localhost"  # Web hook won't work until the server sets up
#port = 8001
headers = {"Authorization": "Bearer %s" % accessToken, "Content-Type": "application/json"}
#room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vMmExY2I2YjEtNDQ1NC0zODQ0LWJiMDktODY0Zjk5OTUyZTYx"  ## Room id where bot is added@app.route('/webhook', methods=['POST'])


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


def callApi(url, type, parameters, isJson=False):
    print(url, type, parameters, isJson)

    if "GET" in type:
        if isJson:
            print(parameters)
            response = requests.get(url, json=json.loads(parameters))

        else:
            response = requests.get(url, params=parameters)
    elif "POST" in type:
        if isJson:
            response = requests.post(url, json=json.loads(parameters))
        else:
            response = requests.post(url, data=parameters)
    elif "PUT" in type:
        if isJson:
            response = requests.put(url, json=json.loads(parameters))
        else:
            response = requests.put(url, data=parameters)
    elif "DELETE" in type:
        response = requests.delete(url)
    else:
        raise Exception("unsupported request method.")
    result = json.loads(response.text)
    print(result)
    return result


# Request Handler
@endpoint.route('/v1', methods=['POST'])
def api():
    print("Inside /api/.v1")
    requestJson = request.get_json(silent=True)
    resultJson = requestJson
    print("Test.....", requestJson)
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

        intentClassifier = IntentClassifier()
        try:
            storyId = intentClassifier.predict(requestJson.get("input"))
        except AttributeError:
            resultJson["speechResponse"]="Question not available"
            return buildResponse.buildJson(resultJson)
        story = Story.objects.get(id=ObjectId(storyId))

        if story.parameters:
            parameters = story.parameters
        else:
            parameters = []

        if ((requestJson.get("complete") is None) or (
                requestJson.get("complete") is True)):
            resultJson["intent"] = {
                "name": story.intentName,
                "storyId": str(story.id)
            }

            if parameters:
                extractedParameters = sequenceLabeler.predict(
                    storyId, requestJson.get("input"))
                missingParameters = []
                resultJson["missingParameters"] = []
                resultJson["extractedParameters"] = {}
                resultJson["parameters"] = []
                for parameter in parameters:
                    resultJson["parameters"].append({
                        "name": parameter.name,
                        "type": parameter.type,
                        "required": parameter.required
                    })

                    if parameter.required:
                        if parameter.name not in extractedParameters.keys():
                            resultJson["missingParameters"].append(
                                parameter.name)
                            missingParameters.append(parameter)

                resultJson["extractedParameters"] = extractedParameters

                if missingParameters:
                    resultJson["complete"] = False
                    currentNode = missingParameters[0]
                    resultJson["currentNode"] = currentNode["name"]
                    resultJson["speechResponse"] = currentNode["prompt"]
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
                parameters = resultJson["extractedParameters"]

                urlTemplate = Template(story.apiDetails.url, undefined=SilentUndefined)
                renderedUrl = urlTemplate.render(**context)
                if story.apiDetails.isJson:
                    isJson = True
                    requestTemplate = Template(story.apiDetails.jsonData, undefined=SilentUndefined)
                    parameters = requestTemplate.render(**context)

                try:
                    result = callApi(renderedUrl,
                                     story.apiDetails.requestType,
                                     parameters,isJson)
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

@endpoint.route('/spark',methods=['POST'])
def get_tasks():
    try:

        print("in api/spark")
        print("Request Json",request.json)
        messageId = request.json.get('data').get('id')
        room_id=request.json.get('data').get('roomId')
        toPersonEmail=request.json.get('data').get('personEmail')
        print("Person Email.............",toPersonEmail)
        print(room_id)
        print("Message Id",messageId);
        if toPersonEmail != botEmail:
                messageDetails = requests.get(host + "messages/" + messageId, headers=headers)
                print("messageDetails", messageDetails)
                responseMessage = messageDetails.json().get('text')
                intentClassifier = IntentClassifier()
                try:
                 storyId = intentClassifier.predict(responseMessage)
                 story = Story.objects.get(id=ObjectId(storyId))
                except:
                    payload = {"roomId": room_id, "text": "Sorry! i cant find your question", "personEmail": toPersonEmail}
                    response = requests.request("POST", "https://api.ciscospark.com/v1/messages/",
                                                data=json.dumps(payload),
                                                headers=headers)
                    print(response.status_code)
                    return response.status_code

                print("Speech Response", story.speechResponse)
                print("response message", responseMessage)
                # toPersonEmail = messageDetails.json().get('personEmail')
                print("person email", toPersonEmail);

                payload = {"roomId": room_id, "text": story.speechResponse,"personEmail":toPersonEmail}
                response = requests.request("POST", "https://api.ciscospark.com/v1/messages/", data=json.dumps(payload),
                                            headers=headers)
                print("In send message response", response.status_code)

                return response.status_code
        else:
            return ""

    except :
        print("In Except ")
        return ""





