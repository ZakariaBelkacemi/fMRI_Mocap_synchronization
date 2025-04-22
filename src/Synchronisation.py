#!/usr/bin/python3

"""
    Streaming 6-DOF data from QTM forever
    (start QTM first, Capture->Continuous Capture)
"""

import asyncio
import qtm
import socket
import keyboard
import time
import os
import datetime
from datetime import datetime
import sys

# import numpy as np

sendmotion = 0

measuredCadency = 0

musicVar = 0

xcount=0
xAxis = []
yAxis = []

xcountSpeed = 0
xSpeed = []
ySpeed = []

IP_server = '127.0.0.1' # IP of pc launching QTM
HOST_UDP = '127.0.0.1' #192.168.131.120'#'192.168.131.19' #IP of pc/server receiving UDP packets
PORT_UDP = 4460

wanted_marker = 'MetatarsalHead1'
laterality = 'R'
markerID = 7 #qtmindex -1 because python begin with 0
axis_name = 'z'

patientID = str(input('patient ID : '))
taskID = int(input('Task ID : '))
sessID = int(input('Session : '))

taskNames = ['marche_seule','marche_musique','marche_musique_synchrone', 'musique_seule']
taskName = taskNames[taskID-1]

musicDatatype = 1
gotaskDatatype = 1
synchroDatatype = 1

task1sent = 0

cd = os.getcwd()
print(cd)

if time.localtime()[1]>9:
    exam_date = str(time.localtime()[0]) + '-' + str(time.localtime()[1]) + '-' + str(time.localtime()[2])
else:
    exam_date = str(time.localtime()[0]) + '-0' + str(time.localtime()[1]) + '-' + str(time.localtime()[2])

if time.localtime()[1]>9:
    file_date = str(time.localtime()[0]) + str(time.localtime()[1]) + str(time.localtime()[2])
else:
    file_date = str(time.localtime()[0]) + '0' + str(time.localtime()[1]) + str(time.localtime()[2])

def onset_simulation(block_duration, block_repetition):
    #This function create a vector representing the block
    #x axis is the time in number of volumes
    #y axis is the instruction : 1 for action and 0 for rest
    #block_repetition is the number of repetition of block
    #considering a block = action+rest
    onsets = []
    for ionsets in range(block_duration*block_repetition*2):
        onsets.append(1)

    for i in range(0,5,2):
        lim_inf = (round(block_duration)*i)
        lim_sup = (round(block_duration)*(i+1))
        for ionsetsrest in range(lim_inf,lim_sup):
            onsets[ionsetsrest] = 0 
    
    rest = []
    for irest in range(len(onsets)):
        if onsets[irest]==0:
            rest.append(irest)
    
    exam_len = block_duration * block_repetition * 2
    
    #onsets : vector representing the block (0 = rest, 1 = action)
    #rest : index of onsets when y = 0, volumes during which instruction is rest
    #exam_len : number total of volumes
    return onsets, rest, exam_len

def publisher_udp_main():

    server_address_udp = (HOST_UDP, PORT_UDP)
    print(HOST_UDP, PORT_UDP)
    time.sleep(1)
    # Create a UDP socket
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    return sock_udp, server_address_udp

async def MRIsynchro(connection, sock_udp, server_address_udp, volume_count):
# async def MRIsynchro(connection, exam_info, server_address_udp, volume_count):
    global motionMsgToSave
    global variation
    global sendmotion
    global task1signalSent
    global music
    
    variation = 1
    volume_occurence_list = []
    onsets_vector, rest_list, exam_len = onset_simulation(38,3)
    
    #vector which will be saved
    MusicMsgToSave = ''
    SynchroMsgToSave = ''
    # while True:
        # await asyncio.sleep(0)
        # if keyboard.is_pressed('²'):
        #indent
    while True:
        #await sleep necessary for the function
        await asyncio.sleep(0)
        if keyboard.is_pressed('s'): 
            # print('S key detected !**********************************************************************')
            now = datetime.now()
            actualTime = now.strftime("%H%M%S.%f")
            SynchroMsgToSave = SynchroMsgToSave + str(actualTime) + '\n'
            # volume_occurence_list.append(str(actualTime))
            
            task1begin = 189 #5
            task1end = 226 #15
            if taskID == 1:
                if volume_count == task1begin :
                    sendMotion = 1
                    goMsg = "1;goirmf;1;" + str(batchID)
                    bytesGoMsg = bytes(goMsg,'utf8')
                    sentGo = sock_udp.sendto(bytesGoMsg, server_address_udp)
                    print('goTask for task ', str(taskID),' sent')
                    
                    startMsg = "100;startmotion;" + patientID + ';' + str(exam_date) + ';' + str(taskID) + ';' + str(batchID)
                    bytesStartMsg = bytes(startMsg,'utf8')
                    # sentStart = sock_udp.sendto(bytesStartMsg, server_address_udp)
                    print('startmotion for task 1 sent')
                
                if task1end > volume_count > task1begin :
                    sendmotion = 2
                    
                elif volume_count > task1end :
                    sendmotion = 3
            
            await asyncio.sleep(0.2)
            
            if taskID != 1:
                if volume_count-1 in rest_list: #instruction_rest
                #-1 car le vecteur "rest_list" considère un début à 0
                    music = "musicoff"
                    musicVar = 0
                else: #instruction_action
                    music = "musicon" 
                    musicVar = 1
            
            # if task == 1:
            #     music = 0
            
            #sending udp packet
            normTimestampSync = round(time.time()*1000)        
            
            if volume_count == 1 :
                
                async with qtm.TakeControl(connection, "password"):
                    await connection.set_qtm_event("MRIbeginS1")
                
                if taskID == 2 or taskID == 3:
                    goMsg = "1;goirmf;1;" + str(batchID)
                    bytesGoMsg = bytes(goMsg,'utf8')
                    sentGo = sock_udp.sendto(bytesGoMsg, server_address_udp)
                    print('goTask for task ', str(taskID),' sent')
                    
                    startMsg = "100;startmotion;" + patientID + ';' + str(exam_date) + ';' + str(taskID) + ';' + str(batchID)
                    bytesStartMsg = bytes(startMsg,'utf8')
                    # sentStart = sock_udp.sendto(bytesStartMsg, server_address_udp)
                    print('startmotion for task ', str(taskID),' sent')                    
                    
                if taskID == 4:
                    next4Msg = "1;next4;1;" + str(batchID)
                    bytesNext4Msg = bytes(next4Msg,'utf8')
                    sentGo = sock_udp.sendto(bytesNext4Msg, server_address_udp)
                    print('goTask for task 4 sent')
            
            volume_count += 1
            print(' S key detected*************************************************************')
            
            if taskID != 1:                
                if variation != musicVar:
                    musicMsg = "1;" + music + ";1;" + str(batchID)
                    bytesMusicMsg = bytes(musicMsg,'utf8')
                    # MusicMsgToSave = MusicMsgToSave + '\n' + musicMsg
                    sentMusic = sock_udp.sendto(bytesMusicMsg, server_address_udp)
                    print('music ' + str(music) + ' sent')
                    variation = musicVar
            # else:
            #     if sendmotion == 1 :
            #         sentTask1 = sock_udp.sendto(bytesMusicMsg, server_address_udp)
            #         sendmotion == 2
            
            # print(tic - time.time())
            
            # print('UDP sent ' + str(tic-time.time()) +' %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            # await asyncio.sleep(0.3)
            
            if volume_count == 229:
                if taskID == 2 or taskID == 3 :
                    music = "musicoff"
                    musicMsg = "1;" + music + ";1;" + str(batchID)
                    bytesMusicMsg = bytes(musicMsg,'utf8')
                    # MusicMsgToSave = MusicMsgToSave + '\n' + musicMsg
                    sentMusic = sock_udp.sendto(bytesMusicMsg, server_address_udp)
                    print('music ' + str(music) + ' sent')
                
        if keyboard.is_pressed('*'):
            async with qtm.TakeControl(connection, "password"):
                await connection.stop()
                time.sleep(3)
                BeatParkFilename = file_date + '/' + patientID + '_' + str(sessID) + '_' + taskName + '.qtm'
                await connection.save(BeatParkFilename)
            if taskID == 2:
                music = "musicoff"
                musicMsg = "1;" + music + ";1;" + str(batchID)
                bytesMusicMsg = bytes(musicMsg,'utf8')
                # MusicMsgToSave = MusicMsgToSave + '\n' + musicMsg
                sentMusic = sock_udp.sendto(bytesMusicMsg, server_address_udp)
                print('music ' + str(music) + ' sent')
           
            endMsg = "100;endmotion;" + patientID + ';' + str(exam_date) + ';' + str(taskID) + ';' + str(batchID)
            bytesEndMsg = bytes(endMsg,'utf8')
            # sentEnd = sock_udp.sendto(bytesEndMsg, server_address_udp)
            print('endmotion for task ', str(taskID), ' sent')
            
            await connection.stream_frames_stop()
            # np.save('yAxis',yAxis)
            # np.save('xAxis',xAxis)
            # plt.close()
            # with open((cd + '/RESULTATS/stream_signal' + '_' + patientID + '_' + taskName + '.csv'),'w') as f:
            #     f.write(motionMsgToSave)
            break
    # with open((cd + '/RESULTATS/synchro_signal' + '_' + patientID + '_' + taskName + '.csv'),'w') as f:
    #     f.write(MusicMsgToSave)
    #ajouter identifiant du patient et session
    with open((cd + '/RESULTATS/synchroS' + '_' + patientID + '_' + str(sessID) + '_' + taskName + '.csv'),'w') as f:
        # f.write(str(volume_occurence_list)) #indiquer le chemin complet
        f.write(str(SynchroMsgToSave)) #indiquer le chemin complet
    print('writed ' + cd + '/RESULTATS/synchroS' + '_' + patientID + '_' + taskName + '.csv')
    ##print('writed file !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    
    #TRAILER
    #DATATYPE_CMD;K_START_MOTION|K_END_MOTION;[BODY_MARKER];[PATIENT_ID];
    #[LAB_DATE];[TASK_ID];[BATCH_ID]
    # headerDatatype = 100
    # trailerMsgV1 = str(headerDatatype) + ';endmotion;' + patientID + ';' + exam_date + ';' + str(taskID) + ';' + str(batchID)
    # trailerMsg = str(headerDatatype) + ';endmotion;' + str(markerID) + ';' + patientID + ';' + exam_date + ';' + str(taskID) + ';' + str(batchID)
    # bytesTrailerMsg = bytes(trailerMsgV1,'utf8')
    # sentTrailer = sock_udp.sendto(bytesTrailerMsg, server_address_udp)
    
    print('done, saving and stopping...')
    await asyncio.sleep(2)
    
    loop.stop()
            # break

# async def stream3D(connection, on_packet, exam_information):
async def stream3D(connection, on_packet, sock_udp, server_address_udp):
    global motionMsgToSave
    print('streaming')
    await connection.stream_frames(frames='frequency:50', components=["3d"], on_packet=on_packet)
    #WARINING : if you change the frequency divisor, change also the frequency variable of task 1 on 'on_packet' function
    #if you want to avoid error on cadence calculation

async def main():
    
    global batchID

    # If you want to stream recorded data in a real-time way, change json file and load it here.
    # There might be a bug about file path. Will test it later. -- Sept. 08, 2020

    #QTM_FILE = pkg_resources.resource_filename("qtm", file_name_qtm)
    
    # Create a UDP socket for data streaming
    sock_udp, server_address_udp = publisher_udp_main()
    
    #GO TO TASK
    batchID = round(time.time()*1000)
    
    # Connect to qtm
    connection = await qtm.connect(IP_server)

    # Connection failed?         
    if connection is None:
        print("Failed to connect")
        return

    xml_string = await connection.get_parameters(parameters=["3d"])

    
    
    global motionMsgToSave
    motionMsgToSave = ''

    def on_packet(packet):
        global motionMsgToSave
        global xcount
        global xcountSpeed
        global xAxis
        global yAxis
        global xSpeed
        global ySpeed
        global measuredCadency
        global music
        global task1sent
        
        xcount +=1
        
        header, mark = packet.get_3d_markers()

        motionDatatype = 0
        
        #scalable variable
        localTimestampStream = packet.framenumber * 10 #ms
        normTimestampStream = round(time.time()*1000)
        
        axes = ['x','y','z']
        
        axis_number = axes.index(axis_name)
        position = mark[markerID] #using order of "manual label listing", begining with 0
        
        #*Real-Time plotting (but difficult to receive 's' and 'spacebar' in front of plot)
        xAxis.append(xcount)
        yAxis.append(position[axis_number])
        # plt.plot(xAxis,yAxis, color='red')
        # plt.pause(0.001)
        # plt.draw()
        
        #THRESHOLD
        #threshold calculation if xcount suffisant
        # thresholdDatatype = 1
        # thresholdMsg = str(thresholdDatatype) + ';threshold;' + str(threshold) + ';' + str(batchID)
        # bytesThresholdMsg = bytes(thresholdMsg,'utf8')
        # sent = sock_udp.sendto(bytesThresholdMsg, server_address_udp)

        #(str(time.localtime()[0:3])[1:12]) = actual date
        motionMsg = str(motionDatatype) + ';' + str(normTimestampStream) + ';' + laterality + ';' + axis_name + ';' + str(round(position[axis_number],6)) + ';' + str(batchID)
        motionMsgV1 = str(motionDatatype) + ';' + str(localTimestampStream) + ';' + str(normTimestampStream) + ';' + str(markerID) + ';' + laterality + ';' + axis_name + ';' + str(round(position[axis_number],6)) + ';' + patientID + ';' + exam_date + ';' + str(taskID) + ';' + str(batchID)
        motionMsgV2 = str(motionDatatype) + ';' + str(localTimestampStream) + ';' + str(round(position[axis_number],6))
        bytesMotionMsg = bytes(motionMsgV2,'utf8')
        ## motionMsgToSave = motionMsgToSave + '\n' + motionMsg

        print(motionMsgV2)
        
        if taskID == 1:
            if sendmotion > 0: #sendmotion is 1 then 2 when we have to stream motion
                sent = sock_udp.sendto(bytesMotionMsg, server_address_udp)

        elif taskID == 3:
            sent = sock_udp.sendto(bytesMotionMsg, server_address_udp)
    
    #INITIALISATION
    
    if taskID == 1:
        music = 0
        musicMsg = str(musicDatatype) + ';music;' + str(music) + ';' + str(batchID)
        bytesMusicMsg = bytes(musicMsg,'utf8')
        # sentMusic = sock_udp.sendto(bytesMusicMsg, server_address_udp)
        # print('music = 0 sent')
        await asyncio.sleep(2)
    if taskID == 3:
        BHtaskID = 3
        goToTaskMsg = str(gotaskDatatype) +';task;' + str(BHtaskID) + ';' + str(batchID)    
        bytesGoToTaskMsg = bytes(goToTaskMsg,'utf8')
        await asyncio.sleep(2)
    if taskID == 4:
        goMsg = "1;goirmf;1;" + str(batchID)
        bytesGoMsg = bytes(goMsg,'utf8')
        sentGo = sock_udp.sendto(bytesGoMsg, server_address_udp)
        print('goTask for task 4 sent')
    
    # await connection.start(rtfromfile=True)#for simulation
    async with qtm.TakeControl(connection, "password"):
        await connection.new()
        time.sleep(7)
    await connection.start()#for real acquisition
    
    volume_count = 1#demarre à 1 et volume count +1 après check mristape
    synchroTask = asyncio.create_task(MRIsynchro(connection, sock_udp, server_address_udp, volume_count))
    print('ready to hear fMRI signal')
    #streaming and calling 'on_packet' function
    streamTask = asyncio.create_task(stream3D(connection, on_packet, sock_udp, server_address_udp))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # Run our asynchronous main function forever
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
