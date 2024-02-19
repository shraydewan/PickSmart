import requests

url = "https://betsapi2.p.rapidapi.com/v1/bet365/inplay_filter"

querystring = {"sport_id":"1"}

headers = {
	"X-RapidAPI-Key": "SIGN-UP-FOR-KEY",
	"X-RapidAPI-Host": "betsapi2.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())