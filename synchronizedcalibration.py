#Imports
from decimal import Decimal, getcontext
import time
import asyncio
#import sys
import logging
from time import sleep
from asyncua import Client, Node, ua
#import numpy as np
######################################################################

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


#Function for getting the amplitude for a given frequency and power
######################################################################
async def getampl(freq, pow):
    
    df = ua.DataValue(ua.Variant(freq, ua.VariantType.Float)) #Setting the frequency data
    dp = ua.DataValue(ua.Variant(pow, ua.VariantType.Float))  #Setting the power data
    dv = ua.DataValue(ua.Variant(1, ua.VariantType.Boolean))  #Setting the vibrator enable/disable data
    await vibfreq.set_value(df)     #Sending the frequency
    await vibpow.set_value(dp)      #Sending the power
    await vibstart.set_value(dv)    #Sending vibrator start
    period=int(1000000/freq)        #Calculating the period from the frequency
    dper=ua.DataValue(ua.Variant(period, ua.VariantType.Int32)) #Setting the period data
    await vibperiod.set_value(dper) #Sending the period
    sleep(3) #wait for the vibration to start and stabilize before starting inspection
    
    #Picture taking and data collection
    de = ua.DataValue(ua.Variant(1, ua.VariantType.Boolean)) #Setting amplitude search enable data
    await amplSearch.set_value(de) #Send amplitude search enable
    while (await processdone.read_value())==0: #Check if search was done
        sleep(0.01) #Sleep
    ampl=await pampl.read_value()/100 #Read found amplitude from the PLC
    dpd = ua.DataValue(ua.Variant(0, ua.VariantType.Boolean)) #Setting the process done data
    await processdone.set_value(dpd) #Sending the process done data
    #hPosXf=await hPosX.read_value() #For troubleshooting
    #lPosXf=await lPosX.read_value() #For troubleshooting
    await vibstop.set_value(dv)      #Sending vibrator stop command
    return ampl #Returning the amplitude value
######################################################################


async def main():
    getcontext().prec = 4     #used for rounding the frequencies to avoid repeated frequency searches
    startTime = time.time()   #Saves the start time in order to find the duration of the test
    url = 'opc.tcp://192.168.2.11:4840' # The IP address of the PLC
    async with Client(url=url) as client:
      

        #Initializing the variables internal use for OPC-UA and making them global
        global amplSearch, vibperiod, pampl, vibstart, vibstop, vibfreq, vibpow, hPosX, lPosX, processdone
        
        #OPC-UA variable addresses
        ######################################################################
        vibstart = client.get_node("ns=6;s=::vibrator:opcua[0].startVibrators")
        amplSearch = client.get_node("ns=6;s=::Program:amplSearch")
        vibstop = client.get_node("ns=6;s=::vibrator:opcua[0].stopVibrators")
        vibfreq = client.get_node("ns=6;s=::vibrator:opcua[0].frequency")                   # For the circular vibrator
        vibpow = client.get_node("ns=6;s=::vibrator:opcua[0].vibratorSpeedPercent")         # For the circular vibrator
        #vibfreq = client.get_node("ns=6;s=::vibrator:opcua[1].frequency")                  # For the linear vibrator
        #vibpow = client.get_node("ns=6;s=::vibrator:opcua[1].vibratorSpeedPercent")        # For the linear vibrator
        pampl = client.get_node("ns=6;s=::Program:pampl")
        vibperiod = client.get_node("ns=6;s=::Program:period")
        processdone = client.get_node("ns=6;s=::Program:processdone")
        #hPosX = client.get_node("ns=6;s=::Program:hPosX") #For troubleshooting
        #lPosX = client.get_node("ns=6;s=::Program:lPosX") #For troubleshooting
        ######################################################################



        #Frequency and power sweep code
        ######################################################################
        for xl4 in range(1): #The range can be changed to set the number of runs 1- 1run

            ##################################
            #User search parameters
            ##################################
            pow=50      #Starting power
            tpow = 50   #End power, if equal to starting power only one power runs
            ipow = 10   #Power increment
            sfr = Decimal(49) #starting freq
            tfr = Decimal(50.2) #target freq
            afn1="linvibsctest_" #File name (structure: afn1+X+_PY, X - run number (starts at 0), Y - power setting)
            ##################################

            #Advanced settings
            ##################################
            ifr1=Decimal(0.01)  #Final fine search increment
            ifr2=Decimal(0.04)  #Medium search increment
            ifr3=Decimal(0.16)  #Initial Coarse search increment
            ##################################


            fr=sfr #Reset frequency between runs
            hampl=0 #Hightest amplitude declaration
            hfreq=0 #Highest frequency declaration
            usedfreq=[0] #Storing used frequencies to make sure they do not repeat
            #################################
            
            while pow<=tpow:
                afni=afn1+str(xl4)+'_P'+str(pow)+'.txt' #Creating the file name
                f = open(afni, "w")                     #Creating/opening the file

                #Starting coarse sweep
                while fr<=tfr:                          #Run when frequency is lower than target
                    if (fr in usedfreq)==0:             #Skip frequencies that have already been tested
                        usedfreq.append(fr)             #Add the frequency to the list of used frequencies
                        amplf=await getampl(float(fr), pow) #Call the function for measuring the amplitude

                        if amplf>hampl: #If the new amplitude is higher than previous ones
                            hampl=amplf #Saves the highest amplitude
                            hfreq=fr    #Saves the frequency for the highest amplitude

                        print("Frequency: " + str(fr) + " Power: "+ str(pow) + " Amplitude: "+ str(amplf))  #Print for troubleshooting
                        f.write(str(fr) + ' ' + str(amplf) + '\n')  #Save frequency and amplitude into the file

                    fr+=ifr3    #Increase the frequency by coarse increment
                    sleep(0.25) #Wait to avoid bugs with the vibrator not starting

                #Coarse sweep done, starting medium sweep
                fr=(hfreq-ifr3) #Set the starting frequency
                efreq=(hfreq+ifr3)  #Set the end frequency
                while fr<=efreq:
                    if (fr in usedfreq)==0:
                        usedfreq.append(fr)
                        amplf=await getampl(float(fr), pow)
                        if amplf>hampl:
                            hampl=amplf
                            hfreq=fr

                        print("Frequency: " + str(fr) + " Power: "+ str(pow) + " Amplitude: "+ str(amplf))
                        f.write(str(fr) + ' ' + str(amplf) + '\n')

                    fr+=ifr2
                    sleep(0.25)
                #Medium sweep done, starting final sweep
                fr=(hfreq-ifr2) #Set the starting frequency
                efreq=(hfreq+ifr2) #Set the end frequency
                while fr<=efreq:
                    if (fr in usedfreq)==0:
                        usedfreq.append(fr)
                        amplf=await getampl(float(fr), pow)
                        if amplf>hampl: 
                            hampl=amplf
                            hfreq=fr

                        print("Frequency: " + str(fr) + " Power: "+ str(pow) + " Amplitude: "+ str(amplf))
                        f.write(str(fr) + ' ' + str(amplf) + '\n')

                    fr+=ifr1
                    sleep(0.25)

                print("Highest frequency: " + str(hfreq) + " Amplitude: "+ str(hampl))
                #Final sweep done
                pow+=ipow #Increment the power
                fr=sfr #Reset the frequency to the starting frequency
                hampl = 0   #Reset the highest amplitude
                hfreq = 0   #Reset the highest frequency
                usedfreq=[0]#Reset the used frequencies
                f.close     #Close the file

        
        executionTime = (time.time() - startTime)                       #Calculates the running time
        print('Execution time in seconds: ' + str(executionTime))       #Displays the running time

if __name__ == '__main__':
    asyncio.run(main())