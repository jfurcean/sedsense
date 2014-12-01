import time, httplib, urllib, serial, time, wx
from threading import *




# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()

def checkSitting(ser,MAX_DISTANCE):

	listen=True
	while listen:

		read_val= ser.readline()
		if(read_val):

			read_val = read_val.strip()
			val_list = read_val.split()
			distance = val_list[1].strip('cm')
			print distance
			listen = False

			if int(distance) < MAX_DISTANCE:
				return True
			else:
				return False



def sendNotification(sittingTime):

	sittingTimeStr = str(sittingTime/60)

	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
	  urllib.urlencode({
	    "token": "aSMvPprPX7v4aq1z3tDoiAnWmE6H7G",
	    "user": "Mgi64WImrWUncCaV5w3qfu6Os1Crb4",
	    "message": "You have been sitting for "+sittingTimeStr+" minutes. You should move around!",
	    "title": "Sedentary",
	  }), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()





# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data



# Thread class that executes processing
class WorkerThread(Thread):

    """Worker Thread Class."""
    def __init__(self, notify_window):
        
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0

        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()



    def run(self):

        """Run Worker Thread."""

        ser = serial.Serial('/dev/tty.HC-06-DevB', 9600, timeout=1)
        ser.close()

        serIsOpen = False
        while not serIsOpen:
            try:
                ser.open()
                serIsOpen=True
            except:
                serIsOpen=False

        MAX_SIT_TIME = int(self._notify_window.maxSitTime.GetValue())
        WAIT_TIME = int(self._notify_window.waitTime.GetValue())
        MIN_ACTIVE_TIME = int(self._notify_window.minActiveTime.GetValue())
        MIN_NOTIFICATION_TIME = int(self._notify_window.minNotificationTime.GetValue())
        MAX_DISTANCE = int(self._notify_window.maxDistance.GetValue())

        numberNotifications = 0
        notifcationTime = 0
        sittingTime = 0
        activeTime = 0

        totalSitTime = 0
        totalActiveTime = 0

        countNoteTime = False

        sitting = checkSitting(ser, MAX_DISTANCE)

        while(True):

          if self._want_abort:
            totalActiveTime += activeTime
            totalSitTime += sittingTime



            print "Sitting Time: ",totalSitTime
            print "Active Time", totalActiveTime 

            sedFile = open("sedentary.txt","a")
            todayDate = time.strftime("%m/%d/%Y")
            outputStr = todayDate +"\t"+str(totalSitTime)+"\t"+str(totalActiveTime)+"\n"
            sedFile.write(outputStr)
            sedFile.close()

            wx.PostEvent(self._notify_window, ResultEvent(None))
            ser.close()
            return

          start_time = time.time()	

          if(checkSitting(ser, MAX_DISTANCE)):
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

          print "SittingTime: ",sittingTime
          print "MAX_SIT_TIME", MAX_SIT_TIME
          print "NumberNotifications",numberNotifications
          time.sleep(WAIT_TIME)

          if activeTime >= MIN_ACTIVE_TIME:
            totalActiveTime += activeTime
            totalSitTime += sittingTime

            sittingTime = 0
            activeTime = 0
            numberNotifications = 0
            notifcationTime = 0

        ser.close()

        if ser.IsOpen():
          ser.close()

        wx.PostEvent(self._notify_window, ResultEvent(10))



    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1



# GUI Frame class that spins off the worker thread

class MainFrame(wx.Frame):

    """Class MainFrame."""
    def __init__(self, parent, id):

        """Create the MainFrame."""
        #wx.Frame.__init__(self, parent, id, 'Sedentary')
        wx.Frame.__init__(self, parent, id, 'Sedentary',
          pos=(300, 180), size=(250, 250))

        self.maxSitTime = wx.TextCtrl(self, id=-1, pos=(150, 10), size=(100, 28))
        self.maxSitTime.SetValue('50')
        self.maxSitTimeLabel = wx.StaticText(self, -1, '', pos=(10,14))
        self.maxSitTimeLabel.SetLabel('Max Sit Time: ')

        self.minActiveTime = wx.TextCtrl(self, id=-1, pos=(150, 40), size=(100, 28))
        self.minActiveTime.SetValue('10')
        self.minActiveTimeLabel = wx.StaticText(self, -1, '', pos=(10,44))
        self.minActiveTimeLabel.SetLabel('Min Active Time: ')

        self.waitTime = wx.TextCtrl(self, id=-1, pos=(150, 70), size=(100, 28))
        self.waitTime.SetValue('20')
        self.waitTimeLabel = wx.StaticText(self, -1, '', pos=(10,74))
        self.waitTimeLabel.SetLabel('Wait Time: ')

        self.minNotificationTime = wx.TextCtrl(self, id=-1, pos=(150, 100), size=(100, 28))
        self.minNotificationTime.SetValue('30')
        self.NotificationTimeLabel = wx.StaticText(self, -1, '', pos=(10,104))
        self.NotificationTimeLabel.SetLabel('Notification Time: ')

        self.maxDistance = wx.TextCtrl(self, id=-1, pos=(150, 130), size=(100, 28))
        self.maxDistance.SetValue('20')
        self.maxDistanceLabel = wx.StaticText(self, -1, '', pos=(10,134))
        self.maxDistanceLabel.SetLabel('Max Distance in cm:')

        self.startButton = wx.Button(self, ID_START, 'Start', pos=(150,160))
        self.stopButton = wx.Button(self, ID_STOP, 'Stop', pos=(150,190))
        self.stopButton.Disable()

        self.status = wx.StaticText(self, -1, '', pos=(10,210))

        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnStop, id=ID_STOP)



        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None

    def OnStart(self, event):

        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        if not self.worker:

            self.startButton.Disable()
            self.stopButton.Enable()
            self.status.SetLabel('Tracking Sitting')
            self.worker = WorkerThread(self)



    def OnStop(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        if self.worker:
            self.stopButton.Disable()
            self.startButton.Enable()
            self.status.SetLabel('Stopping Tracking')
            self.worker.abort()


    def OnResult(self, event):
        self.status.SetLabel('Tracking Complete')
        self.worker = None



class MainApp(wx.App):
    """Class Main App."""

    def OnInit(self):
        """Init Main App."""
        self.frame = MainFrame(None, -1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True



if __name__ == '__main__':
    app = MainApp(0)
    app.MainLoop()
