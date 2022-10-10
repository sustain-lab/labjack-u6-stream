"""
Stream data from LabJack U6 to a file. Script adapted from
https://github.com/labjack/LabJackPython/blob/master/Examples/streamTest.py.
Currently implemented only for 2 channels on analog inputs 0 and 1.
"""

from datetime import datetime
import u6

SCAN_FREQUENCY = 1000
STREAM_DURATION_SECONDS = 10

# Don't edit this
NUM_CHANNELS = 2

d = u6.U6()
d.getCalibrationData()

d.streamConfig(
    NumChannels=NUM_CHANNELS,
    ChannelNumbers=[0, 1],
    ChannelOptions=[0, 0],
    SettlingFactor=1,
    ResolutionIndex=1,
    ScanFrequency=SCAN_FREQUENCY
)

max_requests = STREAM_DURATION_SECONDS * NUM_CHANNELS

try:

    d.streamStart()

    start = datetime.utcnow()
    print('Start time is %s' % start)
    filename = datetime.strftime(start, 'u6_stream_%Y%m%d_%H%M%S.%f.csv')
    print('Writing data to %s..' % filename)
    f = open(filename, 'w')
    f.write('Time,Channel1,Channel2\n')

    missed = 0
    dataCount = 0
    packetCount = 0
    sample = 0
    for r in d.streamData():
        if r is not None:
            if dataCount >= max_requests:
                break

            if r["errors"] != 0:
                print("Errors counted: %s ; %s" % (r["errors"], datetime.utcnow()))

            if r["numPackets"] != d.packetsPerRequest:
                print("----- UNDERFLOW : %s ; %s" % (r["numPackets"], datetime.utcnow()))

            if r["missed"] != 0:
                missed += r["missed"]
                print("+++ Missed %s" % r["missed"])
            # Currently hardcorded for first two analog inputs
            for n in range(len(r['AIN0'])):
                f.write('%.3f,%.6f,%.6f\n' % (sample / SCAN_FREQUENCY, r['AIN0'][n], r['AIN1'][n]))
                sample += 1
            dataCount += 1
            packetCount += r["numPackets"]
        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
            print("No data ; %s" % datetime.utcnow())
except:
    raise
finally:
    stop = datetime.utcnow()
    d.streamStop()
    print(" Stop time is %s" % stop)
    d.close()

    sampleTotal = packetCount * d.streamSamplesPerPacket

    scanTotal = sampleTotal / NUM_CHANNELS  # sampleTotal / NumChannels
    print(
        "%s requests with %s packets per request with %s samples per packet = %s samples total."
        % (
            dataCount,
            (float(packetCount) / dataCount),
            d.streamSamplesPerPacket,
            sampleTotal,
        )
    )
    print("%s samples were lost due to errors." % missed)
    sampleTotal -= missed
    print("Adjusted number of samples = %s" % sampleTotal)

    runTime = (stop - start).total_seconds()
    print("The stream took %s seconds." % runTime)
    print("Actual Scan Rate = %s Hz" % SCAN_FREQUENCY)
    print(
        "Timed Scan Rate = %s scans / %s seconds = %s Hz"
        % (scanTotal, runTime, float(scanTotal) / runTime)
    )
    print(
        "Timed Sample Rate = %s samples / %s seconds = %s Hz"
        % (sampleTotal, runTime, float(sampleTotal) / runTime)
    )