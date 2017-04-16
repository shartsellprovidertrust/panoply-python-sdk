import time
import panoply
from pprint import pprint


KEY = "panoply/2g866xw4oaqt1emi"
SECRET = "MmM0NWNvc2wwYmJ4ZDJ0OS84MmY3MzQ4NC02MDIzLTQyN2QtODdkMS0yY2I0NTAzNDk"\
         "0NDQvMDM3MzM1OTk5NTYyL3VzLWVhc3QtMQ=="


def dumpArgsFor(event_name):
    def dumpArgs(*args):
        print('-----in handler {0}-------'.format(event_name))
        for arg in args:
            print('------arg {}-----'.format(arg))
            pprint(vars(arg))

    return dumpArgs


sdk = panoply.SDK(KEY, SECRET)

sdk.on('send', dumpArgsFor('send'))
sdk.on('flush', dumpArgsFor('flush'))

sdk.write('roi-test', {'hello': 1})

print(sdk.qurl)

time.sleep(5)
