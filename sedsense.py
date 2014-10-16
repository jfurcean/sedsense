import time, httplib, urllib

def checkSitting():

	#TODO:
	
	#READ FROM BLUETOOTH 
	
	#Check if sitting or not return result
	
	return true

def sendNotification(sittingTime):
	sittingTimeStr = str(sittingTime/60)
	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
	  urllib.urlencode({
	    "token": "TOKEN",
	    "user": "USERSTRING",
	    "message": "You have been sitting for "+sittingTimeStr+" minutes. You should move around!",
	    "title": "Sedentary",
	  }), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()

def main():

	MAX_SIT_TIME = 50*60
	WAIT_TIME =60
	MIN_ACTIVE_TIME = 10*60
	MIN_NOTIFICATION_TIME = 10*60

	numberNotifications = 0
	notifcationTime = 0
	sittingTime = 0
	activeTime = 0

	totalSitTime = 0
	totalActiveTime = 0

	countNoteTime = False

	sitting = checkStting()


	while(true):
		start_time = time.time()	
		time.sleep(WAIT_TIME)

		if(checkSitting()):
			sittingTime += WAIT_TIME
		
		else:
			activeTime += WAIT_TIME

		if countNoteTime:
			notifcationTime += WAIT_TIME
			if notifcationTime >= MIN_NOTIFICATION_TIME:
				sendNotification(sittingTime)
				notifcationTime = 0

		if ((sittingTime)/(MAX_SIT_TIME*1.0)) >= (numberNotifications+1):
			sendNotification(sittingTime)
			numberNotifications+=1
			countNoteTime = True
	
		else:
			sendNotification()
			numberNotifications += 1

		if activeTime >= MIN_ACTIVE_TIME:
			totalActiveTime += activeTime
			totalSitTime += sittingTime

			sittingTime = 0
			activeTime = 0
			numberNotifications = 0
			notifcationTime = 0

main()

