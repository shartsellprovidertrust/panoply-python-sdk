import base64
import json
import time
import urllib
import urllib.request
import threading
import queue
from copy import copy
from panoply import events
from panoply import VERSION, PKGNAME, MAXSIZE, FLUSH_TIMEOUT


class SDK (events.Emitter):
    account = None
    apikey = None
    apisecret = None

    # duck-typed logger object that exposes a `.log(lvl, msg)` method
    logger = None

    # internal buffer queue
    _buffer = None

    def __init__(self, apikey, apisecret):
        super(SDK, self).__init__()

        self.apikey = apikey
        self.apisecret = apisecret

        # decompose the api key and secret
        # api-key: ACCOUNT/RAND1
        # api-secret: BASE64( RAND2/UUID/AWSACCOUNT/REGION )

        decoded = base64.b64decode(apisecret).decode('utf-8').split("/")
        rand = decoded[0]
        awsaccount = decoded[2]
        region = decoded[3]
        account = apikey.split("/")[0]

        # construct the queue url
        # queue: sdk-ACCOUNT-RAND2
        self.qurl = "https://sqs.%s.amazonaws.com/%s/sdk-%s-%s" % (
            region,
            awsaccount,
            account,
            rand
        )

        self._buffer = queue.Queue()
        thread = threading.Thread(target=self._sendloop)
        thread.daemon = True
        thread.start()

    def write(self, table, data):
        # add the new data entry to the internal buffer
        data = copy(data)
        data["__table"] = table
        data = json.dumps(data).encode("utf-8")
        data = urllib.parse.quote(data)
        self._buffer.put(data + "\n")

    # flush the buffer to SQS
    def _send(self, body):
        body = [
            "Action=SendMessage",
            "MessageBody=" + body,
            "MessageAttribute.1.Name=key",
            "MessageAttribute.1.Value.DataType=String",
            "MessageAttribute.1.Value.StringValue=" + self.apikey,
            "MessageAttribute.2.Name=secret",
            "MessageAttribute.2.Value.DataType=String",
            "MessageAttribute.2.Value.StringValue=" + self.apisecret,
            "MessageAttribute.3.Name=sdk",
            "MessageAttribute.3.Value.DataType=String",
            "MessageAttribute.3.Value.StringValue=" + PKGNAME + "-" + VERSION,
        ]

        body = "&".join(body)

        headers = {
            "Content-Length": len(body),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        print("FLUSHING DATA")

        body_bytes = body.encode('utf-8')
        req = urllib.request.Request(self.qurl, body_bytes, headers)
        self.fire("send", req)
        try:
            res = urllib.request.urlopen(req)
        except Exception as err:
            self.fire("error", err)
            return

        self.fire("flush", req, res)

    def _sendloop(self):
        buf = self._buffer
        body = ""
        lastsend = time.time()
        while True:
            data = None
            try:
                data = buf.get(True, FLUSH_TIMEOUT)  # blocking
                body += data + "\n"
            except queue.Empty:
                pass

            length = len(body)
            elapsed = time.time() - lastsend

            if length is 0:
                # reset the time when there's nothing to send
                lastsend = time.time()
            elif length > MAXSIZE or elapsed > FLUSH_TIMEOUT:
                lastsend = time.time()
                self._send(body)
                body = ""

            if data:
                buf.task_done()
