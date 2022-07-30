#!/usr/bin/python3

from __future__ import print_function
import sys
import argparse
from textwrap import indent

from gattlib import DiscoveryService
from gattlib import GATTRequester
from gattlib import GATTRequester

from threading import Event

from datetime import datetime
from time import sleep

import json

parser = argparse.ArgumentParser(description='Receive measurement values from a J7-C USB power monitor using BLE')

group_debug_me = parser.add_mutually_exclusive_group()
group_debug_me.add_argument("-v", "--verbose", help="increase output verbosity. Repeat for higher verbosity (max. 5)", action="count", default=0)
group_debug_me.add_argument("-q", "--quiet", help="suppress non-data output messages", action="store_true")

group_dev = parser.add_argument_group(title="Device control")
group_dev.add_argument("-d", "--device", help="target device MAC address. If no address is given the first compatible device found will be used", default=False)
group_dev.add_argument('-w', '--wait', help='wait for device to appear', action='store_true')
group_dev.add_argument('-r', '--reconnect', help='wait and reconnect when loosing connection', action='store_true')
group_dev.add_argument("-H", "--hci", help="HCI used for communication. Defaults to hci0", default="hci0")
group_dev.add_argument("-T", "--scantime", help="Time in seconds to scan for devices. Defaults to 2 Seconds", default=2, type=int)

group_out = parser.add_argument_group(title="Output options")
group_out.add_argument("-m", "--mode", help="output type", default='Text', choices=['Text', 'CSV', 'JSON', 'RAW', 'InfluxDB'])
group_out.add_argument('-O', '--output', help='output file, device or network address ([tcp|udp]://[host_or_ip]:port)', default="/dev/stdout")
group_out.add_argument('-a', '--append', help='append output if it is a file', action='store_true')

group_out_csv = parser.add_argument_group(title="Output options for CSV")
group_out_csv.add_argument("--csv-delimiter", help="CSV delimiter. Default: ';'", default=';')
group_out_csv.add_argument("--csv-no-header", help="Omit CSV header", action="store_true")

group_out_json = parser.add_argument_group(title="Output options for JSON")
group_out_json.add_argument("--json-pretty", help="Use pretty-print for JSON Output", action="store_true")

group_out_raw = parser.add_argument_group(title="Output options for RAW")
group_out_raw.add_argument("--raw-header", help="Add address header", action="store_true")
group_out_raw.add_argument("--raw-pretty", help="Use pretty-print for RAW Output", action="store_true")

args = parser.parse_args()

debugLevel = 1
if args.verbose:
    debugLevel = args.verbose
elif args.quiet:
    debugLevel = 0

def debug(level, msg):
    if level <= debugLevel:
        sys.stderr.write(str(msg) + "\n")

def output(data, overwrite=False, newline="\n"):
    #@TODO: output to file/device
    param = "a"
    if overwrite:
        param = "w"
    with open(args.output, param) as f:
        for line in data:
            f.write(str(line) + newline)
            if args.output != "/dev/stdout":
                debug(3, line)

class NotifyRequester(GATTRequester):
    fulldata = False

    def __init__(self, wakeup, *args):
        self.wakeup = wakeup
        GATTRequester.__init__(self, *args)

    def on_notification(self, handle, data):
        if(len(data) == 23):
            self.fulldata = data
        elif(len(data) == 19):
            self.fulldata += data

            voltage = int.from_bytes(self.fulldata[0x07:0x0a], 'big', signed=False)
            current = int.from_bytes(self.fulldata[0x0a:0x0d], 'big', signed=False)
            capacity = int.from_bytes(self.fulldata[0x0d:0x10], 'big', signed=False)
            power = voltage/100*current/100
            if voltage > 0 and current > 0:
                resistance = (voltage/100)/(current/100)
            else:
                resistance = 0
            energy = int.from_bytes(self.fulldata[0x10:0x14], 'big', signed=False)
            hours = int.from_bytes(self.fulldata[0x1d:0x1f], 'big', signed=False)
            minutes = int(self.fulldata[0x1f])
            seconds = int(self.fulldata[0x20])
            temperature = int(self.fulldata[0x1c])
            #@TODO: D+ might need adjustment if in QC?J7-
            data1 = int.from_bytes(self.fulldata[0x19:0x1b], 'big', signed=False)
            data2 = int.from_bytes(self.fulldata[0x14:0x16], 'big', signed=False)
            #@TODO: Signaling type
            #@TODO: Current measurement slot

            if args.mode == 'Text':
            
                data = [
                    ("    Voltage: {:8.2f}V".format(voltage/100)),
                    ("    Current: {:8.2f}A".format(current/100)),
                    ("      Power: {:8.2f}W".format(power)),
                    (" Resistance: {:8.2f}Ω".format(resistance)),
                    "",
                    ("   Capacity: {:5}   mAh".format(capacity)),
                    ("     Energy: {:8.2f}Wh".format(energy/100)),
                    ("    Runtime: {:04}:{:02}:{:02}".format(hours, minutes, seconds)),
                    "",
                    ("Temperature: {:5}   °C".format(temperature)),
                    "",
                    ("         D+: {:8.2f}V".format(data1/100)),
                    ("         D-: {:8.2f}V".format(data2/100))
                ]
                output(data)
            elif args.mode == 'CSV':
                data = [
                    datetime.isoformat(datetime.now()), 
                    str(voltage/100), 
                    str(current/100), 
                    str(power), 
                    str(resistance), 
                    str(capacity), 
                    str(energy/100), 
                    "{:04}:{:02}:{:02}".format(hours, minutes, seconds),
                    str(temperature), 
                    str(data1/100), 
                    str(data2/100)
                ]
                output([args.csv_delimiter.join(data)])
            elif args.mode == 'JSON':
                indent = 0
                if args.json_pretty:
                    indent = 4
                jsonstr = json.dumps({
                    "timestamp": datetime.isoformat(datetime.now()),
                    "voltage": voltage/100,
                    "current": current/100,
                    "power": power,
                    "resistance": resistance,
                    "capacity": capacity,
                    "energy": energy/100,
                    "runtime": "{:04}:{:02}:{:02}".format(hours, minutes, seconds),
                    "temperature": temperature,
                    "data1": data1/100,
                    "data2": data2/100
                }, indent=indent)
                output([jsonstr, ','])
            elif args.mode == 'RAW':
                if args.raw_pretty:
                    data_raw        = (''.join('{:02x} '.format(x) for x in self.fulldata))
                else:
                    data_raw        = (''.join('{:02x}'.format(x) for x in self.fulldata))
                output([data_raw])
            elif args.mode == 'InfluxDB':
                print("NOT YET IMPLEMENTED")
                sys.exit(1)

class ReceiveNotification(object):
    def __init__(self, address):
        self.received = Event()
        self.requester = NotifyRequester(self.received, address, False)

    def connect(self):
        debug(1, "Conneting to " + target)
        sys.stdout.flush()

        self.requester.connect(True)

    def wait_notification(self):
        debug(5, "Connected, waiting for data")
        self.received.wait()

    def get_primary(self):
        debug(5, "Discovering services...")
        primary = self.requester.discover_primary()
        for prim in primary:
            debug(5, "Service" + str(prim))

    def send_data(self):
        self.requester.write_by_handle(13, b"\x01\x00")


debug(5, "Parsed arguments: " + str(args))

target = False
doWait = True

while doWait:
    doWait = False

    if args.device:
        target = args.device
    else:
        debug(2, "Searching for compatible devices")
        try:
            debug(4, "Using " + args.hci + " as HCI")
            service = DiscoveryService(args.hci)
            devices = service.discover(args.scantime)

            for address, name in devices.items():
                debug(5, "Found device - name: {}, address: {}".format(name, address))
                if name.strip("\x00") == "UC96_BLE":
                    debug(3, "Found compatible device at address " + address)
                    target = address
        except:
            debug(0, "Device discovery failed. Is bluetooth enabled? Are you root?")

    if args.wait:
        doWait = True

    if target:
        try:
            bt = ReceiveNotification(target)
            bt.connect()
            doWait = False
        except:
            pass

    if doWait:
        debug(2, "Waiting for device...")
        sleep(1)


if target == False:
    debug(0, "No target device found")
    sys.exit(1)

if not args.append:
    debug(4, "Overwriting output file")
    output("", True, '')

if args.mode == "CSV" and not args.csv_no_header:
    output([args.csv_delimiter.join(["Measurement Time", "Voltage (V)", "Current (A)", "Power (W)", "Resistance (Ω)", "Capacity (mAh)", "Energy (Wh)", "Runtime (HHHH:MM:SS)", "Temperature (°C)", "D+ (V)", "D- (V)"])])
elif args.mode == "JSON":
    output(["["])
elif args.mode == "RAW" and args.raw_header:
    if args.raw_pretty:
        output([''.join('{:02x} '.format(x) for x in range(0,0x2a))])
    else:
        output([''.join('{:02x}'.format(x) for x in range(0,0x2a))])
elif args.mode == 'InfluxDB':
    print("NOT YET IMPLEMENTED")
    sys.exit(1)

#@TODO: Reconnect if connection lost
#@TODO: JSON close bracket
#@TODO: InfluxDB

bt.get_primary() #Check services
bt.send_data() #Enable notifications
bt.wait_notification()
