import time
import panoply
from pprint import pprint
from datetime import datetime
import json

KEY = "panoply/2g866xw4oaqt1emi"
SECRET = "MmM0NWNvc2wwYmJ4ZDJ0OS84MmY3MzQ4NC02MDIzLTQyN2QtODdkMS0yY2I0NTAzNDk"\
         "0NDQvMDM3MzM1OTk5NTYyL3VzLWVhc3QtMQ=="


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


def dumpArgsFor(event_name):
    def dumpArgs(*args):
        print('-----in handler {0}-------'.format(event_name))
        for arg in args:
            print('------arg {}-----'.format(arg))
            pprint(vars(arg))

    return dumpArgs


encoder = JsonEncoder()
sdk = panoply.SDK(KEY, SECRET, jsonEncoder=encoder)

sdk.on('send', dumpArgsFor('send'))
sdk.on('flush', dumpArgsFor('flush'))

sdk.write('roi-test', {'hello': 1})
sdk.write('roi-test', {'hello': 1, 'a-date': datetime.now()})

print(sdk.qurl)

time.sleep(5)
