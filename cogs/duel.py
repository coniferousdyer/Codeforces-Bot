import discord
import aiohttp
import asyncio
import random
import datetime
from discord.ext import commands


class Duel(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Command to suggest a random problem, with optional tags and rating
    @commands.command()
    async def duel(self, ctx, usr: discord.User = None, rating=0):
        async with aiohttp.ClientSession() as session:

            # Checking if a user was mentioned
            if usr == None:
                await ctx.send("Please mention whom you want to duel.")
                return

            # Checking if rating was not given
            if rating == 0:
                await ctx.send("Please provide a rating.")
                return

            # Checking if the user mentioned themselves
            # if usr == ctx.author:
            #     await ctx.send("You can't duel yourself.")
            #     return

            reactMsg = await ctx.send(f"<@{usr.id}>, react to this message with :thumbsup: within 30 seconds to accept the duel.")

            # Function to check the reaction on the message
            def check(reaction, user):
                return user == usr and str(reaction.emoji) == '\N{THUMBS UP SIGN}' and reactMsg.id == reaction.message.id

            # Waiting for the reaction
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Sorry, the duel expired because 30 seconds were up!")
                return
            else:
                await ctx.send(f"<@{usr.id}> has accepted the duel! Finding problem...")

                # Finding problem
                async with session.get('https://codeforces.com/api/problemset.problems') as r:

                    # If URL was not found
                    if not r.ok:
                        await ctx.send("Sorry, an error occurred.")
                        return

                    # Reading the data as JSON data and storing the dictionary in data variable
                    data = await r.json()

                    # Filtering out the problems without rating
                    data["result"]["problems"] = filter(
                        lambda p: 'rating' in p, data["result"]["problems"])

                    # Filter the list to get problems of given rating
                    data["result"]["problems"] = filter(
                        lambda p: p["rating"] == rating, data["result"]["problems"])

                    data["result"]["problems"] = list(
                        data["result"]["problems"])

                    # In case no problems are found
                    if len(data["result"]["problems"]) == 0:
                        await ctx.send("Sorry, no problems could be found. Please try again.")
                        return

                    # Storing problem
                    problem = data["result"]["problems"][random.randint(
                        0, len(data["result"]["problems"]) - 1)]

                    # Creating an embed
                    Embed = discord.Embed(title=f"{problem['contestId']}{problem['index']}. {problem['name']}",
                                          url=f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']},",
                                          description="The duel starts now!",
                                          color=0xff0000)

                    Embed.add_field(
                        name="Rating", value=problem["rating"], inline=False)

                    Embed.add_field(
                        name="Duel", value=f"{ctx.author.display_name} vs {usr.display_name}")

                    # Sending embed
                    await ctx.send(embed=Embed)

                    # Storing the start time of the duel
                    startTime = datetime.datetime.now()

                    # Deleting problem list
                    del data

                    # Waiting for the duel to end
                    def check_2(m):
                        return m.content == "endduel" and m.channel == reactMsg.channel and (m.author == user or m.author == ctx.message.author)

                    msg = await self.client.wait_for('message', check=check_2)

                    # Obtaining and comparing the last submissions of the two users ###### TO BE CHANGED
                    async with session.get(f'https://codeforces.com/api/user.status?handle={}&from=1&count=1') as r1:
                        async with session.get(f'https://codeforces.com/api/user.status?handle={}&from=1&count=1') as r2:

                            # Saving the last submission in JSON form
                            data_1 = await r1.json()
                            data_2 = await r2.json()

                            # Boolean variables to check whether both users solved the problem
                            match_1 = False
                            match_2 = False

                            if problem["contestId"] == data_1["result"][0]["problem"]["contestId"] and problem["index"] == data_1["result"][0]["problem"]["index"] and data_1["result"][0]["verdict"] == "OK":
                                match_1 = True
                            if problem["contestId"] == data_2["result"][0]["problem"]["contestId"] and problem["index"] == data_2["result"][0]["problem"]["index"] and data_2["result"][0]["verdict"] == "OK":
                                match_2 = True

                            # If both users solved the problem
                            if match_1 and match_2:
                                if data_1["result"][0]["creationTimeSeconds"] <= data_2["result"][0]["creationTimeSeconds"]:
                                    await ctx.send(f"<@{ctx.message.author.id}> has won the duel against <@{user.id}>!")
                                else:
                                    await ctx.send(f"<@{user.id}> has won the duel against <@{ctx.message.author.id}>!")

                            # If only user_1 solved the problem
                            elif match_1:
                                await ctx.send(f"<@{ctx.message.author.id}> has won the duel against <@{user.id}>!")

                            # If only user_2 solved the problem
                            elif match_2:
                                await ctx.send(f"<@{user.id}> has won the duel against <@{ctx.message.author.id}>!")

                            # If neither solved the problem
                            else:
                                await ctx.send("Duel ended, neither won!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("-Duel ready!")


def setup(client):
    client.add_cog(Duel(client))
