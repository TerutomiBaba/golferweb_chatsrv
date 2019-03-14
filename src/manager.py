#coding: UTF-8

import tornado.websocket

import dataclasses
from src import log
from typing import Any
from src.enums import ReceptLevel

@dataclasses.dataclass
class SessionInfo:
    session: Any
    compeNo: int = None
    memberId: str = None
    receptLevel: ReceptLevel = None

class SessionManager():
    """
    セッション管理
    """
    logger = log.getLog(__name__)
    idSessionMap = dict()
    compeIdsMap = dict()

    @staticmethod
    def addSession(sessionInfo: SessionInfo):
        sessionId = sessionInfo.session.id
        SessionManager.idSessionMap[sessionId] = sessionInfo
        compeNo = sessionInfo.compeNo
        idsMap = SessionManager.compeIdsMap
        if compeNo in idsMap.keys():
            ids = idsMap[compeNo]
        else:
            ids = list()
            idsMap[compeNo] = ids
        ids.append(sessionId)
        if log.isDebug():
            SessionManager.logger.debug("addSession id:" + sessionId + ", compe_no:" + str(compeNo))

    @staticmethod
    def removeSession(session: tornado.websocket.WebSocketHandler):
        sessionId = session.id
        idMap = SessionManager.idSessionMap
        if sessionId in idMap.keys():
            info = idMap.pop(sessionId)
            idsMap = SessionManager.compeIdsMap
            compeNo = info.compeNo
            if compeNo in idsMap.keys():
                idsMap[compeNo].remove(sessionId)
        if log.isDebug():
            SessionManager.logger.debug("removeSession id:" + sessionId)

    @staticmethod
    def getSessionInfos(compeNo: str = None) -> list:
        if compeNo is None:
            return map(lambda it:it.session, SessionManager.idSessionMap.values())
        else:
            idsMap = SessionManager.compeIdsMap
            if compeNo not in idsMap.keys():
                return list()
            return map(lambda it:SessionManager.idSessionMap[it], idsMap[compeNo])

    @staticmethod
    def getSessionInfo(compeNo: str, memberId: str) -> SessionInfo:
        idsMap = SessionManager.compeIdsMap
        if compeNo not in idsMap.keys():
            return None
        infos = list(filter(lambda it:it.memberId == memberId, map(lambda it:SessionManager.idSessionMap[it], idsMap[compeNo])))
        if len(infos) == 0:
            return None
        return infos[0]

    @staticmethod
    def getSessionInfoFromId(sessionId: str) -> SessionInfo:
        idMap = SessionManager.idSessionMap
        if sessionId in idMap.keys():
            return idMap[sessionId]
        return None

