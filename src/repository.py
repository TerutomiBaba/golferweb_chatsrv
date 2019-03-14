import mysql.connector
import dataclasses
import configparser
from src.util import ValueUtils
from builtins import str
from src import log
from src.enums import ReceptLevel

inifile = configparser.ConfigParser()
inifile.read('./config.ini', 'UTF-8')
DB_HOST = inifile.get('db', 'host')
DB_PORT = ValueUtils.toInt(inifile.get('db', 'port'))
DB_USER = inifile.get('db', 'user')
DB_PASSWORD = inifile.get('db', 'password')
DB_SCHEMA = inifile.get('db', 'schema')

def get_connection() -> mysql.connector:
    return mysql.connector.connect(
            host = DB_HOST,
            port = DB_PORT,
            user = DB_USER,
            password = DB_PASSWORD,
            database = DB_SCHEMA,
            auth_plugin='mysql_native_password'
        )

class RepositoryException(Exception):
    def __init__(self, message, *errors):
        Exception.__init__(self, message)
        self.errors = errors

class RepositoryBase:
    logger = log.getLog(__name__)
    conn: mysql.connector
    useTransaction: bool = False
    isComplete: bool = False

    def __init__(self):
        try:
            self.conn = get_connection()
        except Exception as e:
            raise RepositoryException(*e.args)
        self.isComplete = False

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def complete(self):
        self.isComplete = True

    def close(self):
        if self.conn:
            try:
                if self.useTransaction:
                    if self.isComplete:
                        self.conn.commit()
                    else:
                        self.conn.rollback()
                        if log.isDebug():
                            self.logger.debug("rollbacked")
            except Exception as e:
                raise RepositoryException(*e.args)
            finally:
                try:
                    self.conn.close()
                except Exception as e:
                    raise RepositoryException(*e.args)

    def checkConnect(self, conn: mysql.connector):
        isConnected = conn.is_connected()
        if not isConnected:
            conn.ping(True)

    def query(self, sql: str, param: tuple = ()) -> mysql.connector.cursor:
        try:
#            self.logger.debug("sql:" + sql)
            conn = self.conn
            self.checkConnect(conn)
            cur = self.conn.cursor(dictionary=True)
            cur.execute(sql, param)
            if log.isDebug():
                self.logger.debug("sql:" + cur.statement)
            return cur
        except Exception as e:
            raise RepositoryException(*e.args)

    def execute(self, sql: str, param: tuple = ()) -> mysql.connector.cursor:
        try:
            self.useTransaction = True
            conn = self.conn
            self.checkConnect(conn)
            cur = self.conn.cursor(dictionary=True)
            cur.execute(sql, param)
            if log.isDebug():
                self.logger.debug("sql:" + cur.statement)
            self.isComplete = True
            return cur
        except Exception as e:
            self.isComplete = False
            raise RepositoryException(*e.args)

#     def getCursor(self, useTransaction: bool):
#         if useTransaction:
#             self.useTransaction = True
#         conn = self.conn
#         self.checkConnect(conn)
#         return self.conn.cursor(dictionary=True)

    def ifStr(self, condition: bool, callback) -> str:
        if condition:
            return callback()
        return ""

@dataclasses.dataclass
class SendMessageData:
    message_id: int
    send_type: int
    compe_no: int
    dest_member_id: str
    member_id: str
    time: int
    message: str
    stamp_id: str
    is_delete: bool

@dataclasses.dataclass
class GetMessagesData:
    message_id: int
    send_type: int
    compe_no: int
    member_id: str
    time: int
    message: str
    stamp: str

class MessageDatRepository(RepositoryBase):

    def findMessages(self, receptLevel: ReceptLevel, beforeTime: int, count: int, compeNo: str, memberId: str, excludeMyself: bool) -> list:
        """
        対象コンペのメッセージを取得する。
        Parameters
        ----------
        beforeTime: int
            指定時間(1970/1/1UTCからのミリ秒)より前のメッセージに制限する。(0以下の場合は制限しない。)
        count: int
            新着順からの件数制限(0以下の場合は制限しない。)
        excludeMyself : bool
            自分(memberId)が送信者のメッセージを除外するか否か
        isParticipant : bool
            参加者か否か
                Falseの場合、コンペ参加者宛のメッセージを除外して検索する。
                (個人宛のものに関しては特に制御しない。)
        """
        destSql = self.ifStr(receptLevel == ReceptLevel.All, lambda: "        OR msg.send_type = 2 #コンペ参加者")
        excludeSql = self.ifStr(excludeMyself, lambda: "    AND msg.member_id <> %(memberId)s #自分を含まない")
        beforeSql = self.ifStr(beforeTime > 0, lambda: "    AND msg.time < %(beforeTime)s")
        limitSql = self.ifStr(count > 0, lambda: "    LIMIT %(count)s")
        sql = """
SELECT msgex.message_id, msgex.send_type, msgex.compe_no, msgex.member_id, msgex.time, msgex.message, stp.stamp_url AS stamp
FROM (
    SELECT msg.*
    FROM {dbSchema}.t_message msg
    WHERE msg.compe_no = %(compeNo)s
    AND msg.is_delete = false
{beforeSql}
    AND (
        msg.send_type = 1 #ギャラリー含む
{destSql}
        OR (
            msg.send_type = 3 #個人宛
            AND (
                msg.dest_member_id = %(memberId)s #自分宛
                OR msg.member_id = %(memberId)s #送信者が自分
            )
        )
    )
{excludeSql}
    ORDER BY msg.time DESC, msg.message_id DESC
{limitSql}
) msgex
LEFT JOIN {dbSchema}.m_stamp stp ON (
    stp.is_delete = false
    AND msgex.stamp_id IS NOT NULL
    AND msgex.stamp_id = stp.stamp_id
)
ORDER BY msgex.time ASC, msgex.message_id ASC
""".replace("{dbSchema}", DB_SCHEMA).replace("{destSql}", destSql).replace("{excludeSql}", excludeSql).replace("{beforeSql}", beforeSql).replace("{limitSql}", limitSql)

        messages: list[MessageData] = list()
        cursor = self.query(sql, { "compeNo": compeNo, "memberId": memberId, "beforeTime": beforeTime, "count": count })
        for row in cursor:
            messages.append(GetMessagesData(
                row["message_id"],
                row["send_type"],
                row["compe_no"],
                row["member_id"],
                row["time"],
                row["message"],
                row["stamp"]
                ))
        return messages

    def save(self, data: SendMessageData):
        sql = """
INSERT INTO {dbSchema}.t_message (
    send_type,
    compe_no,
    dest_member_id,
    member_id,
    time,
    message,
    stamp_id,
    is_delete
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
""".replace("{dbSchema}", DB_SCHEMA)
        param = (data.send_type, data.compe_no, data.dest_member_id, data.member_id, data.time, data.message, data.stamp_id, data.is_delete)
        cur = self.execute(sql, param)
        data.message_id = cur.lastrowid

@dataclasses.dataclass
class StampData:
    stamp_id: int
    stamp_url: str

class StampMstRepository(RepositoryBase):

    def findStamps(self) -> list:
        stamps: list[StampData] = list()
        sql = """
SELECT stp.*
FROM {dbSchema}.m_stamp stp
WHERE stp.is_delete = false
ORDER BY stp.stamp_id ASC;
""".replace("{dbSchema}", DB_SCHEMA)
        cursor = self.query(sql)
        for row in cursor:
            stamps.append(StampData(
                row["stamp_id"],
                row["stamp_url"]
                ))
        return stamps

    def findStamp(self, stampId: int) -> StampData:
        sql = """
SELECT stp.*
FROM {dbSchema}.m_stamp stp
WHERE stp.is_delete = false
AND stp.stamp_id = %(stampId)s
""".replace("{dbSchema}", DB_SCHEMA)
        cursor = self.query(sql, { "stampId": stampId })
        for row in cursor:
            return StampData(
                row["stamp_id"],
                row["stamp_url"]
                )
        return None



