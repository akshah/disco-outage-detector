import configparser
from contextlib import closing

class outputWriter():

    def __init__(self,resultfilename=None):
        if not resultfilename:
            print('Please give a result filename.')
            exit(0)
        self.lock = threading.RLock()
        self.resultfilename = resultfilename
        if os.path.exists(self.resultfilename):
            os.remove(self.resultfilename)
        self.dbname=None
        # Read MongoDB config
        configfile = 'conf/mongodb.conf'
        config = configparser.ConfigParser()
        try:
            config.sections()
            config.read(configfile)
        except:
            logging.error('Missing config: ' + configfile)
            exit(1)

        try:
            self.dbname = config['MONGODB']['dbname']
        except:
            print('Error in reading mongodb.conf. Check parameters.')
            exit(1)

        #self.mongodb = mongoClient(DBNAME)

    def write(self,val,delimiter="|"):
        self.lock.acquire()
        try:
            with closing(open(self.resultfilename, 'a+')) as csvfile:
                writer = csv.writer(csvfile, delimiter=delimiter)
                writer.writerow(val)
        except:
            traceback.print_exc()
        finally:
            self.lock.release()

    def toMongoDB(self,val):
        mongodb = mongoClient(self.dbname)
        (id, startMedian, endMedian, durationMedian, numProbesInUnit, probeIds)=val
        #results={}
        streamName=self.resultfilename.split('/')[1].split('.')[0].split('_')[2]#Gives the stream name
        streamType=None
        try:
            asnum=int(streamName)
            streamType='asn'
        except:
            if '-' in streamName:
                streamType = 'geo'
            else:
                streamType = 'country'

        # Keep track of all conf settings
        confParams={'probeInfoDataYear':dataYear,'burstLevelThreshold':BURST_THRESHOLD,\
                    'minimumSignalLength':SIGNAL_LENGTH,'minimumProbesInUnit':MIN_PROBES,\
                    'probeClusterDistanceThreshold':probeClusterDistanceThreshold}
        insertTime = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds())
        results={'streamName':streamName,'streamType':streamType,'start':startMedian,'end':endMedian,\
                 'duration':durationMedian,'numberOfProbesInUnit':numProbesInUnit,'probeInfo':probeIds, \
                 'confParams':confParams,'insertTime':insertTime}
        collectionName='streamResults'

        incFlag = False
        if results['duration'] == -1:
            incFlag = True
        sys.stdout.flush()
        #return
        # Check if this event has an entry
        entries = mongodb.db[collectionName].find({'streamName':streamName,'duration':-1})
        if entries.count() > 0:
            if not incFlag:
                entry = entries[0]
                print('---------')
                print('Updated '+str(entry["_id"]))
                print(results)
                print('---------')
                try:
                    mongodb.db[collectionName].update({"_id": entry["_id"]}, {'$set':{"end": endMedian, "duration":durationMedian ,\
                                                                          'probeInfo':probeIds,'insertTime':insertTime}})

                except:
                    traceback.print_exc()
        else:
            mongodb.insertLiveResults(collectionName,results)
            if incFlag:
                print('---------')
                entries = mongodb.db[collectionName].find({'start': startMedian, 'streamName': streamName, 'end': -1})
                print('Inserted overlapping outage: ' + str(entries[0]["_id"]))
                print(results)
                print('---------')

    def pushProbeInfoToDB(self,probeInfo):
        mongodb = mongoClient(self.dbname)
        collectionName='streamInfo'
        results=mongodb.findInCollection(collectionName,'year',dataYear)
        if len(results) == 0:
            allASes=probeInfo.asnToProbeIDDict.keys()
            allPIDs=probeInfo.probeIDToASNDict.keys()
            allCountries=probeInfo.countryToProbeIDDict.keys()
            #streamInfoData={'year':dataYear,'streamsMonitored':{'ases':allASes,'countries':allCountries,'probeIDs':allPIDs}}
            simpleASN2PID={}
            for k,v in probeInfo.asnToProbeIDDict.items():
                simpleASN2PID[str(k)]=list(set(v))
            simpleCountry2PID = {}
            for k,v in probeInfo.countryToProbeIDDict.items():
                simpleCountry2PID[k]=list(set(v))
            streamInfoData = {'year': dataYear,
                              'streamsMonitored': {'ases': simpleASN2PID, \
                                                   'countries': simpleCountry2PID}}
            mongodb.insertLiveResults(collectionName, streamInfoData)

    def updateCurrentTimeInDB(self,ts):
        mongodb = mongoClient(self.dbname)
        mongodb.updateLastSeenTime(ts)

