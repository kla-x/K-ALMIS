import requests
import json

url = 'https://api.abuseipdb.com/api/v2/check'

querystring = {
    'ipAddress': '196.96.24.54',
    'maxAgeInDays': '90'
}

headers = {
    'Accept': 'application/json',
    'Key': '1ad2de736e538768cf0b63d8a3a488b76fd08fc6362b919b65e20be28422ec9c0a518d26415356d0'
}

response = requests.request(method='GET', url=url, headers=headers, params=querystring)
decodedResponse = json.loads(response.text)
print(json.dumps(decodedResponse, sort_keys=True, indent=4))
