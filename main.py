# Gambling Bot for Discord with Wallets, Withdrawals, Admin Controls, and Custom Currency Types

import discord
import random
import asyncio
import json
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command("help")

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE = "user_data.json"
OWNER_ID = 1357231971905835151  # Your Discord user ID

def load_data():
    if os.path.exists(DATABASE):
        with open(DATABASE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATABASE, 'w') as f:
        json.dump(data, f, indent=4)

user_data = load_data()

MONEY_FILE = "money_types.json"
def load_money_types():
    if os.path.exists(MONEY_FILE):
        with open(MONEY_FILE, 'r') as f:
            return json.load(f)
    return ["money_1", "money_2"]

def save_money_types():
    with open(MONEY_FILE, 'w') as f:
        json.dump(money_types, f, indent=4)

money_types = load_money_types()

def ensure_wallet(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"wallet": {}, "withdraws": []}
    for mtype in money_types:
        if mtype not in user_data[user_id]["wallet"]:
            user_data[user_id]["wallet"][mtype] = 0
    save_data(user_data)

@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    ensure_wallet(user_id)
    wallet = user_data[user_id]["wallet"]
    embed = discord.Embed(title=f"{ctx.author.display_name}'s Wallet", color=discord.Color.green())
    for money, amount in wallet.items():
        emoji = "🪙" if "1" in money else "💎"
        embed.add_field(name=money.capitalize(), value=f"{amount} {emoji}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Gambling Bot Help", color=discord.Color.blurple())
    embed.add_field(name="/balance", value="Check your wallet.", inline=False)
    embed.add_field(name="/gamble <amount> <money_type>", value="Gamble an amount using specified money type.", inline=False)
    embed.add_field(name="/withdraw <amount> <money_type>", value="Withdraw money and notify admins.", inline=False)
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="/addmoney /reducemoney", value="Admins only: Modify user balances.", inline=False)
    if ctx.author.id == OWNER_ID:
        embed.add_field(name="/createmoney /deletemoney", value="Owner only: Add or remove money types.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def gamble(ctx, amount: int, money_type: str):
    user_id = str(ctx.author.id)
    ensure_wallet(user_id)
    money_type = money_type.lower()
    if money_type not in money_types:
        return await ctx.send("❌ Invalid money type.")
    if amount <= 0 or user_data[user_id]["wallet"][money_type] < amount:
        return await ctx.send("❌ Invalid amount.")
    if random.choice(["win", "lose"]) == "win":
        user_data[user_id]["wallet"][money_type] += amount
        await ctx.send(f"🎉 You won {amount} {money_type}!")
    else:
        user_data[user_id]["wallet"][money_type] -= amount
        await ctx.send(f"💀 You lost {amount} {money_type}.")
    save_data(user_data)

@bot.command()
async def withdraw(ctx, amount: int, money_type: str):
    user_id = str(ctx.author.id)
    ensure_wallet(user_id)
    money_type = money_type.lower()
    if money_type not in money_types or amount <= 0:
        return await ctx.send("❌ Invalid money type or amount.")
    if user_data[user_id]["wallet"][money_type] < amount:
        return await ctx.send("❌ Not enough funds.")
    user_data[user_id]["wallet"][money_type] -= amount
    user_data[user_id]["withdraws"].append({ "amount": amount, "type": money_type })
    save_data(user_data)
    for member in ctx.guild.members:
        if member.guild_permissions.administrator and not member.bot:
            try:
                await member.send(f"📤 {ctx.author} wants to withdraw {amount} {money_type}.")
            except:
                pass
    await ctx.send(f"✅ Withdraw request sent for {amount} {money_type}.")

@bot.command()
async def addmoney(ctx, amount: int, user: discord.User, money_type: str):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Admins only.")
    user_id = str(user.id)
    ensure_wallet(user_id)
    money_type = money_type.lower()
    if money_type not in money_types:
        return await ctx.send("❌ Invalid money type.")
    user_data[user_id]["wallet"][money_type] += amount
    save_data(user_data)
    await ctx.send(f"✅ Added {amount} {money_type} to {user.name}.")

@bot.command()
async def reducemoney(ctx, amount: int, user: discord.User, money_type: str):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Admins only.")
    user_id = str(user.id)
    ensure_wallet(user_id)
    money_type = money_type.lower()
    if money_type not in money_types:
        return await ctx.send("❌ Invalid money type.")
    user_data[user_id]["wallet"][money_type] -= amount
    save_data(user_data)
    await ctx.send(f"❌ Removed {amount} {money_type} from {user.name}.")

@bot.command()
async def createmoney(ctx, money_type: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Owner only.")
    money_type = money_type.lower()
    if money_type in money_types:
        return await ctx.send("❌ Money type already exists.")
    money_types.append(money_type)
    save_money_types()
    for uid in user_data:
        if money_type not in user_data[uid]["wallet"]:
            user_data[uid]["wallet"][money_type] = 0
    save_data(user_data)
    await ctx.send(f"✅ Money type '{money_type}' created.")

@bot.command()
async def deletemoney(ctx, money_type: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Owner only.")
    money_type = money_type.lower()
    if money_type not in money_types:
        return await ctx.send("❌ Money type doesn't exist.")
    money_types.remove(money_type)
    save_money_types()
    for uid in user_data:
        user_data[uid]["wallet"].pop(money_type, None)
    save_data(user_data)
    await ctx.send(f"🗑️ Money type '{money_type}' deleted.")

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

bot.run(TOKEN)
