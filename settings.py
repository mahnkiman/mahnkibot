import logging

# Auth stuff. DON'T SHARE IT!

NICK = "mybot" # The name of your bot.  Needs to be a separate Twitch account from your own.
PASS = "mypass" # Log into Twitch with your bot account and go here to get the oauth: http://twitchapps.com/tmi/
MYNICK = "mahnkiman" # Your Twitch name

# Set all the variables necessary to connect to Twitch IRC
HOST = "irc.twitch.tv"
PORT = 6667
readbuffer = ""
MODT = False

#Bot specific stuff
QUOTEFILE = "quotes.txt"
HIGHLIGHTFILE = "highlights.txt"   
MODTTL = 180	# Controls how often we poll for a list of mods in the chat
LOGLEVEL = logging.DEBUG

# For the Plug Cycle
PLUGCYCLE = True        #Set to True if you want it to run, else False if not
PLUGINTERVAL = 600      #How many seconds must pass before the next plug message
PLUGMESSAGENUM = 10     #Minimum number of messages that must be sent in chat before the next plug message
PLUGMESSAGE = "I will be participating in Extra Life, a 24-hour gaming event for charity on Nov 7th and 8th!  Check out our team page at bit.ly/BrosBeforeChocobos and consider donating either now or during the event!  And don't forget to follow me!"

# Other messages
SOCIALTEXT = "http://twitter.com/mahnkimann http://www.youtube.com/mahnkiman2"
RULETEXT = "Simple - be cool to everyone! That means no racism, sexism, or anything that promotes hate and drama. Links are not allowed unless permitted by a mod. No spoilers in blind runs. No help unless I ask for it. No backseating. No spamming!"

#For URL permits
PERMITDATA = {}
PERMITTTL = 60
LINKEXCLUSIONS = {"o.o","O.O"}    #Any exclusions to the link checker
