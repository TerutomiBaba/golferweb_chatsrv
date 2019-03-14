from src.enums import MethodType, ResultStatus
from typing import Any
import json
from src import log

def jsonDefault(OrderedDict):
    return OrderedDict.__dict__

class Serializable(object):
    logger = log.getLog(__name__)

    def __init__(self,*args,**kwargs):
        pass

    def __repr__(self):
        return self.toJson()

    def add_record_as_data(self,_record):
        self.__dict__.update(_record.__dict__)

    def add_record_as_attr(self,_record):
        self.record = _record

    def toJson(self):
        try:
            message = json.dumps(self, default=jsonDefault)
            if log.isDebug():
                self.logger.debug("result message:" + message)
            return message
        except Exception as ex:
            if log.isError():
                self.logger.exception("サーバー返却値のjson変換エラー:%s", ex)
            return "{ \"status\":" + ResultStatus.ResultError.value + " }";

class ServerResult(Serializable):

    @staticmethod
    def fromAll(method: MethodType, status: ResultStatus):
        result = ServerResult()
        result.method = method.value
        result.status = status.value
        return result

    @staticmethod
    def fromStatus(status: ResultStatus) -> Any:
        result = ServerResult()
        result.method = 0
        result.status = status.value
        return result

