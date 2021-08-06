import discord
from discord.ext import commands, tasks
import json
import os
import random
import math
import datetime

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        print("send bot help")
        for cog in mapping:
            await self.get_destination().send(f"{cog.qualified_name}: {[command.name for command in mapping[cog]]}")

    async def send_cog_help(self, cog):
        print("send cog help")
        await self.get_destination().send(f"{cog.qualified_name}:{[command.name for command in cog.get_commands()]}")

    async def send_group_help(self, group):
        print("send group help")
        await self.get_destination().send(f"{group.name}:{[command.name for index, command in enumerate(group.commands)]}")

    async def send_command_help(self, command):
        print("send command help")
        await self.get_destination().send(command.name)

#custom server prefixes
def get_prefix(client, message):
    with open("prefixes.json", "r") as f:
        try:
            prefixes = json.load(f)
        except:
            prefixes = {}
    try:
        return prefixes[str(message.guild.id)]
    except:
        return '.'


intents = discord.Intents(messages = True, guilds = True, reactions = True, members = True, presences = True)
client = commands.Bot(command_prefix = get_prefix, intents = intents)#, help_command = CustomHelpCommand()

#load cogs
@client.command()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")

@client.command()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")



#prefix handling
@client.event #add default prefix when server added
async def on_guild_join(guild):
    with open("prefixes.json", "r") as f:
        try:
            prefixes = json.load(f)
        except:
            prefixes = {}

    prefixes[str(guild.id)] = '/'

    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)

@client.event #delete server prefix when bot removed from server
async def on_guild_remove(guild):
    with open("prefixes.json", "r") as f:
        try:
            prefixes = json.load(f)
        except:
            prefixes = {}

    prefixes.pop(str(guild.id))

    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)

@client.command() #change prefix
async def changeprefix(ctx, prefix):
    with open("prefixes.json", "r") as f:
        try:
            prefixes = json.load(f)
        except:
            prefixes = {}
        # print(f"prefixes: {prefixes}")

    prefixes[f"{ctx.guild.id}"] = prefix

    with open("prefixes.json", "w+") as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(f"Prefix changed to: {prefix}")

#some error handling
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command doesnt exist!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please pass in all required arguments!')


#money stuff


class AmountConverter(commands.Converter):
        async def convert(self, ctx, argument):
            amount = argument[:-1]
            unit = argument[-1]
            print(f"amount, unit: {amount}, {unit}")

            if amount.isdigit() and unit in ['', 'k', 'm', 'b']:
                return (int(amount), unit)

            raise commands.BadArgument(message="Not a valid amount!")


# =============================================================== economy commands ========================================================================


@client.command(aliases=['balance'])
async def bal(ctx):
    memberData = loadMemberData(ctx.author.id)

    embedVar = discord.Embed(title="{member}'s Balance".format(member=ctx.author.display_name))
    embedVar.add_field(name="Wallet", value=str(memberData["bal"]["wallet"]))
    embedVar.add_field(name="Bank", value=str(memberData["bal"]["bank"]))
    # print(f"embedVar: {embedVar}")

    await ctx.send(embed=embedVar)

@client.command()
async def transfer(ctx, member: discord.Member, amount):
    ownerData = loadMemberData(ctx.author.id)
    recipientData = loadMemberData(member.id)
    # multiplier = {'k': 3, 'm': 6, 'b': 9}

    # amount, unit = quantity
    # amount = amount * pow(10, multiplier[unit])
    # print(f"ownerData: {ownerData}, recipientData: {recipientData}")
    try:
        amount = int(amount)
    except:
        await ctx.send("invalid amount!")

    # print(f"{type(amount)}")
    if ownerData["bal"]["wallet"] >= amount:
        ownerData["bal"]["wallet"] -= amount
        recipientData["bal"]["wallet"] += amount

        updateBalance(ctx.author.id, ownerData)
        updateBalance(member.id, recipientData)

        await ctx.send(f"{amount} :coin: has been transferred to {member.mention}")
    else:
        await ctx.send("funds are insufficient!")

@client.command()
async def deposit(ctx, amount):
    memberData = loadMemberData(ctx.author.id)
    try:
        amount = int(amount)
    except:
        await ctx.send("invalid amount!")

    # print(f"{type(amount)}")
    if memberData["bal"]["wallet"] >= amount:
        memberData["bal"]["wallet"] -= amount
        memberData["bal"]["bank"] += amount

        updateBalance(ctx.author.id, memberData)
        
        await ctx.send(f"{amount} :coin: has been deposited!")
    else:
        await ctx.send("funds are insufficient!")

@client.command()
async def withdraw(ctx, amount):
    memberData = loadMemberData(ctx.author.id)
    try:
        amount = int(amount)
    except:
        await ctx.send("invalid amount!")

    # print(f"{type(amount)}")
    if memberData["bal"]["bank"] >= amount:
        memberData["bal"]["bank"] -= amount
        memberData["bal"]["wallet"] += amount

        updateBalance(ctx.author.id, memberData)
        
        await ctx.send(f"{amount} :coin: has been withdrawn!")
    else:
        await ctx.send("funds are insufficient!")


# =============================================================== earn money ===============================================================================


@client.command()
async def work(ctx):
    # print(f'work command')
    memberData = loadMemberData(ctx.author.id)
    # print(f"memberData: {memberData}")

    # await checkCooldowns("work", memberData)
    # checkBuffs(ctx.author.id, memberData)
    multiplier = 1
    for item in memberData["buffs"]:
        if item[0] == "money buff":
            print("money buff found")
            multiplier = 1.2
            item[1] -= 1
            if item[1] == 0:
                memberData["buffs"].remove(item)
            # print(f"memberdata in check buffs; {memberData}")
            updateBuffs(ctx.author.id, memberData)
    print(multiplier) #this shit doesn't print but checkBuffs literally goes all the way to the end

    # print(memberData["bal"]["wallet"])
    memberData["bal"]["wallet"] += round(100 * multiplier)
    memberData["cd"]["work"] = str(datetime.datetime.now() + datetime.timedelta(hours=1))
    print(memberData["bal"]["wallet"])
    await ctx.send(f"You earned {round(100 * multiplier)} :coin:!")

    updateBalance(ctx.author.id, memberData)
    updateCooldowns(ctx.author.id, memberData)

@client.command()
async def search(ctx):
    locations = ["car", "bathroom", "park", "truck", "pocket", "your room", "floor"]
    chosenLocations = random.choices(locations, k=3)
    print(f"chosen locations: {chosenLocations}")
    message = await ctx.send("where would you like to search")
    emojis = [':unknown:869243162902790194', '\N{THUMBS UP SIGN}'] #global emojis don't work what
    for emoji in emojis:
        await message.add_reaction(emoji)

    #filter out other messages https://youtu.be/A_3AOuQ4TMk?t=353
    #collector 

    # earnings = random.randint(100, 1000)
    # await ctx.send(f"You found {earnings} :coin:!")

    # memberData = loadMemberData(ctx.author.id)
    # memberData["bal"]["wallet"] += earnings
    # updateBalance(ctx.author.id, memberData)

@client.command() #steal; 70% chance of stealing 10-30 :coin: from target
async def steal(ctx, member: discord.Member):
    targetData = loadMemberData(member.id)
    memberData = loadMemberData(ctx.author.id)

    await checkCooldowns("steal", memberData)
    checkBuffs(ctx.author.id, memberData)

    luckynumber = random.randint(1,100)
    stealAmt = random.randint(10,30)

    if luckynumber <= 70:
        if targetData["bal"]["wallet"] >= stealAmt * multiplier:
            targetData["bal"]["wallet"] -= stealAmt * multiplier
            memberData["bal"]["wallet"] += stealAmt * multiplier
        else:
            stealAmt = targetData["bal"]["wallet"]
            targetData["bal"]["wallet"] -= stealAmt
            memberData["bal"]["wallet"] += stealAmt
            
        await ctx.send(f"You have stolen {stealAmt}:coin: from {member.mention}!")

    else:
        if memberData["bal"]["wallet"] >= stealAmt:
            memberData["bal"]["wallet"] -= stealAmt
            targetData["bal"]["wallet"] += stealAmt
        else:
            stealAmt = memberData["bal"]["wallet"]
            memberData["bal"]["wallet"] -= stealAmt
            targetData["bal"]["wallet"] += stealAmt

        await ctx.send(f"You failed to steal from {member.mention} and lost {stealAmt}:coin: instead!")
    
    memberData["cd"]["steal"] = str(datetime.datetime.now() + datetime.timedelta(hours=1))

    updateBalance(ctx.author.id, memberData)
    updateBalance(member.id, targetData)
    updateCooldowns(ctx.author.id, memberData)
        



# =============================================================== user commands ========================================================================


@client.command(aliases=["inventory"])
async def inv(ctx):
    memberData = loadMemberData(ctx.author.id)
    # print(f"member: {memberData}")
    em = discord.Embed(title=f"{ctx.author.display_name}'s Inventory")

    if len(memberData["inv"]) == 0:
        em.add_field(name = "Items", value = "none")
        em.add_field(name = "Consumables", value = "none")
    else:
        itemvalue = ""
        consumablevalue = ""
        for item in memberData["inv"]:
            name = item[0]
            amount = item[1]
            if item[2] == "item":
            # print(f"item: {item}")
                itemvalue = itemvalue + f"> **{name}:** {amount} \n"
            elif item[2] == "consumable":
            # print(f"item: {item}")
                consumablevalue = consumablevalue + f"> **{name}:** {amount} \n"
            
        if itemvalue == "":
            itemvalue = "none"
        elif consumablevalue == "":
            consumablevalue = "none"
        
        em.add_field(name = "Items", value = itemvalue)
        em.add_field(name = "Consumables", value = consumablevalue)

    await ctx.send(embed=em)

@client.command(aliases=['p'])
async def profile(ctx): #turn into profile and combine with bal 
    memberData = loadMemberData(ctx.author.id)

    if memberData["buffs"] != []:
        # print("buffs exist")
        value = ""
        for buff in memberData["buffs"]:
            value = value + f"> {buff[1]} | {buff[0]} \n"
        # print(value)
    else:
        # print('no buff')
        value = "no active buffs"

    em = discord.Embed(title=f"{ctx.author.display_name}'s Profile <:unknown:869243162902790194>")
    em.set_thumbnail(url=ctx.author.avatar_url)
    em.add_field(name = "PROGRESS", value = f"**Level:** {memberData['lvl']} \n **Experience:** {memberData['exp']}")
    em.add_field(name = "BALANCE", value = f"<:wallet:869585710519300137> **Wallet:** {str(memberData['bal']['wallet'])} \n :bank: **Bank:** {str(memberData['bal']['bank'])}", inline=False)
    em.add_field(name = "ACTIVE BUFFS", value = value)
    #rank

    await ctx.send(embed=em)

@client.command(aliases=['top'])
async def leaderboard(ctx):
    print("leaderboard") #make sure command gets run at all
    data = loadData() #grab data from json file
    rankedList = [] #list to dump sorted totals in
    unsortedList = [] #list to dump sorted totals in
    appended = False
    # counter = 0
    for memberID in data.keys(): #dump stuff into unsortedList
        netWorth = data[memberID]["bal"]["wallet"] + data[memberID]["bal"]["bank"] #sum wallet and bank values
        unsortedList.append(netWorth)
    # for i in list2:
    #     if rankedList == []:
    #         rankedList.append(i)
    #     else:
    print(f"list2: {unsortedList}")

    for i in unsortedList: #sort the stuff by amount
        print("i loop")
        appended = False
        for r in range(len(rankedList)):
            print("r loop")
            if i <= rankedList[r]:
                rankedList.insert(r,(int(memberID), netWorth)) #BUGGED please fix
                appended = True
                # counter +=1
                print(rankedList)
                break #why is this brekaing out of the outer loop
        if not appended:
            print("not appended")
            rankedList.append((int(memberID), netWorth))
            print(rankedList)
            

    print(f"rankedlist: {rankedList}")

@client.command()
async def buffs(ctx): #add how many uses left
    print("buffs")
    memberData = loadMemberData(ctx.author.id)
    
    em = discord.Embed(title=f"{ctx.author.display_name}'s Active Buffs")
    # print("em initialized")

    if memberData["buffs"] != []:
        # print("buffs exist")
        value = ""
        for buff in memberData["buffs"]:
            value = value + f"> {buff[1]} | {buff[0]} \n"
        # print(value)
        em.add_field(name = ".", value = value)
    else:
        # print('no buff')
        em.add_field(name = ".", value = "no active buffs")
    
    # print(em)
    await ctx.send(embed=em)



# =============================================================== shop commands ========================================================================


@client.command()
async def shop(ctx):
    print('shop command')
    shopData = loadShop()
    # print(f"shopdata: {shopData}")
    em = discord.Embed(title="Shop")
    itemvalue = ""
    consumablevalue = ""

    for item in shopData.values():
        # print(f"item: {item}")
        name = item["name"]
        price = item["price"]
        description = item["description"]
        if item["type"] == "item":
            itemvalue = itemvalue + f"**{name} | {price}** :coin: \n > {description} \n"
        elif item["type"] == "consumable":
            consumablevalue = consumablevalue + f"**{name} | {price}** :coin: \n > {description} \n"

        # print(value)
    if itemvalue == "":
        itemvalue = "Nothing in stock right now!"
    elif consumablevalue == "":
        consumablevalue = "Nothing in stock right now!"

    em.add_field(name = "ITEMS", value = itemvalue, inline = True)
    em.add_field(name = "CONSUMABLES", value = consumablevalue, inline = True)

    await ctx.send(embed=em)

@client.command() #to be done
async def buy(ctx, item, amount=1): 
    memberData = loadMemberData(ctx.author.id)
    shopData = loadShop()
    # print(shopData)
    # print(item, amount)
    # print(f'shopdata.keys = {list(shopData.keys())}')
    # print(shopData[item])
    # print(f"item doesnt exist check: {item not in list(shopData.keys())}")
    # print("the other check", shopData[item]["price"] * amount >= memberData["bal"]["wallet"])

    if item not in list(shopData.keys()):
        print("item doesn't exist")
        await ctx.send("Item doesn't exist!")
        return
    elif shopData[item]["price"] * amount >= memberData["bal"]["wallet"]:
        print("insufficient funds")
        await ctx.send("Insufficient funds!")
        return
    else:
        print("checks passed")
        memberData["bal"]["wallet"] = memberData["bal"]["wallet"] - shopData[item]["price"] * amount
        itemInInv = False
        for i in memberData["inv"]:
            if i[0] == item:
                i[1] += amount
                itemInInv = True
        if not itemInInv:
            memberData["inv"].append([item, amount, shopData[item]["type"]])

        updateBalance(ctx.author.id, memberData)
        updateInventory(ctx.author.id, memberData)

        await ctx.send(f"{amount} {item} purchased for {shopData[item]['price'] * amount} :coin:!")

@client.command()
async def sell(ctx, item, amount=1):
    print("sell command")
    memberData = loadMemberData(ctx.author.id)
    shopData = loadShop()
    print(type(amount))
    itemInInv = False

    try:
        amount = int(amount) #I actually dont know if this is even necessary since we default to 1
    except:
        await ctx.send("invalid amount!")
        return


    for invItem in memberData["inv"]:
        print(invItem)
        if item == invItem[0] and amount <= invItem[1]:
            print("item in inv and enough quantity")
            invItem[1] = invItem[1] - amount
            print(invItem)
            sellingprice = math.floor(amount * shopData[item]["price"] * 0.7)
            print(sellingprice)
            print(memberData["bal"]["wallet"])
            memberData["bal"]["wallet"] += sellingprice
            print(memberData["bal"]["wallet"])

            if invItem[1] == 0:
                memberData["inv"].remove(invItem)
            print(memberData["inv"])
            itemInInv = True

        elif item == invItem[0] and amount > invItem[1]:
            await ctx.send("not enough items to sell!")
            itemInInv = True
            return
        
    if itemInInv == False:
        await ctx.send("You don't have this item!")
    
    updateBalance(ctx.author.id, memberData)
    updateInventory(ctx.author.id, memberData)
    await ctx.send(f"{amount} {item} sold for {sellingprice} :coin:!")

@client.command()
async def use(ctx, *, item):
    memberData = loadMemberData(ctx.author.id)

    if item == "money buff":
        itemInInv = False
        for i in memberData["inv"]:
            if i[0] == item:
                i[1] -= 1
                memberData["buffs"].append([item, 15])
                itemInInv = True
                if i[1] == 0:
                    memberData["inv"].remove(i)

        if not itemInInv:
            await ctx.send("You don't have this item!")
            return
        
        await ctx.send(f"{item} is now active for 15 commands!")

    elif item == "cd potion":
        itemInInv = False
        for i in memberData["inv"]:
            if i[0] == item:
                i[1] -= 1
                for func in memberData["cd"]:
                    # print(func)
                    cdTime = convert_stringtime(memberData["cd"][func])
                    now = datetime.datetime.now()
                    # print(f"old cd: {cdTime}")
                    # print(f"{cdTime > now}")
                    if cdTime > now:
                        timedifference = cdTime - now
                        # print(f"time dif: {timedifference}")
                        cdTime = cdTime - timedifference/2
                        # print(f"new cd: {cdTime}")
                        memberData["cd"][func] = str(cdTime)

                itemInInv = True
                if i[1] == 0:
                    memberData["inv"].remove(i)

        if not itemInInv:
            await ctx.send("You don't have this item!")
            return
        updateCooldowns(ctx.author.id, memberData)
        await ctx.send("Your cooldowns have been cut in half!")
    else:
        await ctx.send("item doesn't exist!")
        return

    updateInventory(ctx.author.id, memberData)
    updateBuffs(ctx.author.id, memberData)


# =============================================================== admin commands ========================================================================


@client.command()
@commands.has_permissions(manage_messages=True)
#@commands.has_any_role(insert roles)
async def give(ctx, member: discord.Member, amount):
    recipientData = loadMemberData(member.id)
    try:
        amount = int(amount)
    except:
        await ctx.send("invalid amount!")
    # print(f"recipientData: {recipientData}")
    # print(f"{type(amount)}")

    recipientData["bal"]["wallet"] += amount
    updateBalance(member.id, recipientData)

    await ctx.send(f"{amount} :coin: has been given to {member.mention}")

@client.command()
@commands.has_permissions(administrator=True)
async def additem(ctx, item, price, *, description):
    print('add item')
    shopData = loadShop()
    
    shopData[item] = {"name": item, "price": int(price), "description": description, "type": "item"}

    updateShop(shopData)
    await ctx.send(f"item {item} has been added to the shop.")

@client.command()
@commands.has_permissions(administrator=True)
async def addconsumable(ctx, item, price, *, description):
    shopData = loadShop()
    
    shopData[item] = {"name": item, "price": int(price), "description": description, "type": "consumable"}

    updateShop(shopData)
    await ctx.send(f"consumable {item} has been added to the shop.")


# =============================================================== helper functions ========================================================================


def loadData():
    with open(os.path.join(os.getcwd(), "amounts.json"), "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def loadMemberData(memberID):
    # print(f"memberID: {memberID}")
    data  = loadData()
    # print(f"data in load member: {data}")

    if f"{memberID}" not in list(data.keys()):
        print("member id not in data")
        now = datetime.datetime.now()
        return {"bal": {"wallet": 0, "bank": 0}, "cd":{"search": str(now), "work": str(now), "steal": str(now)}, "inv": [], "exp": 0, "lvl": 1, "buffs":[]}
    else:
        # print(f"member id in data yes very good")
        return data[f"{memberID}"]

def updateBalance(memberID, memberData):
    data = loadData()
    # print(f"data: {data}")
    # print(f"memberID: {memberID}, memberData: {memberData}")

    if data == {}:
        data = {f'{memberID}': memberData}
    elif f"{memberID}" not in list(data.keys()):
        data[f"{memberID}"] = memberData
    else:
        data[f"{memberID}"]["bal"] = memberData["bal"]
    # print(f"data after: {data}")

    with open("amounts.json", "w") as f:
        json.dump(data, f, indent=4)

def updateCooldowns(memberID, memberData):
    data = loadData()
    # print(f"data: {data}")

    if data == {}:
        data = {f'{memberID}': memberData}
    elif f"{memberID}" not in list(data.keys()):
        data[f"{memberID}"] = memberData
    else:
        data[f"{memberID}"]["cd"] = memberData["cd"]
    # print(f"data after: {data}")

    with open("amounts.json", "w") as f:
        json.dump(data, f, indent=4)

async def checkCooldowns(usercommand, memberData):
    now = datetime.datetime.now()
    cdTime = convert_stringtime(memberData["cd"][usercommand])
    # print(f"cdTime: {cdTime}") 
    # print(f"now: {now}")
    # print(f'time in object: {memberData["cd"]["work"]}, now: {now}, {cdTime > now}')
    if cdTime > now:
        timedifference = cdTime - now
        await ctx.send(f"Wait {timedifference} before using this command again!")
        return

def updateInventory(memberID, memberData):
    data = loadData()
    # print(f"data: {data}")

    if data == {}:
        data = {f'{memberID}': memberData}
    elif f"{memberID}" not in list(data.keys()):
        data[f"{memberID}"] = memberData
    else:
        data[f"{memberID}"]["inv"] = memberData["inv"]
    # print(f"data after: {data}")

    with open("amounts.json", "w") as f:
        json.dump(data, f, indent=4)

def updateBuffs(memberID, memberData):
    data = loadData()
    # print(f"data: {data}")
    if data == {}:
        data = {f'{memberID}': memberData}
    elif f"{memberID}" not in list(data.keys()):
        data[f"{memberID}"] = memberData
    else:
        data[f"{memberID}"]["buffs"] = memberData["buffs"]
    # print(f"data after: {data}")

    with open("amounts.json", "w") as f:
        json.dump(data, f, indent=4)

def checkBuffs(memberID, memberData):
    multiplier = 1
    for item in memberData["buffs"]:
        if item[0] == "money buff":
            print("money buff found")
            multiplier = 1.2
            item[1] -= 1
            if item[1] == 0:
                memberData["buffs"].remove(item)
            # print(f"memberdata in check buffs; {memberData}")
            updateBuffs(memberID, memberData)
            # print(multiplier)
            return multiplier
    return multiplier

def loadShop():
    with open(os.path.join(os.getcwd(), "shop.json"), "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def updateShop(shopData):
    with open(os.path.join(os.getcwd(), "shop.json"), "w") as f:
        json.dump(shopData, f, indent=4)
    
def convert_stringtime(time):
    return datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')

def updateLevel(memberID, memberData):
    # print("update level")
    data = loadData()
    # print(f"data: {data}")
    if data == {}:
        data = {f'{memberID}': memberData}
    elif f"{memberID}" not in list(data.keys()):
        data[f"{memberID}"] = memberData
    else:
        data[f"{memberID}"]["exp"] = memberData["exp"]
        data[f"{memberID}"]["lvl"] = memberData["lvl"]
    # print(f"data after: {data}")

    with open("amounts.json", "w") as f:
        json.dump(data, f, indent=4)


# =============================================================== events ========================================================================                 


@client.event
async def on_ready():
    print("Bot Ready")

#levelling system
@client.event
async def on_message(msg):
    if not msg.author.bot:
        print("on message")

        memberData = loadMemberData(msg.author.id)
        # print(f"memberData: {memberData}")

        experience = memberData["exp"]
        memberData["exp"] += 5

        # print(experience, memberData["exp"])

        lvl_start = memberData["lvl"]
        lvl_end = int(experience ** (1/4))
        # print(lvl_start, lvl_end)

        if lvl_start < lvl_end:
            # print("lvl start < lvl end")
            await msg.channel.send(f"{msg.author.mention} has leveled up to level {lvl_end}!")
            memberData["lvl"] = lvl_end
        

        updateLevel(msg.author.id, memberData)
    else:
        print("bot detected")

    await client.process_commands(msg)

#for the search command
@client.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        if reaction.emoji in [':unknown:869243162902790194', '\N{THUMBS UP SIGN}']:

            memberData = loadMemberData(user.id)
            amt = random.randint(300,500) * multiplier
            memberData["bal"]["wallet"] += amt 
            updateBalance(user.id, memberData)
            await ctx.send(f"You found {amt} :coin: in the garbage") #make the location dynamic; doesn't prevent reaction spamming or other people taking your shit


client.run('ODY1MjUxOTQ3OTAwODI5Njk4.YPBSqw.aqZNiP5irY2Q6EJf4x1q7Mhkvdg')
