import json
import pandas as pd
import utils
import csv

# open tracking data
with open('data/20200912-NSH-ATL_886b2a47-3249-4e95-8200-f7cdd8fbbf46_SecondSpectrum_Data.jsonl') as f:
    frames = f.read().splitlines()

f.close()

# open metadata data
with open('data/20200912-NSH-ATL_886b2a47-3249-4e95-8200-f7cdd8fbbf46_SecondSpectrum_Metadata.json') as f:
    metadata = json.load(f)
    
f.close()

    
def cannotDetermineDefensiveTeam(ballLocation):
    # No data for the ball location at that time frame
    if ballLocation == None:
        return True
    # Ball is in center of end lines
    if ballLocation[0] == 0.0:
        return True
    
    # Ball is in midair
    if ballLocation[2] > utils.feetToMeters(10):
        return True
    
    return False

def playerWithinCertainYardsOfBall(playerLocation, ballLocation, yards):
    distanceInMeters = utils.distanceBetweenTwoPoints(playerLocation, ballLocation)
    return (utils.metersToYards(distanceInMeters) <= yards, distanceInMeters)
    
def isAnOffensivePlayerInPossession(offensivePlayers, ballLocation):
    for player in offensivePlayers:
        playerLocation = player["xyz"]
        if playerWithinCertainYardsOfBall(playerLocation, ballLocation, 2.0)[0]:
            return True
    return False

def getPlayersWithin5YardsOfBall(defensivePlayers, ballLocation):
    players = []
    for player in defensivePlayers:
        playerLocation = player["xyz"]
        within5Yards, distance = playerWithinCertainYardsOfBall(playerLocation, ballLocation, 5.0)
        if within5Yards:
            players.append({"playerNumber": player["number"], "distanceFromBall": distance})
    
    return players

def getPlayersMovingTowardsBall(players, nextPlayers, ballLocation):
    playersMovingTowards = []
    for player in players:
        playerNumber = player["playerNumber"]
        distance = player["distanceFromBall"]
        nextPlayer = next((item for item in nextPlayers if item["number"] == playerNumber), None)
        if nextPlayer == None:
            continue
        nextDistanceFromBall = utils.distanceBetweenTwoPoints(nextPlayer["xyz"], ballLocation)
        if nextDistanceFromBall < distance:
            playersMovingTowards.append({
                "playerNumber": playerNumber,
                "distanceFromBall": distance,
                "changeInDistanceFromBall": distance - nextDistanceFromBall
            })
    return playersMovingTowards

def getOnBallPressures(offensivePlayers, defensivePlayers, ballLocation, nextDefensivePlayers):
    if isAnOffensivePlayerInPossession(offensivePlayers, ballLocation):
        players = getPlayersWithin5YardsOfBall(defensivePlayers, ballLocation)
        players = getPlayersMovingTowardsBall(players, nextDefensivePlayers, ballLocation)
        return players
    return []

def periodIsOdd(period):
    return period % 2 != 0

onBallPressuresCsvData = []

for i in range(len(frames) - 1):
    currFrame = frames[i]
    nextFrame = frames[i+1]
    
    data = json.loads(currFrame)
    dataForNextFrame = json.loads(nextFrame)
    
    period = data["period"]
    awayIsOnLeftSide = periodIsOdd(period)
    
    # cannot determine if moving towards ball
    if dataForNextFrame["period"] != period:
        continue
    
    ballLocation = data["ball"]["xyz"]
    nextBallLocation = dataForNextFrame["ball"]["xyz"]
    
    if cannotDetermineDefensiveTeam(ballLocation):
        continue
    
    if cannotDetermineDefensiveTeam(nextBallLocation):
        continue
    
    ballX = ballLocation[0]
    ballIsOnLeftSide = ballX < 0.0
    ballIsStillOnLeftSide = nextBallLocation[0] < 0.0
    
    if ballIsOnLeftSide != ballIsStillOnLeftSide:
        continue
    
    if ballIsOnLeftSide:
        defensive = "awayPlayers" if awayIsOnLeftSide else "homePlayers"
        offensive = "homePlayers" if awayIsOnLeftSide else "awayPlayers"
    else:
        defensive = "homePlayers" if awayIsOnLeftSide else "awayPlayers"
        offensive = "awayPlayers" if awayIsOnLeftSide else "homePlayers"
        
    defensivePlayers = data[defensive]
    offensivePlayers = data[offensive]
    nextDefensivePlayers = dataForNextFrame[defensive]
    
    lastTouch = data["lastTouch"]
    if lastTouch == "away":
        if offensive != "awayPlayers":
            continue
    else:
        if offensive != "homePlayers":
            continue
    
    onBallPressures = getOnBallPressures(offensivePlayers, defensivePlayers, ballLocation, nextDefensivePlayers)
        
    for onBallPressure in onBallPressures:
        listOfPlayers = metadata[defensive]
        playerNumber = onBallPressure["playerNumber"]
        player = next((player for player in listOfPlayers if player["number"] == playerNumber), None)
        if player == None:
            continue
        
        teamName = "Nashville" if defensive == "homePlayers" else "Atlanta"
        
        onBallPressuresCsvData.append({
            "period": data["period"],
            "gameClock": utils.convertToMinuteFormat(data["gameClock"]),
            "wallClock": data["wallClock"],
            "team": teamName,
            "playerName": player["name"],
            "playerNumber": playerNumber,
            "distanceFromBall": onBallPressure["distanceFromBall"],
            "changeInDistanceFromBall": onBallPressure["changeInDistanceFromBall"]
        })

csv_columns = ["period", "gameClock", "wallClock", "team", "playerName", "playerNumber", "distanceFromBall", "changeInDistanceFromBall"]

csv_file = "on-ball-pressures.csv"

try:
    with open(csv_file, "w") as c:
        writer = csv.DictWriter(c, fieldnames=csv_columns)
        writer.writeheader()
        for data in onBallPressuresCsvData:
            writer.writerow(data)
except IOError:
    print("Error writing to CSV file.")    
    
    