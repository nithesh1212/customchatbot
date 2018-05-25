from flask import Blueprint
from app.stories.models import Bot

from flask import request


bot = Blueprint('bot_blueprint', __name__,
                    url_prefix='/bot',
                    template_folder='templates')

@bot.route('/create', methods=['POST'])
def create():
    content = request.get_json(silent=True)

    bot = Bot()
    bot.botNameName = content.get("botName")
    bot.botDescription = content.get("botDescription")

    try:
        bot.save()
    except Exception as e:
        return ({"error": str(e)})

    return "Bot Created"
