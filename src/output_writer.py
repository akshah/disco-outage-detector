from __future__ import print_function
import threading
import os
import traceback
import csv
from contextlib import closing

class outputWriter():
    def __init__(self, resultfilename=None):
        if not resultfilename:
            print('Please give a result filename.')
            exit(0)
        self.lock = threading.RLock()
        self.resultfilename = resultfilename

    def write(self, val,output_format='custom', delimiter='|'):
        self.lock.acquire()
        try:
            if output_format == 'custom':
                with closing(open(self.resultfilename, 'a+')) as csvfile:
                    writer = csv.writer(csvfile, delimiter=delimiter)
                    writer.writerow(val)
            elif output_format == 'fsdb':
                with closing(open(self.resultfilename, 'a+')) as fp:
                    prefixes_seen =  set() # Some probes could be in the same /24, accounting for overlaps
                    probeInfoList = eval(str(val[6]))
                    for pVal in probeInfoList:
                        prefix_block = pVal['slash24']
                        if prefix_block not in prefixes_seen:
                            print(val[2], val[3], prefix_block,val[1],sep='\t',file=fp)
                            prefixes_seen.add(prefix_block)
        except:
            traceback.print_exc()
        finally:
            self.lock.release()

    def updateProbeInfo(self, infoDictList):
        # "probeInfo" : [ { "start" : 1500897808, "probeID" : 3264, "end" : 1500900061, "state" : 20 } ]
        newInfoDict = {}
        for inDict in infoDictList:
            for pDict in inDict:
                if pDict['probeID'] not in newInfoDict.keys():
                    if pDict['end'] != -1:
                        newInfoDict[pDict['probeID']] = {'start': pDict['start'], 'end': pDict['end'], \
                                                         'state': pDict['state'], 'probeID': pDict['probeID'], \
                                                         'prefix_v4': pDict['prefix_v4'],
                                                         'address_v4': pDict['address_v4']}
                else:
                    # Pick min start
                    newInfoDict[pDict['probeID']]['start'] = min(newInfoDict[pDict['probeID']]['start'], pDict['start'])
                    # Pick max end
                    newInfoDict[pDict['probeID']]['end'] = max(newInfoDict[pDict['probeID']]['end'], pDict['end'])
                    # Pick max state
                    newInfoDict[pDict['probeID']]['state'] = max(newInfoDict[pDict['probeID']]['state'], pDict['state'])
        retList = [p for p in newInfoDict.values()]
        return retList