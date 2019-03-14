from typing import Any
import datetime

class ValueUtils:
    @staticmethod
    def isNumeric(value: Any) -> bool:
        valType = type(value)
        if valType is int:
            return True
        elif valType is str and (value and value.strip()):
            return value.isnumeric()
        else:
            return False

    @staticmethod
    def isEmpty(value: Any) -> bool:
        if not value:
            return True
        valType = type(value)
        if valType is str:
            return not (value and value.strip())
        else:
            return False

    @staticmethod
    def toInt(value: Any) -> int:
        valType = type(value)
        if valType is int:
            return value
        elif valType is str:
            return int(value, 10)

    @staticmethod
    def toStr(value: Any) -> str:
        valType = type(value)
        if valType is int:
            return str(value)
        elif valType is str:
            return value

    @staticmethod
    def toBool(value: Any) -> str:
        valType = type(value)
        if valType is bool:
            return value
        elif valType is str:
            return value.lower() == "true"
        return False

    @staticmethod
    def getStr(datas: dict, key: str) -> str:
        if key in datas.keys():
            val = datas[key]
            return ValueUtils.toStr(val)
        return None

    @staticmethod
    def getInt(datas: dict, key: str) -> int:
        if key in datas.keys():
            val = datas[key]
            return ValueUtils.toInt(val)
        return None

    @staticmethod
    def getBool(datas: dict, key: str) -> bool:
        if key in datas.keys():
            val = datas[key]
            return ValueUtils.toBool(val)
        return False

    @staticmethod
    def getAny(datas: dict, key: str) -> Any:
        if key in datas.keys():
            return datas[key]
        return None

    @staticmethod
    def getTimeInMillis() -> int:
        return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
