import os
import requests
import random
import asyncio
import sqlite3
import discord
from discord.ext import commands
import re
import pandas as pd
import time

with open("token.txt", "r") as f:
	TOKEN = f.read().rstrip()

bot = commands.Bot(command_prefix=">", intents=discord.Intents.all())


# sqlite3

con = sqlite3.connect("pokemon.db")
cur = con.cursor()


# df / pandas / csv

df = pd.read_csv("chances_edited.csv")



# api commands

def get_pokemon_api(id):
	try:
		response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{id}")
		resp = response.json()
		return resp
	except:
		print(f"Sorry, {id} is not a valid pokemon.")
		return

def get_species_api(id):
	try:
		response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{id}")
		resp = response.json()
		return resp 
	except:
		print(f"Sorry, {id} is not a valid species.")
		return


@bot.event
async def on_ready():
	print(f"Logged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n")


def sanitize_name(name):
	name = name.lower()
	name = re.sub('[^0-9a-zA-Z]+', '-', name)
	name = re.sub(r'(-)\1+', r"\1", name)

	return name

# sanitize name for display
def dsanitize(name):
	name = name.lower()
	name = name.capitalize()

	excl = ["ordinary"]
	parenth = ["land"]

	n = name.split("-")
	if len(n) > 1:
		if n[1] in excl:
			return n[0] 
		elif n[1] in parenth:
			return n[0] + " (" + n[1] + ")" 
		else:
			n[1] = n[1].capitalize()

	return " ".join(n)

def getNamesFromSpeciesJSON(j):
	nameList = []
	nameList.append(next(item for item in j["names"] if item["language"]["name"] == "en")["name"])
	for lang in j["names"]:
		censored = ["zh-Hans", "zh-Hant"]
		if lang["name"] not in nameList and lang["language"]["name"] not in censored:
			nameList.append(lang["name"])

	nameList.sort()

	return nameList


@bot.command(name="d")
async def dex(ctx, *n):
	name=sanitize_name(" ".join(map(str, n)))
	
	resp = get_pokemon_api(name)

	pokeId = resp["id"]

	if pokeId > 908:
		await ctx.send(f"Sorry, it looks like {name} is a dumb newgen =D try a better poke")
		return

	# speciesURL = resp["species"]["url"]
	# speciesResponse = requests.get(speciesURL)
	# speciesJSON = speciesResponse.json()

	speciesJSON = get_species_api(name)


	embed = discord.Embed(
		title=f"#{pokeId} — {resp['name'].capitalize()}", 
		color=discord.Color.gold(), 
		description=[d["flavor_text"] for d in speciesJSON["flavor_text_entries"] if d["language"]["name"] == "en"][-1].replace('\n', ' '))
	# alternatively:
	# embed.set_image(url=f"https://raw.githubusercontent.com/HybridShivam/Pokemon/382adce67ba7f4f765cee378141356560424c031/assets/images/{str(pokeId).zfill(3)}.png")
	embed.set_image(url=f"https://cdn.poketwo.net/images/{pokeId}.png")

	# evolution
	# types
	embed.add_field(name="Types", value="\n".join(d["type"]["name"].capitalize() for d in resp["types"]))
	
	# region
	regions = {"I": "Kanto", "II": "Johto", "III": "Hoenn", "IV": "Sinnoh", "V": "Unova", "VI": "Kalos", "VII": "Alola", "VIII": "Galar", "IX": "Paldea"}

	embed.add_field(name="Region", value=f'{regions[speciesJSON["generation"]["name"].split("-")[1].upper()]}')

	# catchable
	embed.add_field(name="Catchable", value="Yes")

	# base stats
	embed.add_field(name="Base Stats", value=f'**HP:** {resp["stats"][0]["base_stat"]}\n**Attack:** {resp["stats"][1]["base_stat"]}\n**Defense:** {resp["stats"][2]["base_stat"]}\n**Sp. Atk:** {resp["stats"][3]["base_stat"]}\n**Sp. Def:** {resp["stats"][4]["base_stat"]}\n**Speed:** {resp["stats"][5]["base_stat"]}')

	# names
	# maybe add flags?
	embed.add_field(name="Names", value="\n".join(d.capitalize() for d in getNamesFromSpeciesJSON(speciesJSON)))

	# appearance
	embed.add_field(name="Appearance", value=f"Height: {resp['height']/10} m\nWeight: {resp['weight']/10} kg")

	# footnote
	embed.set_footer(text="You've caught 0 of this pokemon!")

	await ctx.send(embed=embed)

	# await ctx.send(f"https://cdn.poketwo.net/images/{pokeId}.png")


def get_num_pokes(userID):
	res = cur.execute(f"SELECT SUM(CASE WHEN userID = {userID} THEN 1 ELSE 0 END) FROM pokemon").fetchall()
	return res[0][0]

def catch_pokemon(userID, poke, level):
	ti = round(time.time() * 1000) # caughtTime
	# caughtID = userID
	# userID = userID
	pokeID = get_num_pokes(userID) + 1
	xp = 0

	natures = ["hardy", "lonely", "adamatant", "naughty", "brave", "bold", "docile", "impish", "lax", "relaxed", "modest", "mild", "bashful", "rash", "quiet", "calm", "gentle", "careful", "quirky", "sassy", "timid", "hasty", "jolly", "naive", "serious"]
	nature = random.choice(natures)

	hp = random.randint(0,31) 
	attack = random.randint(0,31)
	defense = random.randint(0,31)
	spatk = random.randint(0,31)
	spdef = random.randint(0,31)
	speed = random.randint(0,31)

	total = round((hp+attack+defense + spatk +spdef+ speed)*100/(31*6), 2)

	cur.execute(f"INSERT INTO pokemon VALUES ({ti}, {userID}, {userID}, {pokeID}, {poke}, {level}, {xp}, '{nature}', {hp}, {attack}, {defense}, {spatk}, {spdef}, {speed}, {total})")
	# cur.execute(f"INSERT INTO pokemon ")
	con.commit()

	# success
	return True


@bot.command(name="s")
async def spawn(ctx):

	pokeId = 10000
	while pokeId > 908:
		ri = random.randint(0, 1005828) # note this number is determined by sum(chance)

		pokeId = df[df['end'].gt(ri)].index[0]
		print(pokeId)

	# response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokeId}")
	# resp = response.json()

	resp = get_pokemon_api(pokeId)


	embed = discord.Embed(
		title="A wild pokémon has appeared!",
		color=discord.Color.gold(),
		description="Guess the pokémon and type the name to catch it!")

	# embed.set_image(url=f"https://raw.githubusercontent.com/HybridShivam/Pokemon/382adce67ba7f4f765cee378141356560424c031/assets/images/{str(pokeId).zfill(3)}.png")
	embed.set_image(url=f"https://cdn.poketwo.net/images/{pokeId}.png")

	await ctx.send(embed=embed)

	# check function

	def check(msg):
		return msg.channel == ctx.channel and sanitize_name(msg.content) == sanitize_name(resp["name"])

	try:
		msg = await bot.wait_for("message", check=check, timeout=300)
	except:
		await ctx.send(f"The wild {resp['name'].capitalize()} fled.")
		return

	lvl = random.randint(0, 50)

	await ctx.send(f"Congratulations {msg.author.mention}! You caught a level {lvl} {resp['name'].capitalize()}!")

	catch_pokemon(msg.author.id, pokeId, lvl)

@bot.command(aliases=["p"])
async def pokemon(ctx):
	res = cur.execute(f"SELECT DENSE_RANK() OVER (ORDER BY pokeID ASC) as pokeID, poke, level, total FROM pokemon WHERE userID = {ctx.message.author.id}").fetchall()

	print(res)


	desc = ""

	for i in range(min(len(res), 20)):
		pokemonJSON = get_pokemon_api(res[i][1])
		if desc != "":
			desc += "\n"
		desc += f"`{str(res[i][0]).zfill(4)}`   **{dsanitize(pokemonJSON['name'])}**  |  Lvl. {res[i][2]}  |  {res[i][3]}%"

	embed = discord.Embed(
		title="Your pokemon",
		color=discord.Color.gold(),
		description=desc)

	embed.set_footer(text=f"Showing entries 1-{min(len(res), 20)} of {len(res)}.")

	await ctx.send(embed=embed)


bot.run(TOKEN)
