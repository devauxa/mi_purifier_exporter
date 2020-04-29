import time
import json
import sys
import os

from miio import airpurifier_miot, exceptions

# noinspection PyProtectedMember
from prometheus_client import start_http_server, Gauge, Info
from aqi.algos.epa import AQI, Decimal, ROUND_HALF_EVEN, POLLUTANT_PM25

status = None

aqi = Gauge('mi_purifier_aqi', 'AQI from Purifier', ['name'])
temp = Gauge('mi_purifier_temp', 'Temperature from Purifier', ['name'])
humidity = Gauge('mi_purifier_humidity', 'humidity from Purifier', ['name'])
filter_life_remaining = Gauge('mi_purifier_filter_life', 'Filter life in percent from Purifier', ['name'])
mode = Gauge('mi_purifier_status', 'Status of Purifier as labels', ['name', 'mode', 'filterType'])
motor_speed= Gauge('mi_purifier_motor_speed', 'motor_speed from Purifier', ['name'])
filter_life_used_time =  Gauge('mi_purifier_filter_used_time', 'Filter life used in time from Purifier', ['name'])
purify_volume = Gauge('mi_purifier_volume_purified', 'volume purify from Purifier', ['name'])
pm25 =  Gauge('mi_purifier_pm25', 'pm25 from Purifier', ['name'])


def exit_with_error(error):
    sys.exit(error)


def aqi_to_pm25(aqi_value):
    aqi_idx = None
    aqilo, aqihi = None, None

    for key, range in enumerate(AQI.piecewise['aqi']):
        if range[0] <= aqi_value <= range[1]:
            aqi_idx = key
            (aqilo, aqihi) = range
            break

    if aqi_idx is None:
        raise Exception("invalid aqi")

    (pm25lo, pm25hi) = AQI.piecewise['bp'][POLLUTANT_PM25][aqi_idx]
    pm25val = (((Decimal(aqi_value) - aqilo) / (aqihi - aqilo)) * (pm25hi - pm25lo)) + pm25lo

    return pm25val.quantize(Decimal('1.'), rounding=ROUND_HALF_EVEN)



if __name__ == '__main__':
    port_number = 8000

    if len(sys.argv) == 2 and os.path.exists(sys.argv[1]) is True:
        with open(sys.argv[1]) as f:
            purifiers = json.load(f)
    elif "TOKEN" in os.environ:
        purifiers = json.loads(os.environ["TOKEN"])
    else:
        exit_with_error("Plz, set json path on argv, or use TOKEN environ")


    if len(purifiers["purifiers"]) < 1:
        exit_with_error("No purifiers found in JSON File")

    for purifier in purifiers["purifiers"]:
        purifier["object"] = airpurifier_miot.AirPurifierMiot(ip=purifier["ip"], token=purifier["token"])

    if len(sys.argv) > 2:
        port_number = int(sys.argv[2])
    start_http_server(port_number)

    while True:
        time.sleep(1)
        for purifier in purifiers["purifiers"]:
            try:
                status = purifier["object"].status()
                aqi.labels(purifier["name"]).set(status.aqi)
                temp.labels(purifier["name"]).set(status.temperature)
                humidity.labels(purifier["name"]).set(status.humidity)
                filter_life_remaining.labels(purifier["name"]).set(status.filter_life_remaining)
                mode.labels(purifier["name"], status.mode.name, status.filter_type.name)\
                    .set(1 if status.power == "on" else 0)
                purify_volume.labels(purifier["name"]).set(status.purify_volume)
                motor_speed.labels(purifier["name"]).set(status.motor_speed)
                pm25.labels(purifier["name"]).set(aqi_to_pm25(status.aqi))
                filter_life_used_time.labels(purifier["name"]).set(status.use_time)
            except TypeError as error:
                pass
            except exceptions.DeviceException as error:
                pass
            except OSError as error:
                pass
