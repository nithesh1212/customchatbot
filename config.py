import os


class Config(object):
    DEBUG = False
    DB_NAME = "heroku_dcc30xfp"
    DB_HOST = "mongodb://heroku_dcc30xfp:nekb61rpo3vkv3aujbj1dfsl59@ds259119.mlab.com:59119/heroku_dcc30xfp"
    DB_USERNAME = "heroku_dcc30xfp"
    DB_PASSWORD = "nekb61rpo3vkv3aujbj1dfsl59"
    # Web Server details
    WEB_SERVER_PORT = 8001

    # Intent Classifier model detials
    MODELS_DIR = "model_files"
    INTENT_MODEL_NAME = "intent.model"
    DEFAULT_FALLBACK_INTENT_NAME = "fallback"
    DEFAULT_WELCOME_INTENT_NAME = "init_conversation"


class Development(Config):
    DEBUG = True


class Production(Config):
    # MongoDB Database Details
    DB_HOST = "ds259119.mlab.com:59119"
    DB_USERNAME = "heroku_dcc30xfp"
    DB_PASSWORD = "nekb61rpo3vkv3aujbj1dfsl59"

    # Web Server details
    WEB_SERVER_PORT = 8001
