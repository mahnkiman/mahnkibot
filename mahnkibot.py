import socket, string, datetime, time, requests, json, re, logging, sys
from random import randint
from urlparse import urlparse
from datetime import datetime

#Uptime statuses
UPTIME_404 = '0'
UPTIME_NOTLIVE = '1'

STARTTIME = time.time()

# Get settings and auth info
try:
    from settings import *
except ImportError:
    raise Exception("No settings found")

# Set logging level
log = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s - %(message)s'))
log.addHandler(log_handler)
log.setLevel(LOGLEVEL)

# Connecting to Twitch IRC by passing credentials and joining a certain channel
s = socket.socket()
s.connect((HOST, PORT))
s.send("PASS " + PASS + "\r\n")
s.send("NICK " + NICK + "\r\n")
s.send("JOIN #mahnkiman \r\n")

lastmodpolltime = 0
mods = None
nummessages = 0
nummessagesreachedflag = False
nextplugtime = int(time.time()) + PLUGINTERVAL

# Method for sending a message
def send_message(message):
    s.send("PRIVMSG #mahnkiman :" + message + "\r\n")
    print NICK+": "+message

def get_mods():
    # Check freshness of mod data
    global lastmodpolltime
    global mods
    log.debug("get_mods: Last Mod poll time: %s", str(lastmodpolltime))
    epochtime = int(time.time())
    if epochtime > lastmodpolltime:
        log.debug("get_mods: Refreshing mod data")
        try:
            r = requests.get("http://tmi.twitch.tv/group/user/"+MYNICK+"/chatters")
            parsed_json = json.loads(r.text)
            mods = parsed_json['chatters']['moderators']
            lastmodpolltime = epochtime + MODTTL
        except ValueError:
            log.error("get_mods: ERROR Unable to get mod data values!")
    else:
        log.debug("get_mods: Refreshing mod data")
    return mods

def is_mod(username):
    mods = get_mods()
    try:
        return mods.index(username) >= 0
    except ValueError:
        return False

def get_command_arg(parts):
    try:
        log.debug("get_command_arg: %s",str(parts))
        return string.split(parts[2], " ", 1)[1].replace("\r", "")
    except IndexError:
        return None

def get_uptime(thisnick):
    streaminfo = requests.get("https://api.twitch.tv/kraken/streams/"+thisnick)
    parsed_json = json.loads(streaminfo.text)
    log.debug("get_uptime: Stream data for %s is ", str(parsed_json))

    if 'error' in parsed_json:
        return UPTIME_404
    else:
        if parsed_json['stream'] == None:
            return UPTIME_NOTLIVE

        #2015-10-24T11:46:35Z
        created = parsed_json['stream']['created_at']
        createdate = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
        
        ts = get_timediff_str(createdate, datetime.utcnow())

        return ts

def get_game(username):
    channelinfo = requests.get("https://api.twitch.tv/kraken/channels/"+username)
    parsed_json = json.loads(channelinfo.text)
    return parsed_json['game']

def get_timediff_str(date1, date2):
    secdelta = abs((date2 - date1).seconds)
    hourdelta = str(secdelta / 60 / 60)
    minutedelta = str(secdelta / 60 % 60)
    return hourdelta+" hours, "+minutedelta+" minutes"

# Start

get_mods()

while True:
    readbuffer = readbuffer + s.recv(1024)
    temp = string.split(readbuffer, "\n")
    readbuffer = temp.pop()
    time.sleep(0.1)

    for line in temp:
        # Checks whether the message is PING because its a method of Twitch to check if you're afk
        log.debug("Current line is: \"%s\"", line)
        if line.startswith("PING :tmi.twitch.tv"):
            s.send("PONG :tmi.twitch.tv\r\n")
            log.debug("PONG!")
        else:
            # Splits the given string so we can work with it better
            parts = string.split(line, ":", 2)

            if "QUIT" not in parts[1] and "JOIN" not in parts[1] and "PART" not in parts[1]:
                try:
                    # Sets the message variable to the actual message sent
                    message = parts[2][:len(parts[2]) - 1]
                except:
                    message = ""
                # Sets the username variable to the actual username
                usernamesplit = string.split(parts[1], "!")
                username = usernamesplit[0]
                
                # Only works after twitch is done announcing stuff (MODT = Message of the day)
                if MODT:
                    log.info("Main: "+username + ": " + message)
                    msg = ""

                    # Is this a URL?  If the user does not have permission to post a link, dump it
                    if re.findall(r'[a-zA-z]\.[a-zA-z]', message) and message not in LINKEXCLUSIONS:
                        #Mods and the bot itself are excluded from this
                        log.debug("Link checker: %s just posted a link", username)
                        if not is_mod(username):
                            
                            canpostlink = False

                            try:
                                assert PERMITDATA[username]
                                currenttime = int(time.time())
                                
                                #User is permitted, but is the user still within the permit time window?
                                canpostlink = (currenttime <= PERMITDATA[username])
                                if not canpostlink:
                                    log.debug("Link Checker: %s's permit expired", username)
                                else:
                                    print username+" used their link permit"
                                    
                            except KeyError:
                                log.debug("Link checker: %s not in permit data", username)

                            #Not permitted
                            if canpostlink:
                                log.debug("Link checker: %s had a permit to post a link", username)
                                #Permit used
                                del PERMITDATA[username]
                            else:
                                log.debug("Link checker: Purging link!")
                                send_message(".timeout "+username+" 1\r")
                                send_message(username+", you didn't have permission to post a link!")

                            log.debug("Link checker: Permit data after link and permit checking: %s", str(PERMITDATA))
                        else:
                            log.debug("Link checker: User is a mod, link checking skipped")
                    
                    # You can add all your plain commands here
                    if message == "!quote":
                        try:

                            lines = open(QUOTEFILE, 'r').read().splitlines()
                            randomline = randint(0,len(lines)-1)
                            quoteline = ""
                            
                            #Try to split the line by delimeter (old quotes won't have the new format)
                            try:
                                quotedata = string.split(lines[randomline], "||")

                                # Old quotes won't have datestamps, so the array length will be less than 3
                                if len(quotedata) < 3:
                                    quoteline = quotedata[0]+" (Playing "+quotedata[1]+")"
                                    log.debug("!quote: Quote is in new data format")
                                else:
                                    quoteline = quotedata[0]+" (Playing "+quotedata[1]+" on "+quotedata[2]+")"
                                    log.debug("!quote: Quote is in new data format")
                            except ValueError:
                                log.debug("!quote: Quote is in old data format")
                                quoteline = lines[randomline]
                            
                            send_message(quoteline)
                        except:
                            send_message("Something went wrong Kappa")
                    if message.startswith("!addquote"):
                        if is_mod(username):

                            quote = get_command_arg(parts)

                            if quote:
                                try:
                                    with open(QUOTEFILE, 'a') as txt:
                                        
                                        #Get channel info so we can get the game
                                        thisgame = get_game(MYNICK)

                                        #Get today's date
                                        now = time.strftime("%m/%d/%Y")

                                        #Add the quote
                                        txt.write(quote+"||"+thisgame+"||"+now+"\r")

                                        send_message("Added quote: "+quote+" (Playing "+thisgame+" on "+now+")")
                                except:
                                    send_message("Something went wrong Kappa")
                            else:
                                log.debug("!addquote: No quote provided")
                        else:
                            log.debug("!addquote: %s is a NOT mod",username)
                    if message == "!commands":
                        msg = "Available chat commands are: !commands, !rules, !quote, !uptime, !social"
                        send_message(msg)
                    if message.startswith("!its") or message.startswith("!caster"):
                        if is_mod(username):
                            msg = get_command_arg(parts)
                            if msg:
                                try:
                                    channelinfo = requests.get("https://api.twitch.tv/kraken/channels/"+msg.replace("@", ""))
                                    parsed_json = json.loads(channelinfo.text)

                                    if parsed_json["status"] == 404:
                                        send_message("That doesn't seem to be a valid user, champ.")
                                    else:
                                        url = parsed_json['url']
                                        game = parsed_json['game'].encode("utf-8") # Make sure to encode this to UTF-8 as some game titles have unicode characters in them

                                        if game:
                                            msg = ("Hey, listen! Check out this awesome streamer: "+url+" He/She was just playing %s! \m/").encode("utf-8") % game
                                            send_message(msg)
                                        else:
                                            send_message("Hey, listen! Check out this awesome streamer: "+url+"! \m/")
                                except:
                                    send_message("Something went wrong Kappa")
                        else:
                            log.debug("!caster: %s is a NOT mod", username)
                    if message.startswith("!uptime"):
                        #try:
                            if message == "!uptime":
                                thisnick = MYNICK
                            else:
                                thisnick = get_command_arg(parts)

                            ts = get_uptime(thisnick)
                            msg = ""

                            if ts == UPTIME_404:
                                msg = "User "+thisnick+" does not exist."
                            elif ts == UPTIME_NOTLIVE:
                                msg = "User "+thisnick+" is not live."
                            else:
                                msg = thisnick+" has been live for "+ts+"."

                            send_message(msg)
                        #except:
                        #    send_message("Something went wrong Kappa")

                    if message.startswith("!permit"):

                        if is_mod(username):
                            permitteduser = get_command_arg(parts)

                            if permitteduser:
                                permitteduser = permitteduser.replace("@", "")
                                currenttime = int(time.time())

                                #TO DO: Is this a valid user?

                                PERMITDATA[permitteduser] =  currenttime+PERMITTTL
                                send_message(permitteduser+", you have "+str(PERMITTTL)+" seconds to post a link!")
                                log.debug("!permit: Permit data: %s", str(PERMITDATA))
                            else:
                                log.debug("!permit: Username was missing from permit command")
                        else:
                            log.debug("!permit: %s is not a mod", username)

                    if message.startswith("!highlight"):

                        if is_mod(username):
                            description=get_command_arg(parts) 
                            
                            thisuser=MYNICK
                            #thisuser='monsterousrage'

                            if not description:
                                description = "" 

                            try:
                                with open(HIGHLIGHTFILE, 'a') as txt:
                                                
                                    #Get channel info so we can get the game
                                    thisgame = get_game(thisuser)
                                    ts = get_uptime(thisuser)

                                    msg = ""
                                    if ts == UPTIME_404:
                                        msg = "User "+thisuser+" does not exist."
                                    elif ts == UPTIME_NOTLIVE:
                                        msg = "User "+thisuser+" is not live."
                                    else:
                                        now = time.strftime("%m/%d/%Y")
                                        txt.write(thisgame+"||"+description+"||"+now+"||"+ts+"\r")
                                        msg = "Tagged highlight: "+description+" (Playing "+thisgame+" on "+now+" at "+ts+")"

                                    send_message(msg)
                            except:
                                send_message("Something went wrong, is the streamer live?")
                        else:
                            log.debug("!highlight: %s is not a mod", username)

                    if message == "!social":
                        send_message(SOCIALTEXT)

                    if message == "!rules":
                        send_message(RULETEXT)

                    nummessages+=1

                    if PLUGCYCLE:
                        log.debug("Plug cycle: Number of messages so far: %s", str(nummessages))

                        # Did we reach the threshold of number of messages needed before the next cycle?
                        if not nummessagesreachedflag:
                            nummessagesreachedflag = (nummessages % PLUGMESSAGENUM == 0)

                        # Check if we need to plug the message of the day
                        currenttime = int(time.time())

                        log.debug("Plug cycle: Seconds until next plug is allowed: %s.  Number of messages flag is %s.", str(nextplugtime-currenttime), str(nummessagesreachedflag))
                        if nummessagesreachedflag and currenttime >= nextplugtime:
                            send_message(PLUGMESSAGE)
                            nextplugtime = currenttime + PLUGINTERVAL
                            nummessagesreachedflag = False


                for l in parts:
                    if "End of /NAMES list" in l:
                        MODT = True
