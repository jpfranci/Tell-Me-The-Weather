from twilio.rest import Client
from datetime import datetime
from ApiKeys import twilioKeys, darkSky, numbersToText, latitude, longitude
import requests

TEMPERATURE_MESSAGES = {
    "freezing": "Oh no :( It's gonna be really cold today: {0} degrees at {1}!!\nThe high today is {2} degrees at {3}.\nMake sure you really layer up and wear a good winter coat!\n\n",
    "sweaterWeather": "It's gonna get chilly today with a low of: {0} degrees at {1}.\nThe high today is {2} degrees at {3}.\nMake sure you wear a sweater!\n\n",
    "sweaterLayers": "It's gonna get chilly today: {0} degrees at {1}!\nBut it will get hotter to {2} degrees at {3}, so make sure you wear something you can take off\n\n",
    "perfectWeather": "We're gonna have great weather today: {0} degrees at {1} :)\nThe low is {2} degrees at {3}.\nYou can layer lightly if you want\n\n ",
    "warmWeather": "It's gonna be warm today! It's gonna get up to {0} degrees at {1}!\nThe low is {2} degrees at {3}.\nMake sure you wear something light.\n\n",
    "hotWeather": "It's gonna be really hot today. It's gonna get up to {0} degrees at {1}!.\nThe low is {2} degrees at {3}.\nnDon't wear anything heavy today!!\n\n"
}
PRECIPITATION_MESSAGES = {
    "precipitation": "Oh no! There is a {0}% chance of {1} today\n",
    "noPrecipitation": "Yay! You don't have to worry about rain today because there is only a {0}% chance of {1} today!\n"
}
AVERAGE_TEMP_MESSAGES = {
    "averageTemp": "Average temperature from {0} to {1}: {2} degrees\n"
}
PRECIPITATION_MESSAGE_THRESHOLD = 20
HOURS_OF_SUN_THRESHOLD = 2

def getOutfitSuggestion(minTemp, maxTemp):
    message = ""
    if minTemp["temp"] < 15:
        if minTemp["temp"] < 5: 
           message = TEMPERATURE_MESSAGES["freezing"]
        elif maxTemp["temp"] > 20: 
           message = TEMPERATURE_MESSAGES["sweaterLayers"]
        else:
           message = TEMPERATURE_MESSAGES["sweaterWeather"]
        message = message.format(minTemp["temp"], minTemp["time"], maxTemp["temp"], maxTemp["time"])
    # minTemp > 15 && maxTemp > 20
    else:   
        if maxTemp["temp"] > 30:
            message = TEMPERATURE_MESSAGES["hotWeather"]
        elif maxTemp["temp"] > 25:
            message = TEMPERATURE_MESSAGES["warmWeather"]
        else: 
            message = TEMPERATURE_MESSAGES["perfectWeather"]
        message = message.format(maxTemp["temp"], maxTemp["time"], minTemp["temp"], minTemp["time"])
    return message
        
def getHoursOfSunMessage(hoursOfSun):
    if hoursOfSun > HOURS_OF_SUN_THRESHOLD:
        return "Amazing, we have {0} hrs of sun today!\n".format(hoursOfSun)
    else:
        return ""

def getPrecipitationMessage(precipitationProb, precipitationType):
    message = ""
    message = addTimePrecipitationMessage(message, precipitationType, precipitationProb)        
    return message

def addTimePrecipitationMessage(message, precipitationType, precipitationProbability):
    if precipitationProbability >= PRECIPITATION_MESSAGE_THRESHOLD:
        message += PRECIPITATION_MESSAGES["precipitation"].format(precipitationProbability, precipitationType)
        message += "You should probably bring an umbrella :( \n\n"
    else: 
        message += PRECIPITATION_MESSAGES["noPrecipitation"].format(precipitationProbability, precipitationType)
    return message

def getAlertsMessage(alerts):
    message = ""
    for alert in alerts:
        message += "{0} Alert: {1}\n {2}\n Find out more at {3}\n\n".format(alert["severity"].capitalize(), alert["title"], alert["description"], alert["uri"])
    return message

def getAverageTempMessages(averageTemps):
    message = ""
    for averageTempObj in averageTemps.values():
        message += AVERAGE_TEMP_MESSAGES["averageTemp"].format(averageTempObj["startTime"], averageTempObj["endTime"], averageTempObj["temp"])
    return message + "\n"

def getTimeFromSeconds(seconds):
    return datetime.fromtimestamp(seconds).strftime("%I:%M %p")

def getAverageTemperatures(weatherArray):
    averageTemp = sum(list(map(lambda hourlyData : hourlyData["apparentTemperature"], weatherArray))) / len(weatherArray)
    averageTemp = round(averageTemp)
    return {
        "temp": averageTemp,
        "startTime": getTimeFromSeconds(weatherArray[0]["time"]),
        "endTime": getTimeFromSeconds(weatherArray[-1]["time"])
    }

def getAverageTemperaturesForMorningToEvening(hourlyData):
    averageTemps = {}
    averageTemps["morning"] = getAverageTemperatures(hourlyData[0:6])
    averageTemps["afternoon"] = getAverageTemperatures(hourlyData[6:12])
    averageTemps["evening"] = getAverageTemperatures(hourlyData[12:18])
    return averageTemps

def getMessagesForWeather(weatherJson): 
    weatherData = weatherJson["daily"]["data"][0]
    hourlyData = weatherJson["hourly"]["data"]
    message = "Good morning! This is your weather for today: {0}\n\n".format(weatherData["summary"])
    weatherInfo = {
        "minTemp": {
            "temp": round(weatherData["apparentTemperatureLow"]), 
            "time": getTimeFromSeconds(weatherData["apparentTemperatureLowTime"])
        },
        "maxTemp": {
            "temp": round(weatherData['apparentTemperatureHigh']),
            "time": getTimeFromSeconds(weatherData["apparentTemperatureHighTime"])
        },
        "precipitationProb": round(weatherData['precipProbability'] * 100),
        "precipType": weatherData.get('precipType', 'precipitation'),
        "alerts": weatherData.get("alerts", []),
        "averageTempsThroughDay": getAverageTemperaturesForMorningToEvening(hourlyData)
    }
    message += getOutfitSuggestion(weatherInfo["minTemp"], weatherInfo["maxTemp"])
    message += getAverageTempMessages(weatherInfo["averageTempsThroughDay"])
    message += getPrecipitationMessage(weatherInfo["precipitationProb"], weatherInfo["precipType"]) 
    message += getAlertsMessage(weatherInfo["alerts"])
    return message
    
def textWeather(weatherJson):
    client = Client(twilioKeys["accountSid"], twilioKeys["authToken"])
    messageToText = "\n\n" + getMessagesForWeather(weatherJson)
    for number in numbersToText:
        client.messages.create(
            to= number,
            from_ = twilioKeys["twilioNumber"],
            body = messageToText
        )

def getWeatherInfo(): 
    weatherURL = "https://api.darksky.net/forecast/{0}/{1},{2}".format(darkSky["apiKey"], latitude, longitude)
    params = {
        "exclude": "currently,minutely",
        "units": "si"
    }
    return requests.get(url = weatherURL, params = params)
    
def main():
    response = getWeatherInfo()
    if response.status_code == 200:
        textWeather(response.json())
    else:
        print('Error when trying to get weather info')

if __name__ == '__main__':
    main()