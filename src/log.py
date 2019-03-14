# coding:utf-8

import logging
import configparser

loggers = {}
moduleName = "golferweb-compe-chat"
inifile = configparser.ConfigParser()
inifile.read('./config.ini', 'UTF-8')
logLevel = logging.getLevelName(inifile.get('log', 'level'))

def setting():
    if loggers.get(moduleName):
        return loggers.get(moduleName)
    outputToConsole = inifile.getboolean('log', 'outputToConsole')
    outputToFile = inifile.getboolean('log', 'outputToFile')
    logger = logging.getLogger(moduleName)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    loggers[moduleName] = logger
    formatter = logging.Formatter('%(asctime)s - %(levelname)s [%(name)s %(funcName)s]:%(message)s')
    if outputToConsole:
        # コンソール
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(logLevel)
        logger.addHandler(streamHandler)
    if outputToFile:
        # ファイル
        filePath = inifile.get('log', 'filePath')
        fileBackupCount = int(inifile.get('log', 'fileBackupCount'))
        fileHandler = logging.handlers.TimedRotatingFileHandler(filename=filePath, when='D', interval=1, backupCount=fileBackupCount, encoding='utf-8')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(logLevel)
        logger.addHandler(fileHandler)
    return logger

def killLoggers():
    for logger in loggers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    logging.shutdown()

def getLog(suffix: str):
    return logging.getLogger(moduleName).getChild(suffix)

def isDebug() -> bool:
    return logLevel <= logging.DEBUG

def isInfo() -> bool:
    return logLevel <= logging.INFO

def isWarning() -> bool:
    return logLevel <= logging.WARNING

def isError() -> bool:
    return logLevel <= logging.ERROR

