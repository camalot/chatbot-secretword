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
import logging
from logging.handlers import TimedRotatingFileHandler

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
ReadMeFile = "https://github.com/" + Repo + "/blob/develop/ReadMe.md"

UIConfigFile = os.path.join(os.path.dirname(__file__), "UI_Config.json")
WordFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "./secretwords.txt")
SettingsFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
ScriptSettings = None
Initialized = False

CurrentSecretWord = None
CurrentWordRegex = None
KnownBots = None
Logger = None

class Settings(object):
    """ Class to hold the script settings, matching UI_Config.json. """

    def __init__(self, settingsfile=None):
        """ Load in saved settings file if available else set default values. """
        defaults = self.DefaultSettings(UIConfigFile)
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                settings = json.load(f, encoding="utf-8")
            self.__dict__ = Merge(defaults, settings)
        except Exception as ex:
            if Logger:
                Logger.error(str(ex))
            else:
                Parent.Log(ScriptName, str(ex))
            self.__dict__ = defaults

    def DefaultSettings(self, settingsfile=None):
        defaults = dict()
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
            ui = json.load(f, encoding="utf-8")
        for key in ui:
            if 'value' in ui[key]:
                try:
                    defaults[key] = ui[key]['value']
                except:
                    if key != "output_file":
                        if Logger:
                            Logger.warn("DefaultSettings(): Could not find key {0} in settings".format(key))
                        else:
                            Parent.Log(ScriptName, "DefaultSettings(): Could not find key {0} in settings".format(key))
        return defaults
    def Reload(self, jsonData):
        """ Reload settings from the user interface by given json data. """
        if Logger:
            Logger.debug("Reload Settings")
        else:
            Parent.Log(ScriptName, "Reload Settings")
        self.__dict__ = Merge(self.DefaultSettings(UIConfigFile), json.loads(jsonData, encoding="utf-8"))


class StreamlabsLogHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            message = self.format(record)
            Parent.Log(ScriptName, message)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def GetLogger():
    log = logging.getLogger(ScriptName)
    log.setLevel(logging.DEBUG)

    sl = StreamlabsLogHandler()
    sl.setFormatter(logging.Formatter("%(funcName)s(): %(message)s"))
    sl.setLevel(logging.INFO)
    log.addHandler(sl)

    fl = TimedRotatingFileHandler(filename=os.path.join(os.path.dirname(
        __file__), "info"), when="w0", backupCount=8, encoding="utf-8")
    fl.suffix = "%Y%m%d"
    fl.setFormatter(logging.Formatter(
        "%(asctime)s  %(funcName)s(): %(levelname)s: %(message)s"))
    fl.setLevel(logging.INFO)
    log.addHandler(fl)

    if ScriptSettings.DebugMode:
        dfl = TimedRotatingFileHandler(filename=os.path.join(os.path.dirname(
            __file__), "debug"), when="h", backupCount=24, encoding="utf-8")
        dfl.suffix = "%Y%m%d%H%M%S"
        dfl.setFormatter(logging.Formatter(
            "%(asctime)s  %(funcName)s(): %(levelname)s: %(message)s"))
        dfl.setLevel(logging.DEBUG)
        log.addHandler(dfl)

    log.debug("Logger initialized")
    return log

def Init():
    global ScriptSettings
    global Initialized
    global KnownBots
    global Logger

    if Initialized:
        Logger.debug("Skip Initialization. Already Initialized.")
        return
    ScriptSettings = Settings(SettingsFile)
    Logger = GetLogger()

    Logger.debug("Initialize")

    if KnownBots is None:
        try:
            botData = json.loads(json.loads(Parent.GetRequest(
                "https://api.twitchinsights.net/v1/bots/online", {}))['response'])['bots']
            KnownBots = [bot[0].lower() for bot in botData]
        except:
            Logger.error(str(e))
            KnownBots = []
    # Load saved settings and validate values

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
    Logger.debug("State Changed: " + str(state))
    if state:
        Init()
        if CurrentSecretWord is None:
            SetSecretWord()
        else:
            Logger.debug("Current Word is already: " + CurrentSecretWord)
    else:
        Unload()
        ClearSecretWord()
    return

# ---------------------------------------
# [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
# ---------------------------------------

def ReloadSettings(jsondata):
    Logger.debug("Reload Settings")
    # Reload saved settings and validate values
    Unload()
    Init()
    return



def Parse(parseString, user, target, message):
    resultString = parseString or ""
    resultString = resultString.replace("$awardedpoints", str(int(ScriptSettings.Points)))
    resultString = resultString.replace("$secretword", CurrentSecretWord or "")
    resultString = resultString.replace("$username", user or "")
    resultString = resultString.replace("$userid", target or "")
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

    Logger.debug("SECRET WORD: " + str(CurrentSecretWord))

def IsTwitchBot(user):
    return user.lower() in KnownBots


def Merge(source, destination):
    """
    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            Merge(value, node)
        elif isinstance(value, list):
            destination.setdefault(key, value)
        else:
            if key in destination:
                pass
            else:
                destination.setdefault(key, value)

    return destination

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
    Logger.debug(libsDir)
    try:
        src_files = os.listdir(libsDir)
        tempdir = tempfile.mkdtemp()
        Logger.debug(tempdir)
        for file_name in src_files:
            full_file_name = os.path.join(libsDir, file_name)
            if os.path.isfile(full_file_name):
                Logger.debug("Copy: " + full_file_name)
                shutil.copy(full_file_name, tempdir)
        updater = os.path.join(tempdir, "ApplicationUpdater.exe")
        updaterConfigFile = os.path.join(tempdir, "update.manifest")
        repoVals = Repo.split('/')
        updaterConfig = {
            "path": os.path.realpath(os.path.join(currentDir, "../")),
            "version": Version,
            "name": ScriptName,
            "requiresRestart": True,
            "kill": [],
            "execute": {
                "before": [{
                    "command": "cmd",
                    "arguments": [ "/c", "del /q /f /s *" ],
                    "workingDirectory": "${PATH}\\${FOLDERNAME}\\Libs\\updater\\",
                    "ignoreExitCode": True,
                    "validExitCodes": [ 0 ]
                }],
                "after": []
            },
            "application": os.path.join(chatbotRoot, "Streamlabs Chatbot.exe"),
            "folderName": os.path.basename(os.path.dirname(os.path.realpath(__file__))),
            "processName": "Streamlabs Chatbot",
            "website": Website,
            "repository": {
                "owner": repoVals[0],
                "name": repoVals[1]
            }
        }
        Logger.debug(updater)
        configJson = json.dumps(updaterConfig)
        Logger.debug(configJson)
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


def OpenPaypalDonateLink():
    os.startfile("https://paypal.me/camalotdesigns/10")
    return
def OpenGithubDonateLink():
    os.startfile("https://github.com/sponsors/camalot")
    return
def OpenTwitchDonateLink():
    os.startfile("http://twitch.tv/darthminos/subscribe")
    return
def OpenDiscordLink():
    os.startfile("https://discord.com/invite/vzdpjYk")
    return
