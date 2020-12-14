import math

def feetToMeters(feet):
    return feet*0.3048

def yardsToMeters(yards):
    return yards*0.9144

def metersToYards(meters):
    return meters*1.09361

def distanceBetweenTwoPoints(x, y):
    x1, y1 = x[0], x[1]
    x2, y2 = y[0], y[1]
    return math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))

def convertToMinuteFormat(seconds): 
    seconds = seconds % (24 * 3600)  
    hour = seconds // 3600 
    seconds %= 3600
    minutes = seconds // 60 
    seconds %= 60
      
    return "%d:%02d:%02d" % (hour, minutes, seconds) 
      
