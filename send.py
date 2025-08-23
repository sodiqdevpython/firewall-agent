import json
import requests

from components.GetNetworkInfo import get_traffic_info
from components.GetDeviceInfo import Device


device = Device()


def ip_lookup_online(ip):
    url = f"http://ip-api.com/json/{ip}"
    resp = requests.get(url).json()
    data = {
        "ip": ip,
        "hostname": resp.get("reverse"),
        "asn": resp.get("as"),
        "isp": resp.get("isp"),
        "country": resp.get("country"),
        "region": resp.get("regionName"),
        "city": resp.get("city"),
        "latitude": resp.get("lat"),
        "longitude": resp.get("lon")
    }
    return data


send_app = "http://10.10.111.12:8047/applications/applications/"
connect = "http://10.10.111.12:8047/applications/connections/"

results = get_traffic_info(5)
for result in results["processes"]:
    send_app_data = {
        "image_path": result["image_path"],
        "pid": result["pid"],
        "name": result["name"],
        "hash": result["hash"],
        "sent": result["sent"],
        "received": result["received"],
        "host": device.get_windows_bios_uuid()
    }

    remote_address = result["connection_list"]["1"]["remote_address"]
    local_address = result["connection_list"]["1"]["local_address"]
    more_info = {
        "remote_address": ip_lookup_online(remote_address.split(":")[0]),
        # "local_address": ip_lookup_online(local_address.split(":")[0])
        "local_address": ip_lookup_online("87.192.224.146")
    }
    send_connect_data = {
        "application_hash": result["hash"],
        "local_address": local_address,
        "remote_address": remote_address,
        "more_info": more_info
    }
    print(json.dumps(send_connect_data))
    requests.post(send_app, json=send_app_data)
    res = requests.post(connect, json=send_connect_data)
    print(res.content)
