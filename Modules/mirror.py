import eventing
import threading
import requests
import json
import time
import random
from textToSpeechAI import speak
from speechRecAI import SpeechAI
import faceAI
import time
import weatherAI
import newsAI
import mapsAI
import traceback
import languageAI
import mailCheckAI
import mailAI
import selfieAI
from server import sendToClient, sendJSON, setHandler
import datetime

wit_token = "Bearer A5YKQ3WVJPMYBDUA655USHMZ3HHJ4ZQE"
launchPhrases = ["ok mirror","ok a mirror","okay mirror","okey mirror","ok mera","okay mera","uk mirror"]
useLaunchPhrase = False

myName = "Boaty McBoatface"

def respond(toSpeak, toSend = False):
    if not toSend and not toSpeak:
        return
    elif not toSend:
        toSend = toSpeak

    if (isinstance(toSend, str)):
        sendToClient(toSend)
    else:
        sendJSON(toSend)

    if toSpeak:
        speak(toSpeak)


activeMode = False

def onConnected():
    global activeMode
    if activeMode:
        respond(
            False,
            {
                "type": "command",
                "command": "active-mode"
            }
        )
    else:
        respond(
            False,
            {
                "type": "command",
                "command": "passive-mode"
            }
        )

class mirror(object):

    def __init__(self):
        global activeMode
        self.speech = SpeechAI(0.30)
        self.face = faceAI.faceAI(camera=1)
        self.weather = weatherAI.weather()
        self.news = newsAI.news()
        self.maps = mapsAI.maps()
        self.lang = languageAI.naturalLanguageAI(myName)
        activeMode = False
        self.passivePollData = {
            "headlines": {
                "refresh": 60*60, #60 minutes
                "lastDone": 0
            },
            "quotes": {
                "refresh": 3*60,
                "lastDone": 0
            },
            "weather": {
                "refresh": 5*60*60,
                "lastDone": 0
            },
            "mess-meal": {
                "refresh": 3*60,
                "lastDone": 0
            }
        }

        setHandler(onConnected)

        # info of song will be sent by its thread
    def initialize(self):
        global activeMode
        inertia = 120 # seconds
        lastSpoken = 0 #used for inertia logic
        lastFace = 0

        respond(
            False,
            {
                "type": "command",
                "command": "passive-mode"
            }
        )

        def init_active_mode():
            global activeMode
            activeMode = True
            respond(
                "Hi " + random.choice(["pretty", "beautiful", "sexy", "cutie", "handsome", "lovely"]),
                {
                    "type": "command",
                    "command": "active-mode"
                }
            )

        def passive_bg_jobs():
            global activeMode
            while True:
                if not activeMode: # passive mode
                    for k in self.passivePollData:
                        if (time.time() - self.passivePollData[k]["lastDone"] > self.passivePollData[k]["refresh"]):
                            if(k == "headlines"):
                                response = self.news.findNews(random.choice(["india", "general", "tech"]))
                            elif(k == "weather"):
                                LJ = self.weather.getLocation()
                                response, spk = self.weather.findWeather("7-day", LJ)
                            respond(False, response)
                            self.passivePollData[k]["lastDone"] = time.time()

        passiveThread = threading.Thread(target = passive_bg_jobs)
        passiveThread.daemon = True
        passiveThread.start()

        while True:
            if activeMode:
                if useLaunchPhrase:
                    record, audio = self.speech.ears()
                    respond(False, "I'm all ears")
                    speech = self.speech.recognize(record,audio)
                    if speech is not None and speech.lower() in launchPhrases:
                        ack = self.lang.acknowledge()
                        respond(ack)
                        action = self.action()
                else:
                    action = self.action()

                if action:
                    lastSpoken = time.time()

            # inertia logic
            print("t", time.time() - max(lastFace, lastSpoken))
            if activeMode and time.time() - max(lastFace, lastSpoken) > inertia:
                respond(
                    False,
                    {
                        "type": "command",
                        "command": "passive-mode"
                    }
                )
                activeMode = False

            if self.face.detect_face():
                lastFace = time.time()
                if not activeMode:
                    print("Found face")
                    init_active_mode()

    def action(self):
        record, audio = self.speech.ears()
        speech = self.speech.recognize(record,audio)
        # speech = input()
        if speech is not None and speech != []:
            try:
                r = requests.get('https://api.wit.ai/message?v=20170303&q=%s' % speech,
                                         headers={"Authorization": wit_token})
                print(r.text)
                response = json.loads(r.text)
                entities = []

                if 'entities' in response:
                    entities = response['entities']

                print(entities)

                """
                Takes action based on this intent
                Only maps, news, weather as of now
                """

                if "maps" in entities:
                    self.findMaps(entities)
                elif "news" in entities:
                    self.findNews(entities)
                elif "weather" in entities:
                    self.findWeather(entities)
                elif "userStatus" in entities:
                    self.userStatus(entities)
                elif "interaction" in entities:
                    self.interaction(entities)
                elif "transfer" in entities:
                    self.transferFunctions(entities)
                else:
                    respond("I'm Sorry, I couldn't understand what you meant by that")

            except Exception as e:
                print(e)
                traceback.print_exc()
                respond("I'm Sorry, I couldn't understand what you meant by that")
                return

            return True # for a successful interaction
        elif speech == []:
            return None
        else:
            print("mirror.py: speech is None")
            return False

    def findMaps(self,entities=None):
        if entities is not None:
            maxConf = 0
            intent = entities['maps'][0]["value"]
            location = entities['location'][0]["value"]
            for i in entities['location']:
                if i["confidence"] > maxConf:
                    maxConf = i["confidence"]
                    location = i["value"]
            print(intent)
            print(location)

            if location is not None and intent is not None:
                LJ = self.maps.getLocation(location) #@madhur why is LJ needed here?
                respond("Here is a map of " + location, {"type": "image", "src": self.maps.findMap(intent,location)})
            else:
                respond("I'm Sorry, I couldn't retrieve maps at the moment")
        else:
            respond("I'm Sorry, I couldn't understand what you meant by that")

    def findNews(self,entities=None):
        apiObject = {"type": "news"}
        if entities is not None:
            intent = entities['news'][0]["value"]
            print("news intent", intent)
            if intent is not None:
                newsList = self.news.findNews(intent)
                respond(", ".join(map(lambda x: x["title"], newsList)), {"type": "news", "items": newsList})
            else:
                respond("I'm Sorry, I couldn't retrieve news at the moment")
        else:
            respond("I'm Sorry, I couldn't understand what you meant by that")

    def findWeather(self,entities=None):
        if entities is not None:
            if "location" in entities:
                intent = entities['weather'][0]["value"]
                maxConf = 0
                location = entities['location'][0]["value"]
                for i in entities['location']:
                    if i["confidence"] > maxConf:
                        maxConf = i["confidence"]
                        location = i["value"]
                if location is not None:
                    LJ = self.weather.get_DifferentLocation(location)
                    response, spk = self.weather.findWeather(intent,LJ)
                    respond(spk, {
                        "type": "weather",
                        "location": location,
                        "intent": intent,
                        "data": response
                    })
                else:
                    respond("I'm Sorry, I couldn't retrieve weather info at the moment")
            else:
                intent = entities['weather'][0]["value"]
                print(intent)
                LJ = self.weather.getLocation()
                response, spk = self.weather.findWeather(intent, LJ)
                respond(spk, {
                    "type": "weather",
                    "intent": intent,
                    "data": response
                })
        else:
            respond("I'm Sorry, I couldn't understand what you meant by that")

    def userStatus(self,entities=None):
        property = None
        if entities is not None:
            property = entities['userStatus'][0]['value']
        i = random.randint(0,2)
        category = "neutral"
        if i == 0:
            category = "positive"
        elif i==1:
            category = "negative"
        else:
            category = "neutral"
        phrase = self.lang.user_compliment(category,property)
        respond(phrase)

    def interaction(self,entities=None):
        property = None
        if entities is not None:
            property = entities['interaction'][0]['value']
        phrase = self.lang.interaction(property)
        respond(phrase)

    def transferFunctions(self,entities=None):
        if entities is not None:
            intent = entities['transfer'][0]['value']
            if intent == "check-mail":
                mailCheckAI.checkMail()
            elif intent == "send-mail":
                mailAI.SendMail()
            elif intent == "selfie":
                base = "../client/selfies/"
                selfieAI.capture()
                selfieAI.SendMail(base+'filename.jpg')


if __name__ == "__main__":
    M = mirror()
    M.initialize()
