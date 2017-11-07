Detecting Burst of Internet Outages using RIPE Atlas

Steps:
- Install pybursts (modified version: http://github.com/romain-fontugne/pybursts)
- Setup conf/disco.conf
- Make sure you have probe information in bin/probeArchiveInfo for the year you setup in disco.conf
[Use probeArchiveDownloader.sh to get probe info data]
- Launch Disco: python2.7 src/disco.py &
[Produces flat result files in results/ dir and logs information in logs/, create these dirs]