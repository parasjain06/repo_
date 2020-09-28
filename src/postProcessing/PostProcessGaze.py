from src.Notifier.Notifier import notify

#Assuming:- Average time taken to process one frame is 2 seconds
def calculateMin(frameCount):
    return (frameCount*2)/60

def notifyGaze(totalFrames,unAttentiveFrames):
    webexNotify =""
    totalMins = calculateMin(totalFrames)
    unAttentiveMins = calculateMin(unAttentiveFrames)

    attentiveText = "Total duration of presentation %.2f min \n Attentive duration %.2f min" % (totalMins, (totalMins-unAttentiveMins))
    notAttentiveText = "Total duration of presentation %.2f min \n Attentive duration only %.2f mins\nThis is calculated as the duration when you were looking into the screen" \
                       "\nPossible reasons of inattentive  could be : \n1)You are not intrested in the topic\n2)Presenter is not able to grab attention\n3)You have fatigue" % (totalMins, (totalMins -unAttentiveMins))

    avg = 100 - (unAttentiveFrames / totalFrames * 100)
    print("Average is %s" % avg)
    if avg < 60:
        webexNotify = notAttentiveText
        print("Average is less than 60")
        print("unattentive")
    else:
        webexNotify= attentiveText
        print("Average is greater than 60%")
        print("Attentive")

    notify(webexNotify)