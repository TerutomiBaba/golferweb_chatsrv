import json
import tornado.websocket
import uuid
from src.data import ServerResult
from src.enums import ResultStatus, MethodType
from src.manager import SessionManager
from src.service import ServiceBase, InitService, GetMessagesService, SendMessageService, GetStampsService,\
    GetNewMessagesService
from src.util import ValueUtils
from builtins import staticmethod
from src import log
from src.repository import RepositoryException

initService = InitService()
getNewMessagesService = GetNewMessagesService()
getMessagesService = GetMessagesService()
sendMessageService = SendMessageService()
getStampsService = GetStampsService()

class CompeChatHandler(tornado.websocket.WebSocketHandler):
    logger = log.getLog(__name__)

    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        self.id = str(uuid.uuid4())
        return None

    def on_close(self):
        if log.isDebug():
            self.logger.debug("WebSocket session close:" + self.id);
        SessionManager.removeSession(self);

    def on_message(self, message):
        sessionId = self.id
        if log.isDebug():
            self.logger.debug("セッションID:" + sessionId + ", メッセージ:" + message);
        try:
            form = json.loads(message)
        except ValueError:
            if log.isError():
                self.logger.error("クライアントパラメータのjson変換エラー セッションID:" + sessionId + ", メッセージ:" + message)
            self.write_message(ServerResult.fromStatus(ResultStatus.ParamError).toJson())
            return
        method = MethodType.parse(ValueUtils.getInt(form, "method"))
        if method is None:
            if log.isError():
                self.logger.error("クライアントパラメータの処理タイプ未定義 セッションID:" + sessionId + ", メッセージ:" + message)
            self.write_message(ServerResult.fromStatus(ResultStatus.MethodError).toJson())
            return
        service: ServiceBase = CompeChatHandler.getService(method)
        result = self.executeService(message, form, service);
        result.method = method.value
        self.write_message(result.toJson())

    def executeService(self, message: str, form: dict, service: ServiceBase) -> ServerResult:
        sessionInfo = service.getSessionInfo(self)
        if sessionInfo is None:
            return ServerResult.fromStatus(ResultStatus.LoginError);
        try:
            info: ValidationInfo = service.validate(form)
            if info == None:
                if log.isError():
                    self.logger.error("バリデーション不正(バリデーション結果がnull), メッセージ:" + message)
                return ServerResult.fromStatus(ResultStatus.ValidationError)
            if not info.isValid:
                errors = "[" + ",".join(info.errorMessages) + "]"
                if log.isInfo():
                    self.logger.info("バリデーションエラー(" + info.name + "):" + errors + ", メッセージ:" + message)
                return ServerResult.fromStatus(ResultStatus.ValidationError)
            return service.execute(sessionInfo, service.createParam(form))
        except RepositoryException as ex:
            if log.isError():
                self.logger.exception("リポジトリエラー:%s", ex)
            return ServerResult.fromStatus(ResultStatus.RepositoryError)
        except Exception as ex:
            if log.isError():
                self.logger.exception("サービス実行時のエラー:%s", ex)
            return ServerResult.fromStatus(ResultStatus.ServerError)

    @staticmethod
    def getService(method: MethodType) -> ServiceBase:
        if method == MethodType.Init:
            return initService
        elif method == MethodType.SendMessage:
            return sendMessageService
        elif method == MethodType.GetMessages:
            return getMessagesService
        elif method == MethodType.GetStamps:
            return getStampsService
        elif method == MethodType.GetNewMessages:
            return getNewMessagesService
        return None
