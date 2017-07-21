def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    try:
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        km = 6367 * c
        return km
    except:
        print(lon1, lat1, lon2, lat2)
        traceback.print_exc()

def getTimeStampsForBurstyProbes(burstyProbes,burstDict,burstEventDict):
    burstyProbeInfoDict={}
    for event in dataList:
        if event["event"] == "disconnect":
            eventTime=float(event['timestamp'])
            pid=event["prb_id"]
            if pid in burstyProbes:
                for state,timeDictList in burstDict.items():
                    if state >= BURST_THRESHOLD:
                        eventID=getEventID(burstEventDict,event)
                        for timeDict in timeDictList:
                            if eventID and eventTime>=timeDict['start'] and eventTime<=timeDict['end']:
                                if pid not in burstyProbeInfoDict.keys():
                                    burstyProbeInfoDict[pid]={}
                                if state not in burstyProbeInfoDict[pid].keys():
                                    burstyProbeInfoDict[pid][state]={}
                                if eventID not in burstyProbeInfoDict[pid][state].keys():
                                    burstyProbeInfoDict[pid][state][eventID]=[]
                                burstyProbeInfoDict[pid][state][eventID].append(event["timestamp"])

    #pp.pprint(burstyProbeInfoDict)
    return burstyProbeInfoDict

def correlateWithConnectionEvents(burstyProbeInfoDictIn):
    # Extremely unoptimized way to do this. Need to rewrite this function.

    #pp.pprint(burstyProbeInfoDict)
    burstyProbeInfoDict=burstyProbeInfoDictIn
    allInBurstIDs=[]
    burstyProbeDurations={}
    for event in dataList:
        if event["event"] == "connect":
            pid=event["prb_id"]
            if pid in burstyProbeInfoDict.keys():
                for state in burstyProbeInfoDict[pid].keys():
                    for burstID,tmpSList in burstyProbeInfoDict[pid][state].items():
                        allInBurstIDs.append(burstID)
                        for tmpS in tmpSList:
                            eventTS=float(event["timestamp"])
                            if eventTS >tmpS:
                                burstyProbeInfoDict[pid][state][burstID].remove(tmpS)
                                duration=eventTS-tmpS
                                if burstID not in burstyProbeDurations.keys():
                                    burstyProbeDurations[burstID]={}
                                if pid not in burstyProbeDurations[burstID].keys():
                                    burstyProbeDurations[burstID][pid]={}
                                if state not in burstyProbeDurations[burstID][pid].keys():
                                    burstyProbeDurations[burstID][pid][state]=[]
                                burstyProbeDurations[burstID][pid][state].append({"disconnect":tmpS,"connect":eventTS,"duration":duration})
    # Remove cases where only less than half probes connected
    cleanBurstyProbeDurations={}
    ongoingBurstIDs=[]
    for bid in burstyProbeDurations.keys():
        lenProbeConnVal=len(burstyProbeDurations[bid])
        if lenProbeConnVal >= float(len(burstyProbeInfoDict.keys()))/2:
            cleanBurstyProbeDurations[bid]=burstyProbeDurations[bid]

    burstyProbeDurationsOngoing={}
    for pid in burstyProbeInfoDict.keys():
        for state in burstyProbeInfoDict[pid].keys():
            for burstID, tmpSList in burstyProbeInfoDict[pid][state].items():
                if burstID in cleanBurstyProbeDurations.keys():
                    continue
                for tmpS in tmpSList:
                    if burstID not in burstyProbeDurationsOngoing.keys():
                        burstyProbeDurationsOngoing[burstID] = {}
                    if pid not in burstyProbeDurationsOngoing[burstID].keys():
                        burstyProbeDurationsOngoing[burstID][pid] = {}
                    if state not in burstyProbeDurationsOngoing[burstID][pid].keys():
                        burstyProbeDurationsOngoing[burstID][pid][state] = []
                        burstyProbeDurationsOngoing[burstID][pid][state].append(
                        {"disconnect": tmpS, "connect": -1, "duration": -1})

    return burstyProbeDurationsOngoing,cleanBurstyProbeDurations

def getPerEventStats(burstyProbeDurations,burstyProbeDurationsOngoing,numProbesInUnit,output):
    burstEventInfo=[]
    for id,inDict in burstyProbeDurations.items():
        startTimes=[]
        endTimes=[]
        durations=[]
        probeIds=[]
        for pid,inDict2 in inDict.items():
            maxState=max(inDict2.keys())
            for infoDict in inDict2[maxState]:
                startTimes.append(infoDict["disconnect"])
                endTimes.append(infoDict["connect"])
                durations.append(infoDict["duration"])
                probeIds.append({'probeID':pid,'state':maxState,"start":infoDict["disconnect"],"end":infoDict["connect"]})
        startMedian=np.median(np.array(startTimes))
        endMedian=np.median(np.array(endTimes))
        durationMedian=np.median(np.array(durations))
        burstEventInfo.append([id,startMedian,endMedian,durationMedian,numProbesInUnit,probeIds])
        output.write([id,startMedian,endMedian,durationMedian,numProbesInUnit,probeIds])
        output.toMongoDB([id, startMedian, endMedian, durationMedian, numProbesInUnit, probeIds])


    for id,inDict in burstyProbeDurationsOngoing.items():
        startTimes=[]
        probeIds=[]
        for pid,inDict2 in inDict.items():
            maxState=max(inDict2.keys())
            for infoDict in inDict2[maxState]:
                startTimes.append(infoDict["disconnect"])
                probeIds.append({'probeID':pid,'state':maxState,"start":infoDict["disconnect"],"end":-1})
        startMedian=np.median(np.array(startTimes))
        burstEventInfo.append([id,startMedian,-1,-1,numProbesInUnit,probeIds])
        #output.write([id,startMedian,endMedian,durationMedian,numProbesInUnit,probeIds])
        output.toMongoDB([id, startMedian, -1, -1, numProbesInUnit, probeIds])

    return burstEventInfo
