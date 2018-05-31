from bson.objectid import ObjectId
from mongoengine import *
from mongoengine import fields

from app import app

with app.app_context():
    try:
        connect(app.config["DB_NAME"],host=app.config["DB_HOST"])
    except:
        print("errorrrrrrrrrr")
    #connect("iky-ai",host="localhost",port=27017)

#connect("ciscobot",host="localhost",port=27017)


def update_document(document, data_dict):

    def field_value(field, value):

        if field.__class__ in (
                fields.ListField,
                fields.SortedListField,
                fields.EmbeddedDocumentListField):
            return [
                field_value(field.field, item)
                for item in value
            ]
        if field.__class__ in (
            fields.EmbeddedDocumentField,
            fields.GenericEmbeddedDocumentField,
            fields.ReferenceField,
            fields.GenericReferenceField
        ):
            return field.document_type(**value)
        else:
            return value

    [setattr(
        document, key.replace("_id", "id"),
        field_value(document._fields[key.replace("_id", "id")], value)
    ) for key, value in data_dict.items()]

    return document


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
    url = StringField(required=True)
    requestType = StringField(
        choices=[
            "POST",
            "GET",
            "DELETE",
            "PUT"],
        required=True)
    isJson = BooleanField(default=False)
    isHeader=BooleanField(default=False)
    jsonData = StringField(default="{}")
    headerData= StringField(default="{}")


class Story(Document):
    storyName = StringField(max_length=1000, required=True, unique=True)
    intentName = StringField(required=True)
    apiTrigger = BooleanField(required=True)
    apiDetails = EmbeddedDocumentField(ApiDetails)
    speechResponse = StringField(required=True)
    parameters = ListField(EmbeddedDocumentField(Parameter))
    labeledSentences = EmbeddedDocumentListField(LabeledSentences)
    botId = ObjectIdField(required=True, default=lambda: ObjectId())

class User(Document):
    userId=ObjectIdField(required=True, default=lambda: ObjectId())
    userName=StringField(max_length=100,required=True,unique=True)
    password=StringField(max_length=100,required=True)

class Bot(Document):
    botId=ObjectIdField(required=True, default=lambda: ObjectId())
    botName=StringField(max_length=100,required=True)
    botDescription=StringField(max_length=1000,required=True)
    userId =ObjectIdField(required=True, default=lambda: ObjectId())
    channelId=ObjectIdField(required=True, default=lambda: ObjectId())

class Channel(Document):
    channelId=ObjectIdField(required=True, default=lambda: ObjectId())
    channelName=StringField(max_length=100,required=True)
    webhookId=StringField(max_length=200,required=True)
    webhookName=StringField(max_length=100)
    botAccessToken=StringField(max_length=100)
    botEmail=StringField(max_length=100)
    botId = ObjectIdField(required=True, default=lambda: ObjectId())
