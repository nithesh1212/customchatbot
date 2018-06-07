from flask import Blueprint, render_template, redirect
from requests import request, session
from flask import  request
import base64
from app.stories.models import User
import requests



chat = Blueprint('chat_blueprint', __name__,
                 url_prefix='/',
                 template_folder='templates'
                 )


@chat.route('/', methods=['GET'])
def index():
    return render_template('index.html')



@chat.route('/home', methods=['GET'])
def home():
    return render_template('chat.html')












