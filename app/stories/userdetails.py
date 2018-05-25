from app.stories.models import User,Bot,Channel
#user1=User(userName='Saikumar',password="saikumar")
#user1.save()
bot1=Bot(botName='SampleBot',botDescription="This is sample bot")
bot1.save()
channel1=Channel(channelName='Spark')
channel1.save()