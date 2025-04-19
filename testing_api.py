import requests

url = "https://jsearch.p.rapidapi.com/search?query=python+developer&location=remote"

querystring = {"job_title":"nodejs developer","location":"new york","location_type":"ANY","years_of_experience":"ALL"}

headers = {
	"x-rapidapi-key": "3bd0001341msh0296f7258263cfdp1f0d16jsn719afa9302fb",
	"x-rapidapi-host": "jsearch.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())