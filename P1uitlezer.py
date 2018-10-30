import sys
import serial
import json
import time
from pymongo import MongoClient
from datetime import datetime


################
# Error display #
################
def show_error():
    ft = sys.exc_info()[0]
    fv = sys.exc_info()[1]
    print("Fout type: %s" % ft)
    print("Fout waarde: %s" % fv)
    return


#Maak verbinding met MongoDB
client = MongoClient("192.168.2.186",27017)
db = client.commevents
Slimmemeter =  db.slimmemeter


################################################################################################################################################
# Main program
################################################################################################################################################
print("Slimmemeter uitlezen")
print("Control-C om te stoppen")

# Set COM port config
ser = serial.Serial()
ser.baudrate = 9600
ser.bytesize = serial.SEVENBITS
ser.parity = serial.PARITY_EVEN
ser.stopbits = serial.STOPBITS_ONE
ser.xonxoff = 0
ser.rtscts = 0
ser.timeout = 20
ser.port = "/dev/ttyUSB0"

# Open COM port
try:
    ser.open()
except:
    sys.exit("Fout bij het openen van %s. Programma afgebroken." % ser.name)

# Initialize
# stack is mijn list met de 20 regeltjes.
p1_teller = 0
stack = []
doc = {}
doc["DalDag"] = ""
doc["PiekDag"] = ""
doc["DalTerug"] = ""
doc["PiekTerug"] = ""
doc["AfgenomenVermogen"] = ""
doc["TeruggeleverdVermogen"] = ""


while p1_teller < 20:
    p1_line = ''
    # Read 1 line
    try:
        p1_raw = ser.readline()
    except:
        sys.exit("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % ser.name)

    p1_str = str(p1_raw)
    # p1_str=str(p1_raw, "utf-8")
    p1_line = p1_str.strip()
    stack.append(p1_line)
    # als je alles wil zien moet je de volgende line uncommenten
    #    print (p1_line)
    p1_teller = p1_teller + 1

# Initialize
# stack_teller is mijn tellertje voor de 20 weer door te lopen. Waarschijnlijk mag ik die p1_teller ook gebruiken
stack_teller = 0
meter = 0

while stack_teller < 20:


    if stack[stack_teller][0:9] == "1-0:1.8.1":
        doc["DalDag"] = stack[stack_teller][10:15]
        print "daldag      ", stack[stack_teller][10:15]
        meter = meter + int(float(stack[stack_teller][10:15]))
    elif stack[stack_teller][0:9] == "1-0:1.8.2":
        doc["PiekDag"] = stack[stack_teller][10:15]
        print "piekdag     ", stack[stack_teller][10:15]
        meter = meter + int(float(stack[stack_teller][10:15]))
    #	print "meter totaal  ", meter
    # Daltarief, teruggeleverd vermogen 1-0:2.8.1
    elif stack[stack_teller][0:9] == "1-0:2.8.1":
        doc["DalTerug"] = stack[stack_teller][10:15]
        print "dalterug    ", stack[stack_teller][10:15]
        meter = meter - int(float(stack[stack_teller][10:15]))
    #	print "meter totaal  ", meter
    # Piek tarief, teruggeleverd vermogen 1-0:2.8.2
    elif stack[stack_teller][0:9] == "1-0:2.8.2":
        print "piekterug   ", stack[stack_teller][10:15]
        doc["PiekTerug"] = stack[stack_teller][10:15]
        meter = meter - int(float(stack[stack_teller][10:15]))
        # mijn verbruik was op 17-10-2014 1751 kWh teveel teruggeleverd. Nieuw jaar dus opnieuw gaan rekenen
        #	meter = meter + 1751
        #        print "meter totaal ", meter, " (afgenomen/teruggeleverd van het net vanaf 17-10-2014)"
        # Mijn verbruik was op 23-10-2016 (8850+3247) - (3846+9632) = 12097 - 13478 = 1381
        meter = meter + 1381
        print "meter totaal ", meter, " (afgenomen/teruggeleverd van het net vanaf 23-10-2016)"
    # Huidige stroomafname: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:1.7.0":
        print "Afgenomen vermogen      ", int(float(stack[stack_teller][10:17]) * 1000), " W"
        doc["AfgenomenVermogen"] = int(float(stack[stack_teller][10:17]) * 1000)

    # Huidig teruggeleverd vermogen: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:2.7.0":
        print "Teruggeleverd vermogen  ", int(float(stack[stack_teller][10:17]) * 1000), " W"
        doc["TeruggeleverdVermogen"] = int(float(stack[stack_teller][10:17]) * 1000)
    # Gasmeter: 0-1:24.3.0
    elif stack[stack_teller][0:10] == "0-1:24.3.0":
        print "Gas   ", int(float(stack[stack_teller + 1][1:10]) * 1000), " dm3"
    else:
        pass
    stack_teller = stack_teller + 1


# print (stack, "\n")
print json.dumps(doc)
# Close port and show status
try:
    ser.close()
except:
    sys.exit("Oops %s. Programma afgebroken." % ser.name)
