import json
from datetime import datetime, timedelta

import requests

BASE_URL = "https://sumo-api.com/api"


class SumoApiClient:
    def get_all_rikishi(self):
        endpoint = "/rikishis?intai=true"
        response = requests.get(f"{BASE_URL}{endpoint}")
        return json.loads(response.text)["records"]

    def get_rikishi(self, id):
        endpoint = f"/rikishi/{id}"
        response = requests.get(f"{BASE_URL}{endpoint}")
        return json.loads(response.text)

    def get_bouts(self, year, month, day, division="Makuuchi"):
        endpoint = f"/basho/{year}{month:02d}/torikumi/{division}/{day}"
        print(f"{BASE_URL}{endpoint}")
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        if response and "torikumi" in response:
            return response["torikumi"]
        else:
            return None

    def get_next_basho(self):
        basho_date = (datetime.now() + timedelta(days=5)).strftime("%Y%m")
        endpoint = f"/basho/{basho_date}/banzuke/Makuuchi"
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        return response["east"] + response["west"]
