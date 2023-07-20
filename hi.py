import serial
import time
import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtGui
#import matplotlib.pyplot as plt
from operator import add
import csv
import datetime
from datetime import date
# Change the configuration file name
configFileName = 'new_cfg.cfg'

CLIport = {}
Dataport = {}
byteBuffer = np.zeros(2**15,dtype = 'uint8')
byteBufferLength = 0;


# ------------------------------------------------------------------

# Function to configure the serial ports and send the data from
# the configuration file to the radar
def serialConfig(configFileName):
    
    global CLIport
    global Dataport
    # Open the serial ports for the configuration and the data ports
    
    # Raspberry pi
    #CLIport = serial.Serial('/dev/ttyACM0', 115200)
    #Dataport = serial.Serial('/dev/ttyACM1', 921600)
    
    # Windows
    CLIport = serial.Serial('COM5', 115200)
    Dataport = serial.Serial('COM6', 921600)

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        CLIport.write((i+'\n').encode())
        print(i)
        time.sleep(0.01)
        
    return CLIport, Dataport

# ------------------------------------------------------------------

# Function to parse the data inside the configuration file
def parseConfigFile(configFileName):
    configParameters = {} # Initialize an empty dictionary to store the configuration parameters
    
    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        
        # Split the line
        splitWords = i.split(" ")
        
        # Hard code the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 3
        
        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1;
            
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2;
                
            digOutSampleRate = int(splitWords[11]);
            
        # Get the information about the frame configuration    
        elif "frameCfg" in splitWords[0]:
            
            chirpStartIdx = int(splitWords[1]);
            chirpEndIdx = int(splitWords[2]);
            numLoops = int(splitWords[3]);
            numFrames = int(splitWords[4]);
            framePeriodicity = int(splitWords[5]);

            
    # Combine the read data to obtain the configuration parameters           
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = 16 #numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    print('###################', configParameters["numDopplerBins"], configParameters["numRangeBins"])
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)
    
    return configParameters
   
# ------------------------------------------------------------------
# word array to convert 4 bytes to a 16 bit number
def func1(byteBuffer, idX, configParameters, numDetectedObj):
    word = [1, 2**8]
    tlv_numObj = np.matmul(byteBuffer[idX:idX+2],word)
    idX += 2
    tlv_xyzQFormat = 2**np.matmul(byteBuffer[idX:idX+2],word)
    idX += 2
    
    # Initialize the arrays
    rangeIdx = np.zeros(numDetectedObj,dtype = 'int16')
    dopplerIdx = np.zeros(numDetectedObj,dtype = 'int16')
    peakVal = np.zeros(numDetectedObj,dtype = 'int16')
    x = np.zeros(numDetectedObj,dtype = 'int16')
    y = np.zeros(numDetectedObj,dtype = 'int16')
    z = np.zeros(numDetectedObj,dtype = 'int16')
    #print(f"tlv_numObj = {tlv_numObj}")
    for objectNum in range(numDetectedObj):
        
        # Read the data for each object
        rangeIdx[objectNum] =  np.matmul(byteBuffer[idX:idX+2],word)                    
        idX += 2
        dopplerIdx[objectNum] = np.matmul(byteBuffer[idX:idX+2],word)
        idX += 2                    
        peakVal[objectNum] = np.matmul(byteBuffer[idX:idX+2],word)
        idX += 2                    
        x[objectNum] = np.matmul(byteBuffer[idX:idX+2],word)
        idX += 2
        y[objectNum] = np.matmul(byteBuffer[idX:idX+2],word)
        idX += 2
        z[objectNum] = np.matmul(byteBuffer[idX:idX+2],word)
        idX += 2
        #print(f"rangeIdx[{objectNum}] = {rangeIdx[objectNum]} \t dopplerIdx[{objectNum}] = {dopplerIdx[objectNum]} \t peakVal[{objectNum}] = {peakVal[objectNum]} \t x[{objectNum}] = {x[objectNum]} \t y[{objectNum}] = {y[objectNum]} \t z[{objectNum}] = {z[objectNum]} \t")

    # Make the necessary corrections and calculate the rest of the data
    rangeVal = rangeIdx * configParameters["rangeIdxToMeters"]
    dopplerIdx[dopplerIdx > (configParameters["numDopplerBins"]/2 - 1)] = dopplerIdx[dopplerIdx > (configParameters["numDopplerBins"]/2 - 1)] - 65535
    dopplerVal = dopplerIdx * configParameters["dopplerResolutionMps"]
    #x[x > 32767] = x[x > 32767] - 65536
    #y[y > 32767] = y[y > 32767] - 65536
    #z[z > 32767] = z[z > 32767] - 65536
    #print(f"tlv_xyzQFormat = {tlv_xyzQFormat} \t x = {x}")
    #x = x / tlv_xyzQFormat
    #y = y / tlv_xyzQFormat
    #z = z / tlv_xyzQFormat
    
    # Store the data in the detObj dictionary
    detObj = {"numObj": numDetectedObj, "rangeIdx": rangeIdx, "range": rangeVal, "dopplerIdx": dopplerIdx, \
                "doppler": dopplerVal, "peakVal": peakVal, "x": x, "y": y, "z": z}
    
    dataOK = 1
    return detObj, dataOK
def func23(byteBuffer, idX, configParameters, isRangeProfile):
    traceidX = 0
    if isRangeProfile:
        traceidX = 0
    else:
        traceidX = 2
    numrp = 2 * configParameters["numRangeBins"]
    rp = byteBuffer[idX : idX + numrp]

    rp = list(map(add, rp[0:numrp:2], list(map(lambda x: 256 * x, rp[1:numrp:2]))))
    rp_x = (
        np.array(range(configParameters["numRangeBins"]))
        * configParameters["rangeIdxToMeters"]
    )
    idX += numrp
    if traceidX == 0:
        noiseObj = {"rp": rp}
        return noiseObj
    elif traceidX == 2:
        noiseObj = {"noiserp": rp}
    return noiseObj
def func5(idX, byteBuffer, configParameters):
    numBytes = (
        int(configParameters["numDopplerBins"])
        * int(configParameters["numRangeBins"])
        * 2
    )
    print('######## numBytes', numBytes)
    # Convert the raw data to int16 array
    payload = byteBuffer[idX : idX + numBytes]
    idX += numBytes
    # rangeDoppler = math.add(
    #     math.subset(rangeDoppler, math.index(math.range(0, numBytes, 2))),
    #     math.multiply(math.subset(rangeDoppler, math.index(math.range(1, numBytes, 2))), 256)
    # );

    rangeDoppler = list(
        map(
            add,
            payload[0:numBytes:2],
            list(map(lambda x: 256 * x, payload[1:numBytes:2])),
        )
    )  # wrong implementation. Need to update the range doppler at range index

    # rangeDoppler = payload.view(dtype=np.int16)
    # Some frames have strange values, skip those frames
    # TO DO: Find why those strange frames happen
    # if np.max(rangeDoppler) > 10000:
    #     return 0

    # Convert the range doppler array to a matrix
    rangeDoppler = np.reshape(
        rangeDoppler,
        (int(configParameters["numDopplerBins"]), configParameters["numRangeBins"]),
        "F",
    )  # Fortran-like reshape
    rangeDoppler = np.append(
        rangeDoppler[int(len(rangeDoppler) / 2) :],
        rangeDoppler[: int(len(rangeDoppler) / 2)],
        axis=0,
    )

    dopplerM = []
    rangeDoppler_list = list(rangeDoppler)
    for e in rangeDoppler_list:
        dopplerM.append(list(e))

    #
    # # Generate the range and doppler arrays for the plot# This is dopplermps from js.
    dopplerObj = {
        "rangeDoppler": dopplerM,
    }
    return dopplerObj 
def func6(byteBuffer, idX, configParameters):
    word = [1, 2**8, 2**16, 2**24]
    interFrameProcessingTime = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4
    transmitOutputTime = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4
    interFrameProcessingMargin = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4
    interChirpProcessingMargin = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4
    activeFrameCPULoad = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4

    interFrameCPULoad = np.matmul(byteBuffer[idX : idX + 4], word)
    idX += 4

    statisticsObj = {
        "interFrameProcessingTime": interFrameProcessingTime,
        "transmitOutputTime": transmitOutputTime,
        "interFrameProcessingMargin": interFrameProcessingMargin,
        "interChirpProcessingMargin": interChirpProcessingMargin,
        "activeFrameCPULoad": activeFrameCPULoad,
        "interFrameCPULoad": interFrameCPULoad,
    }
    return statisticsObj
def fun23(byteBuffer, idX, configParameters, bol):
    traceidX = 0
    if(bol) :
        traceidX = 0
    else:
        traceidX = 2
    numrp = 2 * configParameters["numRangeBins"]
    rp = byteBuffer[idX : idX + numrp]
    rp = list(map(add, rp[0:numrp:2], list(map(lambda x: 256 * x, rp[1:numrp:2]))))
    idX += numrp
    if traceidX == 0:
        noiseObj = {"rp": rp}
        return noiseObj
    elif traceidX == 2:
        noiseObj = {"noiserp": rp}
        return noiseObj

def fun1(byteBuffer, idX, configParameters, numDetectedObj):
    rangeIdx = np.zeros(numDetectedObj,dtype = 'int16')
    dopplerIdx = np.zeros(numDetectedObj,dtype = 'int16')
    peakVal = np.zeros(numDetectedObj,dtype = 'int16')
    x = np.zeros(numDetectedObj,dtype = 'int16')
    y = np.zeros(numDetectedObj,dtype = 'int16')
    z = np.zeros(numDetectedObj,dtype = 'int16')
    dop = np.zeros(numDetectedObj,dtype = 'int16')
    detObj = {}
    sizeOfObj = 16
    if(numDetectedObj < 1):
        return detObj
    for i in range(0, numDetectedObj):
        si  = idX + (i* sizeOfObj)
        x[i] = (byteBuffer[si+0],byteBuffer[si+1],byteBuffer[si+2],byteBuffer[si+3])
        y[i] = (byteBuffer[si+4],byteBuffer[si+5],byteBuffer[si+6],byteBuffer[si+7])
        z[i] = (byteBuffer[si+8],byteBuffer[si+9],byteBuffer[si+10],byteBuffer[si+11])
        dopplerIdx[i] = (byteBuffer[si+12],byteBuffer[si+13],byteBuffer[si+14],byteBuffer[si+15])
    rangeIdx = np.sqrt(np.add(np.multiply(z, z), np.add(np.multiply(x, x), np.multiply(y, y)))) 
    detObj = {"rangeIdx": rangeIdx, "dopplerIdx" : dopplerIdx, "x": x, "y": y, "z" :z}
    return detObj 
    



# Funtion to read and parse the incoming data
def readAndParseData14xx(Dataport, configParameters, filename):
    global byteBuffer, byteBufferLength
    # Constants
    OBJ_STRUCT_SIZE_BYTES = 12;
    BYTE_VEC_ACC_MAX_SIZE = 2**15;
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1;
    MMWDEMO_UART_MSG_RANGE_PROFILE   = 2;
    maxBufferSize = 2**15;
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
    dte = date.today()
    time = datetime.datetime.now().time()
    data = []
    data.append(dte)
    data.append(time)
    # Initialize variables
    magicOK = 0 # Checks if magic number has been read
    dataOK = 0 # Checks if the data has been read correctly
    frameNumber = 0
    detObj = {}
    
    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype = 'uint8')
    byteCount = len(byteVec)
    # print(byteCount)
    # Check that the buffer is not full, and then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength:byteBufferLength + byteCount] = byteVec[:byteCount]
        byteBufferLength = byteBufferLength + byteCount
        
    # Check that the buffer has some data
    if byteBufferLength > 16:
        
        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm that is the beginning of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc:loc+8]
            if np.all(check == magicWord):
                startIdx.append(loc)
               
        # Check that startIdx is not empty
        if startIdx:
            
            # Remove the data before the first start index
            if startIdx[0] > 0 and startIdx[0] < byteBufferLength:
                byteBuffer[:byteBufferLength-startIdx[0]] = byteBuffer[startIdx[0]:byteBufferLength]
                byteBuffer[byteBufferLength-startIdx[0]:] = np.zeros(len(byteBuffer[byteBufferLength-startIdx[0]:]),dtype = 'uint8')
                byteBufferLength = byteBufferLength - startIdx[0]
                
            # Check that there have no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0
                
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]
            
            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12:12+4],word)
            # Check that all the packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1
    #print(f"magicOK = {magicOK}")
    # print(byteBufferLength)
    # If magicOK is equal to 1 then process the message
    if magicOK:
        # word array to convert 4 bytes to a 32 bit number
        word = [1, 2**8, 2**16, 2**24]
        
        # Initialize the pointer index
        idX = 0
        
        # Read the header
        magicNumber = byteBuffer[idX:idX+8]
        idX += 8
        version = format(np.matmul(byteBuffer[idX:idX+4],word),'x')
        idX += 4
        totalPacketLen = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        platform = format(np.matmul(byteBuffer[idX:idX+4],word),'x')
        idX += 4
        frameNumber = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        timeCpuCycles = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        numDetectedObj = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        numTLVs = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        idX += 4
        #print(f"magicNumber = {magicNumber} \t version = {version} \t totalPacketLen = {totalPacketLen} \t platform = {platform} \t frameNumber = {frameNumber} ")
        #print(f"timeCpuCycles = {timeCpuCycles} \t\t numDetectedObj = {numDetectedObj} \t numTLVs = {numTLVs} \t\t idX = {idX}")

        # UNCOMMENT IN CASE OF SDK 2
        #subFrameNumber = np.matmul(byteBuffer[idX:idX+4],word)
        
        
        # Read the TLV messages
        for tlvIdx in range(numTLVs):
            
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]

            # Check the header of the TLV message
            #print(f"byteBuffer[idX:idX+4] = {byteBuffer[idX:idX+4]}, word = {word}")
            print('################### idX: ', idX)
            tlv_type = np.matmul(byteBuffer[idX:idX+4],word)
            if tlv_type > 10:
                print("############################################################from here")
                continue
            idX += 4
            tlv_length = np.matmul(byteBuffer[idX:idX+4],word)
            idX += 4
            print('##################### tlv_type, tlv_length, idX:', tlv_type,tlv_length, idX)
            #print(f"tlv_type = {tlv_type} \t MMWDEMO_UART_MSG_DETECTED_POINTS = {MMWDEMO_UART_MSG_DETECTED_POINTS}")
            # Read the data depending on the TLV message
            if tlv_type == 1:
                pass
            elif tlv_type == 2:
                detObj = fun23(byteBuffer, idX, configParameters, True)
                data.append(detObj["rp"])
                print('############## Noise Profile Shape', len(detObj['rp']))
            elif tlv_type == 3:
                detObj = fun23(byteBuffer, idX, configParameters, False)
                data.append(detObj["noiserp"])
                print('############## Noise Profile Shape', len(detObj['noiserp']))
            elif tlv_type == 5:
                detObj = func5(idX, byteBuffer, configParameters)
                data.append(detObj["rangeDoppler"])
                print('######### RangeDoppler Shape: ', detObj['rangeDoppler'])
            elif tlv_type == 6:
                pass                                                                                                      
            idX += tlv_length
        writer = csv.writer(filename)
        writer.writerow(data)
        
        
        
        # Remove already processed data
        if idX > 0 and byteBufferLength > idX:
            print('############### Extra data found')
            shiftSize = totalPacketLen
               
            byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
            byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),dtype = 'uint8')
            byteBufferLength = byteBufferLength - shiftSize
            
            # Check that there are no errors with the buffer length
            if byteBufferLength < 0:
                print('############### Some Issue with buffer length')
                byteBufferLength = 0
                

    return dataOK, frameNumber, detObj

# ------------------------------------------------------------------

# Funtion to update the data and display in the plot
def update(file):
     
    dataOk = 0
    global detObj
    x = []
    y = []
      
    # Read and parse the received data
    dataOk, frameNumber, detObj = readAndParseData14xx(Dataport, configParameters,file)
    #print(f"dataOK = {dataOk}")
    # if dataOk and len(detObj["x"]) > 0:
    #     #print(detObj)
    #     x = -detObj["x"]
    #     y = detObj["y"]
    #     # plt.scatter(x,y)
    #     # plt.pause(0.05)
    #     #s.setData(x,y)
    #     #QtGui.QApplication.processEvents()
    
    return dataOk


# -------------------------    MAIN   -----------------------------------------
# Configurate the serial port
CLIport, Dataport = serialConfig(configFileName)

# Get the configuration parameters from the configuration file
configParameters = parseConfigFile(configFileName)
# the csv file part
file = open("data.csv", 'w', newline='')
writer = csv.writer(file)
writer.writerow([ "date", "time", "range_profile", "noise_profile", "range_doppler"])

# START QtAPPfor the plot
"""
app = QtGui.QApplication([])

# Set the plot 
pg.setConfigOption('background','w')
win = pg.GraphicsWindow(title="2D scatter plot")
p = win.addPlot()
p.setXRange(-0.5,0.5)
p.setYRange(0,1.5)
p.setLabel('left',text = 'Y position (m)')
p.setLabel('bottom', text= 'X position (m)')
s = p.plot([],[],pen=None,symbol='o')

win.show()
app.exec_()
"""
#plt.axis([0, 10, 0, 1])
#plt.show()
    
   
# Main loop 
detObj = {}  
frameData = {}    
currentIndex = 0
while 1:
    try:
        # Update the data and check if the data is okay
        dataOk = update(file)


        if dataOk:
            # Store the current frame into frameData
            frameData[currentIndex] = detObj
            currentIndex += 1
        
        time.sleep(0.033) # Sampling frequency of 30 Hz
        
    # Stop the program and close everything if Ctrl + c is pressed
    except KeyboardInterrupt:
        CLIport.write(('sensorStop\n').encode())
        CLIport.close()
        Dataport.close()
        #win.close()
        break


