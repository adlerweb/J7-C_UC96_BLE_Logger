# J7-C_UC96_BLE_Logger
Bluetooth Low Energy Data logging for J7-C/UC96 USB Digital Power Testers. It should work with all the digital testers sharing the atorch protocol - see [here](https://github.com/CursedHardware/atorch-console/blob/master/README.md#supported-meter) for a list of potentially supported devices. Tested on J7-C and UD18 meters.

## Installation

Requires [gattlib](https://github.com/labapart/gattlib).

### Warning

Sadly there has been an API change with newer bluetooth adapters (HCI5) which [isn't supported by gattlib yet](https://github.com/oscaracena/pygattlib/issues/31). If you see a `Set scan parameters failed` error, your adapter may be using >=HCI5 and not be supported until the code has been ported to dbus/bluez or gattlib is updated. You can still run the script, though, you just need to bypass the scan by passing the `--device` option (or its shorthand `-d`) when running it.

## Usage

Just start the script to show the measurements of the first found J7-C on screen.

```
usage: j7c-gat.py [-h] [-v | -q] [-d DEVICE] [-w] [-r] [-H HCI]
                  [-T SCANTIME] [-m {Text,CSV,JSON,RAW,InfluxDB}]
                  [-O OUTPUT] [-a] [--csv-delimiter CSV_DELIMITER]
                  [--csv-no-header] [--json-pretty] [--raw-header]
                  [--raw-pretty]

Receive measurement values from a J7-C USB power monitor using BLE

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity. Repeat for higher
                        verbosity (max. 5)
  -q, --quiet           suppress non-data output messages

Device control:
  -d DEVICE, --device DEVICE
                        target device MAC address. If no address is given
                        the first compatible device found will be used
  -w, --wait            wait for device to appear
  -r, --reconnect       wait and reconnect after losing connection
  -H HCI, --hci HCI     HCI used for communication. Defaults to hci0
  -T SCANTIME, --scantime SCANTIME
                        Time in seconds to scan for devices. Defaults to 2
                        Seconds

Output options:
  -m {Text,CSV,JSON,RAW,InfluxDB}, --mode {Text,CSV,JSON,RAW,InfluxDB}
                        output type
  -O OUTPUT, --output OUTPUT
                        output file, device or network address
                        ([tcp|udp]://[host_or_ip]:port)
  -a, --append          append output if it is a file

Output options for CSV:
  --csv-delimiter CSV_DELIMITER
                        CSV delimiter. Default: ';'
  --csv-no-header       Omit CSV header

Output options for JSON:
  --json-pretty         Use pretty-print for JSON Output

Output options for RAW:
  --raw-header          Add address header
  --raw-pretty          Use pretty-print for RAW Output
```

## Docker

The command can be run via docker or docker compose in case you have trouble installing the dependencies. Note that the container needs to run in privileged mode!

  docker build . -t j7c
  docker run -i --rm --net=host --privileged -v /dev:/dev j7c --help

## More

The decoder was reverse engineered by myself. There are now a few more comprehensive protocol descriptions available, so if you want to work with these devices yourself you might want to have a look over there:

* https://github.com/NiceLabs/atorch-console/blob/master/docs/protocol-design.md
* https://github.com/syssi/esphome-atorch-dl24/blob/main/docs/protocol-design.md
* https://github.com/msillano/UD18-protocol-and-node-red/blob/master/UD18_protocol.txt
