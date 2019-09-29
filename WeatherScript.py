from twilio.rest import Client
from ApiKeys import twilioKeys, accuWeather, numbersToText
import requests

TEMPERATURE_MESSAGES = {
    "freezing": "Oh no :( It's gonna be really cold today: {0} degrees!! The high today is {1} degrees. Make sure you really layer up and wear a good winter coat!\n\n",
    "sweaterWeather": "It's gonna get chilly today with a low of: {0} degrees! The high today is {1} degrees. Make sure you wear a sweater!\n\n",
    "sweaterLayers": "It's gonna get chilly today: {0} degrees! But it will get hotter to {1} degrees, so make sure you wear something you can take off\n\n",
    "perfectWeather": "We're gonna have great weather today: {0} degrees :) You can layer lightly if you want\n\n ",
    "warmWeather": "It's gonna be warm today! It's gonna get up to {0} degrees! Make sure you wear something light.\n\n",
    "hotWeather": "It's gonna be really hot today. It's gonna get up to {0} degrees. Don't wear anything heavy today!!\n\n"
}
PRECIPITATION_MESSAGES = {
    "precipitation": "There is a {0}% chance of {1} during the {2}\n",
    "noPrecipitation": "Yay! You don't have to worry about rain today!"
}
PRECIPITATION_MESSAGE_THRESHOLD = 30
HOURS_OF_SUN_THRESHOLD = 2

def getOutfitSuggestion(minTemp, maxTemp):
    message = ""
    # minTemp < 15
    if minTemp < 5: 
        message = TEMPERATURE_MESSAGES["freezing"].format(minTemp, maxTemp)
    elif minTemp < 15:
        if maxTemp > 20: 
           message = TEMPERATURE_MESSAGES["sweaterLayers"].format(minTemp, maxTemp)
        else:
           message = TEMPERATURE_MESSAGES["sweaterWeather"].format(minTemp, maxTemp)
    # minTemp > 15 && maxTemp > 20
    else:   
        if maxTemp > 30:
            message = TEMPERATURE_MESSAGES["hotWeather"].format(maxTemp)
        elif maxTemp > 25:
            message = TEMPERATURE_MESSAGES["warmWeather"].format(maxTemp)
        else: 
            message = TEMPERATURE_MESSAGES["perfectWeather"].format(maxTemp)
    return message
        

def getHoursOfSunMessage(hoursOfSun):
    if hoursOfSun > HOURS_OF_SUN_THRESHOLD:
        return "Amazing, we have {0} hrs of sun today!\n".format(hoursOfSun)
    else:
        return ""

def getPrecipitationMessage(dailyForecasts, dayPrecipitationProb, nightPrecipitationProb):
    message = ""
    message = addTimePrecipitationMessage(message, dailyForecasts, "Day", dayPrecipitationProb)
    message = addTimePrecipitationMessage(message, dailyForecasts, "Night", nightPrecipitationProb)
    if PRECIPITATION_MESSAGES["precipitation"] in message: 
        message += "You should probably bring an umbrella :( \n\n"
    else:
        message += PRECIPITATION_MESSAGES["noPrecipitation"] + "\n\n"
    return message

def addTimePrecipitationMessage(message, dailyForecasts, timeString, precipitationProbability):
    if (precipitationProbability > PRECIPITATION_MESSAGE_THRESHOLD):
        precType = "precipitation"
        if "PrecipitationType" in dailyForecasts[timeString]:
            precType = dailyForecasts[timeString]["PrecipitationType"]
        message += PRECIPITATION_MESSAGES["precipitation"].format(precipitationProbability, precType, timeString.lower())
    return message

def getMessagesForWeather(weatherJson): 
    dailyForecasts = weatherJson["DailyForecasts"][0]
    message = "Good morning! Your weather today: "
    weatherInfo = {
        "hoursOfSun": round(dailyForecasts["HoursOfSun"]),
        "minTemp": round(dailyForecasts['RealFeelTemperature']['Minimum']['Value']),
        "maxTemp": round(dailyForecasts['RealFeelTemperature']['Maximum']['Value']),
        "dayPrecipitationProb": dailyForecasts["Day"]["PrecipitationProbability"],
        "nightPrecipitationProb": dailyForecasts["Night"]["PrecipitationProbability"],
        "description": dailyForecasts["Day"]["LongPhrase"]
    }
    message += weatherInfo["description"] + "\n\n"
    message += getOutfitSuggestion(weatherInfo["minTemp"], weatherInfo["maxTemp"])
    message += getPrecipitationMessage(dailyForecasts, weatherInfo["dayPrecipitationProb"], weatherInfo["nightPrecipitationProb"]) 
    message += getHoursOfSunMessage(weatherInfo["hoursOfSun"])
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
    weatherURL = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/47171"
    params = {
        "apikey": accuWeather["apiKey"], 
        "details": True,
        "metric": True
    }
    
    return requests.get(url = weatherURL, params = params)
    
def main():
    response = getWeatherInfo()
    if response.status_code == 200:
        textWeather(response.json())
    else:
        print('error')

if __name__ == '__main__':
    main()