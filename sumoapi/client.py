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

    def get_basho(self, year, month):
        endpoint = f"/basho/{year}{month:02d}"
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        if "date" in response and response["date"] != "":
            return response
        else:
            return None

    def get_basho_by_id(self, id):
        endpoint = f"/basho/{id}"
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        if "date" in response and response["date"] != "":
            return response
        else:
            return None

    def get_bouts(self, year, month, day, division="Makuuchi"):
        endpoint = f"/basho/{year}{month:02d}/torikumi/{division}/{day}"
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        if response and "torikumi" in response:
            return response["torikumi"]
        else:
            return None

    def get_bouts_for_rikishi(self, api_id):
        endpoint = f"/rikishi/{api_id}/matches"
        response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        if response and "records" in response and response["total"] > 0:
            return response["records"]
        else:
            return None

    def get_next_basho(self):
        basho_date = (datetime.now() + timedelta(days=5)).strftime("%Y%m")
        endpoint = f"/basho/{basho_date}/banzuke/Makuuchi"
        try:
            response = json.loads(requests.get(f"{BASE_URL}{endpoint}").text)
        except requests.RequestException as e:
            print(f"Failed to fetch data: {e}")
            return None
        return basho_date, response["east"] + response["west"]
