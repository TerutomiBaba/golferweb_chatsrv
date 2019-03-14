import dataclasses
from abc import abstractmethod
from src.data import ServerResult, Serializable
from typing import TypeVar, Generic, Any
from src.util import ValueUtils
from src.manager import SessionManager, SessionInfo
from src.enums import ResultStatus, SendType, MethodType, ReceptLevel
from src.repository import MessageDatRepository, StampMstRepository, SendMessageData
from src import log

class ValidationInfo:
    """
    バリデーション結果情報
    検証OKとする場合は、valid()を実行し、かつerrorMessagesが存在しない必要がある。
    Attributes:
    name(str):対象サービスクラス名
    isValid(bool):検証結果(true=OK)
    errorMessages(list(str)):エラー内容
    """
    def __init__(self, service: object):
        self.name = service.__class__.__name__
        self.isValid: bool = False
        self.errorMessages = list()

    def valid(self):
        if not self.hasErrorMessages():
            self.isValid = True
        return self

    def addError(self, message: str):
        self.errorMessages.append(message);
        return self

    def hasErrorMessages(self) -> bool:
        return len(self.errorMessages) > 0

P = TypeVar('P')
class ServiceBase(Generic[P]):
    """
    サービス基底クラス
    """
    def getSessionInfo(self, session) -> SessionInfo:
        return SessionManager.getSessionInfoFromId(session.id)

    @abstractmethod
    def validate(self, clientForm: object) -> ValidationInfo:
        """
        バリデーション
        """
        raise NotImplementedError

    @abstractmethod
    def createParam(self, clientForm: object) -> P:
        """
        サービスパラメータ生成
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, sessionInfo: SessionInfo, param: P) -> ServerResult:
        """
        サービス処理実行
        """
        raise NotImplementedError

@dataclasses.dataclass
class InitParam:
    compe_no: int
    member_id: str
    recept_level: ReceptLevel = ReceptLevel.Gallery

class InitService(ServiceBase[InitParam]):

    def getSessionInfo(self, session) -> SessionInfo:
        return SessionInfo(session)

    def validate(self, clientForm: object) -> ValidationInfo:
        info = ValidationInfo(self)
        form = ValueUtils.getAny(clientForm, "init")
        if form is None:
            return info.addError("initパラメータは必須です。")
        compeNo = ValueUtils.getStr(form, "compe_no")
        if compeNo is None:
            info.addError("compe_noは必須です。")
        elif not ValueUtils.isNumeric(compeNo):
            info.addError("compe_noは数値を設定してください。");
        memberId = ValueUtils.getStr(form, "member_id")
        if memberId is None:
            info.addError("member_idは必須です。")
        receptLevel = ReceptLevel.parse(ValueUtils.getInt(form, "recept_level"))
        if receptLevel is None:
            info.addError("recept_levelは必須です。")
        return info.valid();

    def createParam(self, clientForm: object) -> InitParam:
        form = clientForm["init"]
        return InitParam(
                ValueUtils.getInt(form, "compe_no"),
                str(form["member_id"]),
                ReceptLevel.parse(ValueUtils.toInt(form["recept_level"]))
                )

    def execute(self, sessionInfo: SessionInfo, param: InitParam) -> ServerResult:
        sessionInfo.compeNo = param.compe_no
        sessionInfo.memberId = param.member_id
        sessionInfo.receptLevel = param.recept_level
        SessionManager.addSession(sessionInfo);
        return ServerResult.fromStatus(ResultStatus.Success);

@dataclasses.dataclass
class GetNewMessagesParam:
    count: int

class GetNewMessagesService(ServiceBase[GetNewMessagesParam]):

    def validate(self, clientForm: object) -> ValidationInfo:
        info = ValidationInfo(self)
        form = ValueUtils.getAny(clientForm, "get_new_messages")
        if form == None:
            return info.addError("get_new_messagesパラメータは必須です。");
        count = ValueUtils.getStr(form, "count")
        if count == None:
            info.addError("countは必須です。");
        elif not ValueUtils.isNumeric(count):
            info.addError("countは数値を設定してください。");
        return info.valid();

    def createParam(self, clientForm: object) -> GetNewMessagesParam:
        form = clientForm["get_new_messages"]
        return GetNewMessagesParam(
                ValueUtils.getInt(form, "count")
                )

    def execute(self, sessionInfo: SessionInfo, param: GetNewMessagesParam) -> ServerResult:
        messages = list()
        with MessageDatRepository() as messageDat:
            datas = messageDat.findMessages(sessionInfo.receptLevel, 0, param.count, sessionInfo.compeNo, sessionInfo.memberId, True)
            for data in datas:
                message = Serializable()
                message.send_type = data.send_type
                message.message_id = data.message_id
                message.compe_no = data.compe_no
                message.member_id = data.member_id
                message.time = data.time
                message.message = data.message
                message.stamp = data.stamp
                messages.append(message)
        result = ServerResult.fromStatus(ResultStatus.Success)
        result.messages = messages
        return result

@dataclasses.dataclass
class GetMessagesParam:
    before_time: int
    count: int

class GetMessagesService(ServiceBase[GetMessagesParam]):

    def validate(self, clientForm: object) -> ValidationInfo:
        info = ValidationInfo(self)
        form = ValueUtils.getAny(clientForm, "get_messages")
        if form == None:
            return info.addError("get_messagesパラメータは必須です。");
        beforeTime = ValueUtils.getStr(form, "before_time")
        if beforeTime == None:
            info.addError("before_timeは必須です。");
        elif not ValueUtils.isNumeric(beforeTime):
            info.addError("before_timeは数値を設定してください。");
        count = ValueUtils.getStr(form, "count")
        if count == None:
            info.addError("countは必須です。");
        elif not ValueUtils.isNumeric(count):
            info.addError("countは数値を設定してください。");
        return info.valid();

    def createParam(self, clientForm: object) -> GetMessagesParam:
        form = clientForm["get_messages"]
        return GetMessagesParam(
                ValueUtils.getInt(form, "before_time"),
                ValueUtils.getInt(form, "count")
                )

    def execute(self, sessionInfo: SessionInfo, param: GetMessagesParam) -> ServerResult:
        messages = list()
        with MessageDatRepository() as messageDat:
            datas = messageDat.findMessages(sessionInfo.receptLevel, param.before_time, param.count, sessionInfo.compeNo, sessionInfo.memberId, False)
            for data in datas:
                message = Serializable()
                message.send_type = data.send_type
                message.message_id = data.message_id
                message.compe_no = data.compe_no
                message.member_id = data.member_id
                message.time = data.time
                message.message = data.message
                message.stamp = data.stamp
                messages.append(message)
        result = ServerResult.fromStatus(ResultStatus.Success)
        result.messages = messages
        return result

@dataclasses.dataclass
class SendMessageParam:
    send_type: int
    dest_member_id: str
    message: str
    stamp_id: str

class SendMessageService(ServiceBase[SendMessageParam]):
    logger = log.getLog(__name__)

    def validate(self, clientForm: object) -> ValidationInfo:
        info = ValidationInfo(self)
        form = ValueUtils.getAny(clientForm, "send_message")
        if form is None:
            return info.addError("send_messageパラメータは必須です。")
        if ValueUtils.isEmpty(ValueUtils.getStr(form, "message")) and ValueUtils.isEmpty(ValueUtils.getStr(form, "stamp_id")):
            info.addError("send_messageには、messageとstamp_idのいずれかが必須です。")
        # 送信先のパラメータは厳密にチェックし、誤送信をなるべく防ぐ。
        sendType = SendType.parse(ValueUtils.getInt(form, "send_type"))
        if sendType is None:
            return info.addError("send_message.send_typeが正しくありません。")
        destMemberId = ValueUtils.getStr(form, "dest_member_id")
        if sendType == SendType.All:
            if destMemberId is not None:
                return info.addError("全員に送信する場合は、send_message.dest_member_idをnullにしてください。")
        elif sendType == SendType.Compe:
            if destMemberId is not None:
                return info.addError("コンペ指定で送信する場合は、send_message.dest_member_idをnullにしてください。")
        elif sendType == SendType.User:
            if destMemberId is None:
                return info.addError("ユーザー指定で送信する場合は、send_message.dest_member_idは必須です。")
        return info.valid();

    def createParam(self, clientForm: object) -> SendMessageParam:
        form = clientForm["send_message"]
        return SendMessageParam(
                SendType.parse(ValueUtils.getInt(form, "send_type")),
                ValueUtils.getStr(form, "dest_member_id"),
                ValueUtils.getStr(form, "message"),
                ValueUtils.getStr(form, "stamp_id")
                )

    def execute(self, sessionInfo: SessionInfo, param: SendMessageParam) -> ServerResult:
        compeNo = sessionInfo.compeNo
        memberId = sessionInfo.memberId
        sendType = param.send_type
        destMemberId = param.dest_member_id
        data = SendMessageData(
                None,
                sendType.value,
                compeNo,
                destMemberId,
                memberId,
                ValueUtils.getTimeInMillis(),
                param.message,
                param.stamp_id,
                False
                )
        with MessageDatRepository() as messageRepository:
            messageRepository.save(data);
        message = Serializable()
        message.send_type = data.send_type
        message.message_id = data.message_id
        message.compe_no = data.compe_no
        message.member_id = data.member_id
        message.time = data.time
        message.message = data.message
        with StampMstRepository() as stampRepository:
            stamp = stampRepository.findStamp(data.stamp_id)
            if stamp is not None:
                message.stamp = stamp.stamp_url
        otherResult = ServerResult.fromStatus(ResultStatus.Success)
        otherResult.messages = list()
        otherResult.messages.append(message)
        methodType = MethodType.GetMessagesFromSend
        otherResult.method = methodType.value
        otherMessage = otherResult.toJson()
        sendList: list[SessionInfo]
        if sendType == SendType.User:
            # 個人宛の場合、送信者と宛先のみ
            sendList = [
                SessionManager.getSessionInfo(compeNo, memberId),
                SessionManager.getSessionInfo(compeNo, destMemberId)
                ]
        elif sendType == SendType.All:
            sendList = SessionManager.getSessionInfos(compeNo)
        else:
            sendList = filter(lambda it:it.receptLevel == ReceptLevel.All, SessionManager.getSessionInfos(compeNo))
        for info in sendList:
            if info is None:
                continue
            info.session.write_message(otherMessage)
            if log.isDebug():
                self.logger.debug("Send message to others sessions id:" + info.session.id)
        return ServerResult.fromStatus(ResultStatus.Success)

class GetStampsService(ServiceBase[Any]):
    def validate(self, clientForm: object) -> ValidationInfo:
        return ValidationInfo(self).valid()

    def createParam(self, clientForm: object) -> Any:
        return None

    def execute(self, sessionInfo: SessionInfo, param: Any) -> ServerResult:
        stamps = list()
        with StampMstRepository() as stampMst:
            datas = stampMst.findStamps()
            for data in datas:
                stamp = Serializable()
                stamp.stamp_id = data.stamp_id
                stamp.stamp_url = data.stamp_url
                stamps.append(stamp)
        result = ServerResult.fromStatus(ResultStatus.Success)
        result.stamps = stamps
        return result

