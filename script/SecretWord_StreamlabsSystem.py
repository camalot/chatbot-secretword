#---------------------------------------
#   Import Libraries
#---------------------------------------
import sys
import clr
import json
import codecs
import os
import re
import random
import datetime
import glob
import time
import threading
import shutil
import tempfile
from HTMLParser import HTMLParser
import argparse

clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

# clr.AddReferenceToFileAndPath(os.path.join(os.path.dirname(
#     os.path.realpath(__file__)), "./libs/ChatbotSystem.dll"))
# import ChatbotSystem


#---------------------------------------
#   [Required] Script Information
#---------------------------------------
ScriptName = "Secret Word"
Website = "http://darthminos.tv"
Description = "Sets A Secret Word and awards points when found"
Creator = "DarthMinos"
Version = "1.0.0-snapshot"
Repo = "camalot/chatbot-secretword"

DonateLink = "https://paypal.me/camalotdesigns"
ReadMeFile = "https://github.com/" + Repo + "/blob/develop/ReadMe.md"

WordFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "./secretwords.txt")
SettingsFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
ScriptSettings = None
Initialized = False

CurrentSecretWord = None
CurrentWordRegex = None
KnownBots = None

class Settings(object):
    """ Class to hold the script settings, matching UI_Config.json. """

    def __init__(self, settingsfile=None):
        """ Load in saved settings file if available else set default values. """
        try:
            self.SoundFile = ""
            self.SoundVolume = 100
            self.Points = 100
            self.OnlyWhenLive = True
            self.Response = "@$username Discovered the secret word: $secretword and was awarded $awardedpoints $currencyname (total: $points $currencyname)"
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                fileSettings = json.load(f, encoding="utf-8")
                self.__dict__.update(fileSettings)

        except Exception as e:
            Parent.Log(ScriptName, str(e))

    def Reload(self, jsonData):
        """ Reload settings from the user interface by given json data. """
        Parent.Log(ScriptName, "Reload Settings")
        fileLoadedSettings = json.loads(jsonData, encoding="utf-8")
        self.__dict__.update(fileLoadedSettings)




def Init():
    global ScriptSettings
    global Initialized
    global KnownBots
    if Initialized:
        Parent.Log(ScriptName, "Skip Initialization. Already Initialized.")
        return

    Parent.Log(ScriptName, "Initialize")

    if KnownBots is None:
        botData = json.loads(json.loads(Parent.GetRequest(
            "https://api.twitchinsights.net/v1/bots/online", {}))['response'])['bots']
        KnownBots = [bot[0] for bot in botData]
    # Load saved settings and validate values
    ScriptSettings = Settings(SettingsFile)

    if CurrentSecretWord is None:
        SetSecretWord()

    Initialized = True
    return

def Unload():
    global Initialized
    Initialized = False
    return

def Execute(data):
    if ScriptSettings.OnlyWhenLive and not Parent.IsLive():
        return
    if data.IsChatMessage():

        # !secretword : As you type in chat, if you use the random secret word you will be awarded $awardedpoints $currencyname.
        commandTrigger = data.GetParam(0).lower()
        if commandTrigger == "!secretword":
            if data.GetParamCount() > 1:
                subCommand = data.GetParam(1).lower()
                fullSub = "{0} {1}".format(commandTrigger, subCommand)
                if not Parent.IsOnCooldown(ScriptName, fullSub):
                    Parent.AddCooldown(ScriptName, fullSub, 30)
                    pass
            else:
                if not Parent.IsOnCooldown(ScriptName, commandTrigger):
                    Parent.AddCooldown(ScriptName, commandTrigger, 30)
                    Parent.SendTwitchMessage(Parse("As you type in chat, if you use the random secret word you will be awarded $awardedpoints $currencyname", data.UserName, data.User, data.Message))
        # ignore messages from bots
        if not IsTwitchBot(data.UserName):
            if CurrentSecretWord and CurrentWordRegex:
                match = CurrentWordRegex.search(data.Message.lower())
                if match:
                    # Add Points?
                    Parent.AddPoints(data.User, data.UserName, ScriptSettings.Points)
                    # Play Sound?
                    if ScriptSettings.SoundFile and os.path.exists(ScriptSettings.SoundFile):
                        Parent.PlaySound(ScriptSettings.SoundFile, ScriptSettings.SoundVolume / 100)
                    # Notify chat
                    if ScriptSettings.Response:
                        Parent.SendTwitchMessage(Parse(ScriptSettings.Response, data.UserName, data.User, ScriptSettings.Response))
                    # Get New Word
                    SetSecretWord()
            return
    return

def Tick():
    if ScriptSettings.OnlyWhenLive and not Parent.IsLive() and CurrentSecretWord:
        ClearSecretWord()
    elif Parent.IsLive() and CurrentSecretWord is None:
        SetSecretWord()
    return

def ScriptToggled(state):
    Parent.Log(ScriptName, "State Changed: " + str(state))
    if state:
        Init()
        if CurrentSecretWord is None:
            SetSecretWord()
        else:
            Parent.Log(ScriptName, "Current Word is already: " + CurrentSecretWord)
    else:
        Unload()
        ClearSecretWord()
    return

# ---------------------------------------
# [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
# ---------------------------------------

#### IT IS NOT RELOADING THE SETTINGS ON SAVE
def ReloadSettings(jsondata):
    Parent.Log(ScriptName, "Reload Settings")
    # Reload saved settings and validate values
    Unload()
    Init()
    return



def Parse(parseString, user, target, message):
    resultString = parseString
    resultString = resultString.replace("$awardedpoints", str(int(ScriptSettings.Points)))
    resultString = resultString.replace("$secretword", CurrentSecretWord)
    resultString = resultString.replace("$username", user)
    resultString = resultString.replace("$userid", target)
    resultString = resultString.replace("$currencyname", Parent.GetCurrencyName())
    resultString = resultString.replace("$points", str(int(Parent.GetPoints(target))))
    return resultString


def ClearSecretWord():
    global CurrentSecretWord
    global CurrentWordRegex
    CurrentSecretWord = None
    CurrentWordRegex = None

def SetSecretWord():
    global CurrentSecretWord
    global CurrentWordRegex

    CurrentSecretWord = random_line(WordFile)
    CurrentWordRegex = re.compile(r"\b{0}\b".format(CurrentSecretWord.lower()), re.UNICODE)

    Parent.Log(ScriptName, "SECRET WORD: " + str(CurrentSecretWord))

def IsTwitchBot(user):
    return user in KnownBots

def str2bool(v):
    if not v:
        return False
    return stripQuotes(v).strip().lower() in ("yes", "true", "1", "t", "y")

def stripQuotes(v):
    r = re.compile(r"^[\"\'](.*)[\"\']$", re.U)
    m = r.search(v)
    if m:
        return m.group(1)
    return v


def random_line(filename):
    with open(filename) as f:
        lines = f.readlines()
        return random.choice(lines).strip()

def OpenScriptUpdater():
    currentDir = os.path.realpath(os.path.dirname(__file__))
    chatbotRoot = os.path.realpath(os.path.join(currentDir, "../../../"))
    libsDir = os.path.join(currentDir, "libs/updater")
    Parent.Log(ScriptName, libsDir)
    try:
        src_files = os.listdir(libsDir)
        tempdir = tempfile.mkdtemp()
        Parent.Log(ScriptName, tempdir)
        for file_name in src_files:
            full_file_name = os.path.join(libsDir, file_name)
            if os.path.isfile(full_file_name):
                Parent.Log(ScriptName, "Copy: " + full_file_name)
                shutil.copy(full_file_name, tempdir)
        updater = os.path.join(tempdir, "ChatbotScriptUpdater.exe")
        updaterConfigFile = os.path.join(tempdir, "update.manifest")
        repoVals = Repo.split('/')
        updaterConfig = {
            "path": os.path.realpath(os.path.join(currentDir, "../")),
            "version": Version,
            "name": ScriptName,
            "requiresRestart": True,
            "kill": [],
            "execute": {
                "before": [],
                "after": []
            },
            "chatbot": os.path.join(chatbotRoot, "Streamlabs Chatbot.exe"),
            "script": os.path.basename(os.path.dirname(os.path.realpath(__file__))),
            "website": Website,
            "repository": {
                "owner": repoVals[0],
                "name": repoVals[1]
            }
        }
        Parent.Log(ScriptName, updater)
        configJson = json.dumps(updaterConfig)
        Parent.Log(ScriptName, configJson)
        with open(updaterConfigFile, "w+") as f:
            f.write(configJson)
        os.startfile(updater)
        return
    except OSError as exc:  # python >2.5
        raise
    return


def OpenFollowOnTwitchLink():
    os.startfile("https://twitch.tv/DarthMinos")
    return


def OpenReadMeLink():
    os.startfile(ReadMeFile)
    return


def OpenWordFile():
    os.startfile(WordFile)
    return

def OpenDonateLink():
    os.startfile(DonateLink)
    return
