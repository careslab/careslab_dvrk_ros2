import logging
from typing import Mapping
# from urllib import request
from flask import Flask, render_template, request, jsonify
from flask_ask import Ask, statement, question, session
import threading

import rospy
from std_msgs.msg import Empty
from std_msgs.msg import Bool
from std_msgs.msg import String
from std_msgs.msg import Float32
from std_msgs.msg import Int16

import json


app = Flask(__name__)
ask = Ask(app, "/")

#logging.getLogger("flask_ask").setLevel(logging.DEBUG)

# ROS node, publisher, and parameter.
# The node is started in a separate thread to avoid conflicts with Flask.
# The parameter *disable_signals* must be set if node is not initialized
# in the main thread.

threading.Thread(target=lambda: rospy.init_node('dvrk_voice', disable_signals=True, anonymous=True)).start()

run_pub = rospy.Publisher('/assistant/autocamera/run', Bool, queue_size=1, latch=True)
track_pub = rospy.Publisher('/assistant/autocamera/track', String, queue_size=1, latch=True)
keep_pub = rospy.Publisher('/assistant/autocamera/keep', String, queue_size=1, latch=True)
findtools_pub = rospy.Publisher('/assistant/autocamera/find_tools', Empty, queue_size=1, latch=True)
innerZoom_pub = rospy.Publisher('/assistant/autocamera/inner_zoom_value', Float32, queue_size=1, latch=True)
outerZoom_pub = rospy.Publisher('/assistant/autocamera/outer_zoom_value', Float32, queue_size=1, latch=True)
saveEcm_pub = rospy.Publisher('/assistant/save_ecm_position', Int16, queue_size=1)
gotoEcm_pub = rospy.Publisher('/assistant/goto_ecm_position', Int16, queue_size=1)
voiceCommand_pub = rospy.Publisher('/voice_command', String, queue_size=1)
ecm_saved_positions=[]


@ask.launch
def new_game():

    welcome_msg = render_template('welcome')

    return question(welcome_msg)


@ask.intent('RunAutoCameraIntent')
def autocamera_run(run):

    #Capture the json sent from Alexa servers and parse to pull out the value instead of the synonym
    data = request.get_json()
    run = str(data['request']['intent']['slots']['run']['slotValue']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']).lower()  # I'm NEVER doing this again!
    print("RunAutoCameraIntent: " + str(run))

    #publish to run topic 
    if(run == "start"):
        run_pub.publish(True)
        voiceCommand_pub.publish("Da Vinci Start")

    elif(run == "stop"):
        run_pub.publish(False)
        voiceCommand_pub.publish("Da Vinci Stop")

    #return what alexa would say when done
    say = 'Done'
    return statement(say)

@ask.intent("TrackToolIntent")
def autocamera_track(tool):
    
    #Capture the json sent from Alexa servers and parse to pull out the value instead of the synonym
    data = request.get_json()
    #print(data, '\n')      #Optionally print the json
    tool = str(data['request']['intent']['slots']['tool']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']).lower()  # I'm NEVER doing this again!
    print("TrackToolIntent: " + str(tool))

    #publish to track topic 
    if(tool == "right"):
        track_pub.publish("right")
        voiceCommand_pub.publish("Da Vinci track right")

    elif(tool == "left"):
        track_pub.publish("left")
        voiceCommand_pub.publish("Da Vinci track left")

    elif(tool == "middle"):
        track_pub.publish("middle")
        voiceCommand_pub.publish("Da Vinci track middle")

    say = 'Done'
    return statement(say)

@ask.intent("KeepToolPositionIntent")
def autocamera_keep(tool):
    
    #Capture the json sent from Alexa servers and parse to pull out the value instead of the synonym
    data = request.get_json()
    #print(data, '\n')      #Optionally print the json
    tool = str(data['request']['intent']['slots']['tool']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']).lower()  # I'm NEVER doing this again!
    print("KeepToolPositionIntent: " + str(tool))

    #publish to track topic 
    if(tool == "right"):
        keep_pub.publish("right")
        voiceCommand_pub.publish("Da Vinci keep right")

    elif(tool == "left"):
        keep_pub.publish("left")
        voiceCommand_pub.publish("Da Vinci keep left")

    elif(tool == "middle"):
        keep_pub.publish("middle")
        voiceCommand_pub.publish("Da Vinci keep middle")

    say = 'Done'
    return statement(say)

@ask.intent("FindMyToolsIntent")
def autocamera_findtools():

    print("FindMyToolsIntent: ")

    #publish to find tools topic
    findtools_pub.publish()
    voiceCommand_pub.publish("Da Vinci find my tools")

    say = 'Done'
    return statement(say)

@ask.intent("InnerOuterZoomLevelIntent", convert={'value': float})
def autocamera_innerOuterZoom(zone, value):
    
    print("InnerOuterZoomLevelIntent: " + str(zone) + ":" + str(value))
    print(isinstance(value, float))

    #Check for value data types and size
    if(not isinstance(value, float)):
        say = 'Could not register number'
        return statement(say)

    #publish to inner outer zoom topic 
    if(zone == "inner"):
        innerZoom_pub.publish(value)

    elif(zone == "outer"):
        outerZoom_pub.publish(value)

    else:
        say = 'Unknown zone'
        return statement(say)

    say = 'Done'
    return statement(say)

@ask.intent("SaveEcmPositionAsIntent", convert={'name': int})
def davinci_saveEcm(name):
    
    print("SaveEcmPositionAsIntent: " + str(name))

    if(not isinstance(name, int)):
        say = 'Could not register number'
        return statement(say)

    ecm_saved_positions.append(name)
    print(ecm_saved_positions)

    #publish to save topic 
    saveEcm_pub.publish(name)

    say = 'Done'
    return statement(say)

@ask.intent("GotoEcmPositionAsIntent", convert={'name': int})
def davinci_gotoEcm(name):
    
    print("GotoEcmPositionAsIntent: " + str(name))

    #Check for value data types and size
    if(not isinstance(name, int)):
        say = 'Could not register number'
        return statement(say)

    #Check if the value has already been saved
    if(not name in ecm_saved_positions):
        say = 'not found in saved positions'
        return statement(say)

    #publish to go to topic 
    gotoEcm_pub.publish(name)

    say = 'Done'
    return statement(say)


if __name__ == '__main__':
    app.run(debug=True)