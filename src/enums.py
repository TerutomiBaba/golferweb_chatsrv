# coding:utf-8

from enum import Enum
from typing import Any

class ResultStatus(Enum):
    """
    返却ステータス
    """
    Success = 0 #/** 正常 */
    LoginError = 90000 #/** init未実行エラー */
    ParamError = 90001 #/** パラメータ変換エラー */
    ResultError = 90002 #/** 返却値エラー */
    MethodError = 90003 #/** 処理タイプ未定義、あるいはMethodType変換エラー */
    RepositoryError = 90004 #/** リポジトリエラー */
    ValidationError = 90100 #/** パラメータバリデーションエラー */
    ServerError = 99999 #/** サーバー内部エラー */

class ParsableEnum(Enum):
    @classmethod
    def parse(self, value: int) -> Any:
        if value is None:
            return None
        for item in self:
            if item.value == value:
                return item
        return None

class ReceptLevel(ParsableEnum):
    """
    受信レベル
    """
    Gallery = 1 #ギャラリー
    All = 2 #すべて受信

class MethodType(ParsableEnum):
    """
    処理タイプ
    """
    Init = 1 #/** 初期処理 */
    GetMessages = 2 #/** メッセージ取得 */
    SendMessage = 3 #/** メッセージ送信 */
    GetStamps = 4 #/** スタンプ取得 */
    GetNewMessages = 5 #/** 新着メッセージ取得 */
    GetMessagesFromSend = 99 #/** メッセージ取得(送信分) */

class SendType(ParsableEnum):
    """
    送信タイプ
    """
    All = 1 #ギャラリー含む
    Compe = 2 #コンペ参加者
    User = 3 #個人宛


