from components.GetNetworkInfo import get_traffic_info
import json

result = get_traffic_info(5)
print(json.dumps(result, indent=2))