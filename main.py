import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import requests
import datetime
import sqlite3
import os
import asyncio
import random
from bs4 import BeautifulSoup

class Config:
    def __init__(self, fileName):
        self.fileName = fileName
        self.data = self.loadFile()
        self.token = self.data["Token"]
        self.strawpollUser = self.data["Strawpoll User"]
        self.strawpollToken = self.data["Strawpoll Token"]
        self.wikiUrl = self.data["wikiUrl"]
    
    def createFile(self):
        with open(self.fileName, "w") as f:
            json.dump({"Token": "", "Strawpoll User": "", "Strawpoll Token": "","wikiUrl":"https://failyv.fandom.com/fr/wiki/"}, f, indent=4)

    def loadFile(self):
        try:
            with open(self.fileName, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.createFile()
            print("Created config file")
            print("Please fill in the config file")
            exit()

    def setKey(self, key, value):
        self.data[key] = value
        self.saveFile()

    def getKey(self, key):
        return self.data[key]

    def saveFile(self):
        with open(self.fileName, "w") as f:
            json.dump(self.data, f, indent=4)

class DataLogs:
    def __init__(self, fileName):
        self.fileName = fileName
        req = "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, command TEXT, date TEXT)"
        self.conn = sqlite3.connect(self.fileName)
        self.cursor = self.conn.cursor()
        self.cursor.execute(req)
        self.conn.commit()
    
    def addLog(self, user_id, command):
        req = "INSERT INTO logs (user_id, command, date) VALUES (?, ?, ?)"
        self.cursor.execute(req, (user_id, command, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        self.conn.commit()

    def getLogs(self):
        req = "SELECT * FROM logs"
        self.cursor.execute(req)
        return self.cursor.fetchall()

    def getLogsByUser(self, user_id):
        req = "SELECT * FROM logs WHERE user_id=?"
        self.cursor.execute(req, (user_id,))
        return self.cursor.fetchall()

    def getLogsByCommand(self, command):
        req = "SELECT * FROM logs WHERE command=?"
        self.cursor.execute(req, (command,))
        return self.cursor.fetchall()

    def getLogsByDate(self, date):
        req = "SELECT * FROM logs WHERE date=?"
        self.cursor.execute(req, (date,))
        return self.cursor.fetchall()

    def getLogsByUserAndCommand(self, user_id, command):
        req = "SELECT * FROM logs WHERE user_id=? AND command=?"
        self.cursor.execute(req, (user_id, command))
        return self.cursor.fetchall()

    def getLogsByUserAndDate(self, user_id, date):
        req = "SELECT * FROM logs WHERE user_id=? AND date=?"
        self.cursor.execute(req, (user_id, date))
        return self.cursor.fetchall()

    def getLogsByCommandAndDate(self, command, date):
        req = "SELECT * FROM logs WHERE command=? AND date=?"
        self.cursor.execute(req, (command, date))
        return self.cursor.fetchall()

    def getLogsByUserAndCommandAndDate(self, user_id, command, date):
        req = "SELECT * FROM logs WHERE user_id=? AND command=? AND date=?"
        self.cursor.execute(req, (user_id, command, date))
        return self.cursor.fetchall()
    
    def getLastCommand(self, user_id):
        req = "SELECT command,date FROM logs WHERE user_id=? ORDER BY id DESC LIMIT 10"
        self.cursor.execute(req, (user_id,))
        return self.cursor.fetchall()
    
    def getNbCommand(self, user_id):
        req = "SELECT COUNT(*) FROM logs WHERE user_id=?"
        self.cursor.execute(req, (user_id,))
        return self.cursor.fetchone()[0]

def getIdRightPoll(default=False):
    if default:
        return "05ZdWWD1Qg6"
    else:            
        url = f"https://api.strawpoll.com/v3/users/{user}/polls"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": token
        }
        response = requests.request("GET", url, headers=headers)
        data=json.loads(response.text)
        for i in range(len(data['data'])):
            if data['data'][i]['poll_config']['deadline_at'] == None:
                continue
            if data['data'][i]['poll_config']['deadline_at'] > datetime.datetime.now().timestamp():
                return data['data'][i]['id']
        return data['data'][len(data['data'])-1]['id']

def getPollResult(id):
    url = "https://api.strawpoll.com/v3/polls/"+str(id)+"/results"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": token
    }
    response = requests.request("GET", url, headers=headers)
    data=json.loads(response.text)
    return data

def getNameByIndex(data,index):
    return data["poll_options"][index]["value"]

def getUserVote(data,user):
    for i in range(len(data["poll_participants"])):
        nameUpper = data["poll_participants"][i]["name"].upper()
        userUpper = user.upper()
        if nameUpper == userUpper:
            voteList=data["poll_participants"][i]["poll_votes"]
            if len(voteList) == 0:
                return None
            else:
                votedListName=[]
                for i in range(len(voteList)):
                    if voteList[i] == 1:
                        votedListName.append(getNameByIndex(data,i))
                return votedListName
    return None

def getMostVoted(data):
    listOfVotes = []
    for i in range(len(data["poll_options"])):
        listOfVotes.append(data["poll_options"][i]["vote_count"])
    maxVotes = max(listOfVotes)
    maxIndices = [i for i, j in enumerate(listOfVotes) if j == maxVotes]
    if len(maxIndices) == 1:
        mostVoted = [getNameByIndex(data, maxIndices[0])]
    else:
        mostVoted = []
        for idx in maxIndices:
            mostVoted.append(getNameByIndex(data, idx))
    return mostVoted

def getNbVotes(data):
    listOfVotes = []
    for i in range(len(data["poll_options"])):
        listOfVotes.append(data["poll_options"][i]["vote_count"])
    return listOfVotes

def getVoteCount(data,name):
    for i in range(len(data["poll_options"])):
        if data["poll_options"][i]["value"] == name:
            return data["poll_options"][i]["vote_count"]
    return None

def getSortedLeaderBoard(data):
    listOfVotes = []
    for i in range(len(data["poll_options"])):
        listOfVotes.append(data["poll_options"][i]["vote_count"])
    listOfNames = []
    for i in range(len(data["poll_options"])):
        listOfNames.append(data["poll_options"][i]["value"])
    listOfTuples = []
    for i in range(len(data["poll_options"])):
        listOfTuples.append((listOfNames[i],listOfVotes[i]))
    listOfTuples.sort(key=lambda x: x[1], reverse=True)
    listOfNames = []
    for i in range(len(data["poll_options"])):
        listOfNames.append(listOfTuples[i][0])
    listOfVotes = []
    for i in range(len(data["poll_options"])):
        listOfVotes.append(listOfTuples[i][1])
    listReturn = []
    listReturn.append(listOfNames)
    listReturn.append(listOfVotes)
    return listReturn

def buildPollUrl(id):
    return "https://strawpoll.com/polls/"+id

def ListToString(s):  
    str1 = ""  
    for ele in s:  
        str1 += ele + ", "  
    return str1[:-2]

def getGithubInfo():
    url = "https://api.github.com/repos/Wiibleyde/NewStrawpollBot"
    response = requests.request("GET", url)
    data=json.loads(response.text)
    return data

def getGithubLastRelease():
    url = "https://api.github.com/repos/Wiibleyde/NewStrawpollBot/releases/latest"
    response = requests.request("GET", url)
    data=json.loads(response.text)
    return data

def getGithubLastCommit():
    url = "https://api.github.com/repos/Wiibleyde/NewStrawpollBot/commits"
    response = requests.request("GET", url)
    data=json.loads(response.text)
    return data[0]

def getWikiPage(search):
    url = config.wikiUrl+"Spécial:Recherche?query=+"+search.replace(" ","+")
    response = requests.request("GET", url)
    data=response.text
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.find_all('a'):
        if link.get('class') != None:
            if link.get('class')[0] == "unified-search__result__link":
                return link.get('href')
    return None

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot is ready")
    CheckFcChange.start()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        print(f"Commands: {synced}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="sondage", description="Affiche le sondage en cours")
async def sondage(interaction: discord.Interaction):
    logs.addLog(interaction.user.id, "sondage")
    id = getIdRightPoll()
    if id == None:
        await interaction.response.send_message("Aucun sondage en cours")
    else:
        data = getPollResult(id)
        embed = discord.Embed(title="Les FC de Georgia", description="Dernier sondage en cours", color=0x00ff00)
        embed.add_field(name="Lien", value=buildPollUrl(id), inline=False)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="premier", description="Affiche le premier du sondage en cours")
async def premier(interaction: discord.Interaction):
    logs.addLog(interaction.user.id, "premier")
    id = getIdRightPoll()
    if id == None:
        await interaction.response.send_message("Aucun sondage en cours")
    else:
        data = getPollResult(id)
        mostVoted = getMostVoted(data)
        if len(mostVoted) == 1:
            embed = discord.Embed(title="Les FC de Georgia", description="Le premier est "+mostVoted[0]+"\n [Page wiki]("+getWikiPage(mostVoted)+")")
            embed.add_field(name="Nombre de votes", value=getVoteCount(data,mostVoted[0]), inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Les FC de Georgia", description="Les premiers avec "+str(getVoteCount(data,mostVoted[0]))+" votes", color=0x00ff00)
            for i in range(len(mostVoted)):
                embed.add_field(name=mostVoted[i], value=f"([page wiki]({getWikiPage(mostVoted[i])}))", inline=False)
            await interaction.response.send_message(embed=embed)

@bot.tree.command(name="classement", description="Affiche le classement du sondage en cours")
async def classement(interaction: discord.Interaction):
    logs.addLog(interaction.user.id, "classement")
    id = getIdRightPoll()
    if id == None:
        await interaction.response.send_message("Aucun sondage en cours")
    else:
        data = getPollResult(id)
        embed = discord.Embed(title="Les FC de Georgia", description="Classement du sondage en cours", color=0x00ff00)
        id = getIdRightPoll(False)
        data = getPollResult(id)
        sondage=getSortedLeaderBoard(data)
        people=sondage[0]
        votes=sondage[1]
        strToField=""
        for i in range(len(sondage[0])):
            strToField=strToField+f"{i+1}. {people[i]} : {votes[i]} votes\n"
        embed.add_field(name="Résultat", value=strToField, inline=False)
        embed.add_field(name="Lien", value=buildPollUrl(id), inline=False)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="utilisateur", description="Affiche les votes d'un utilisateur")
async def utilisateur(interaction: discord.Interaction, user: discord.Member = None):
    logs.addLog(interaction.user.id, "utilisateur")
    id = getIdRightPoll()
    if id == None:
        await interaction.response.send_message("Aucun sondage en cours")
    if user == None:
        user = interaction.user.name
        try:
            valueToSend=ListToString(getUserVote(getPollResult(getIdRightPoll()),user))
            embed = discord.Embed(title="Les FC de Georgia", description=f"Votes de {user}", color=0x00ff00)
            embed.add_field(name="Votes", value=valueToSend, inline=False)
            await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("Cet utilisateur n'a pas voté")
    else:
        try:
            valueToSend=ListToString(getUserVote(getPollResult(getIdRightPoll()),user.name))
            embed = discord.Embed(title="Les FC de Georgia", description=f"Votes de {user.name}", color=0x00ff00)
            embed.add_field(name="Votes", value=valueToSend, inline=False)
            await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("Cet utilisateur n'a pas voté")

@bot.tree.command(name="best", description="Affiche le meilleur FC")
async def best(interaction: discord.Interaction, user: discord.Member = None):
    logs.addLog(interaction.user.id, "best")
    if user == None:
        user=interaction.user
    data=getPollResult(getIdRightPoll(False))
    listPeople=getSortedLeaderBoard(data)[0]
    listOfUserVotes=getUserVote(getPollResult(getIdRightPoll()),user.name)
    if listOfUserVotes == None:
        randomPerson=listPeople[random.randint(0,len(listPeople)-1)]
    else:
        randomPerson=listOfUserVotes[random.randint(0,len(listOfUserVotes)-1)]
    embed = discord.Embed(title=f"Le best de {user.name}", description=f"{randomPerson} est le meilleur", color=0xeee657)
    embed.add_field(name="Lien", value=buildPollUrl(getIdRightPoll()), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Affiche les informations du bot")
async def info(interaction: discord.Interaction):
    logs.addLog(interaction.user.id, "a propos")
    embed = discord.Embed(title=bot.user.name, description="Bot créé par Wiibleyde#2834", color=0x00ff00)
    releaseInfo = getGithubLastRelease()
    embed.set_thumbnail(url=releaseInfo['author']['avatar_url'])
    embed.add_field(name="Version", value=releaseInfo['tag_name'], inline=False)
    embed.add_field(name="Date de sortie", value=datetime.datetime.strptime(releaseInfo['published_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Lien", value=releaseInfo['html_url'], inline=False)
    embed.set_footer(text="Wiibleyde#2834")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userstat", description="Affiche les statistiques d'un utilisateur")
async def userstat(interaction: discord.Interaction, userid: int = None):
    logs.addLog(interaction.user.id, "userstat")
    if userid == None:
        userid = interaction.user.id
    embed = discord.Embed(title="Statistiques", description=f"Statistiques de {userid}", color=0x00ff00)
    embed.add_field(name="Nombre de commandes", value=logs.getNbCommand(userid), inline=False)
    embed.add_field(name="10 dernières commandes", value=logs.getLastCommand(userid), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="wiki", description="Affiche la page wiki")
async def wiki(interaction: discord.Interaction, search: str):
    logs.addLog(interaction.user.id, "wiki")
    embed = discord.Embed(title="Wiki", description=f"Résultat de la recherche {search}", color=0x00ff00)
    embed.add_field(name="Lien", value=getWikiPage(search), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Affiche l'aide")
async def help(interaction: discord.Interaction):
    logs.addLog(interaction.user.id, "help")
    embed = discord.Embed(title="Les FC de Georgia", description="Pour utiliser les commandes, il faut taper / et discord va vous proposer les commandes disponibles", color=0x00ff00)
    embed.add_field(name="Commandes", value="sondage : Renvoie le dernier sondage des FC valide\nclassement : Renvoie le classement du sondage en cours\nutilisateur : Renvoie les votes d'un utilisateur\nbest : Renvoie le meilleur FC\npremier : Renvoie le premier FC\ninfo : Renvoie les informations du bot\nwiki : Renvoie la page wiki\nhelp : Renvoie l'aide", inline=False)
    await interaction.response.send_message(embed=embed)
    
@tasks.loop(seconds=0.5)
async def CheckFcChange():
    print("Checking FC change")
    await bot.wait_until_ready()
    while not bot.is_closed():
        waitTime = 60
        minChangeTime = 10
        try:
            id = getIdRightPoll(False)
            data = getPollResult(id)
            mostVoted = getMostVoted(data)
            if len(mostVoted) == 0:
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Aucun vote"))
                await asyncio.sleep(waitTime)
                continue
            if len(mostVoted) == 1:
                numberOfVote = getVoteCount(data,mostVoted[0])
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=mostVoted[0]+" ("+str(numberOfVote)+" votes)"))
                await asyncio.sleep(waitTime)
                continue
            numberOfLoop = (waitTime/len(mostVoted))//minChangeTime
            changeTime = waitTime/(len(mostVoted)*numberOfLoop)
            for i in range(int(numberOfLoop)):
                for j in range(len(mostVoted)):
                    numberOfVote = getVoteCount(data,mostVoted[j])
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=mostVoted[j]+" ("+str(numberOfVote)+" votes)"))
                    await asyncio.sleep(changeTime)
        except Exception as e:
            string = "Erreur : " + str(e)
            print(string)
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=string))
            await asyncio.sleep(3)

if __name__ == "__main__":
    config = Config("config.json")
    token = config.getKey("Strawpoll Token")
    user = config.getKey("Strawpoll User")
    logs = DataLogs("logs.db")
    bot.run(config.getKey("Token"))
