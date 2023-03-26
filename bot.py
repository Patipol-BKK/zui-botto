import os

import discord
import openai
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

openai.api_key = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

def init_intent():
    return {
        'chat_gpt' : False,
        'model' : 'gpt-3.5-turbo',
        'chat_msgs' : [{'role' : 'system', 'content' : 'You are an AI assistant. Please also include the language of your code block outputs in the backticks syntax without space in between.'}],
        'current_token' : 0,
        'token_limit' : 2000
    }

def format_msg(role: str, msg: str):
    return {"role": role, "content": msg}

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

channel_intents = {}

@client.event
async def on_message(message):
    if not message.author.bot:
        guild_id = message.guild.id

        channel = message.channel
        channel_id = message.channel.id

        intent_id = str(channel_id) + '_' + str(guild_id)
        global channel_intents
        if intent_id not in channel_intents:
            channel_intents[intent_id] = init_intent()

        print(f'{message.author}: {message.content}')
        if len(message.content) > 0:
            if message.content[0] == '!':
                if len(message.content) > 1:
                    cmd = message.content[1:]
                    if cmd == 'newchat':
                        embedVar = discord.Embed(title="New chat started!", color=0x74a89b)
                        await channel.send(embed=embedVar)
                        channel_intents[intent_id]['chat_gpt'] = True
                        channel_intents[intent_id]['chat_msgs'] = []
                    elif cmd == 'stopchat':
                        embedVar = discord.Embed(title="Chat stopped!", color=0xf75948)
                        await channel.send(embed=embedVar)
                        channel_intents[intent_id]['chat_gpt'] = False
                        channel_intents[intent_id]['chat_msgs'] = []

                    elif cmd == 'currenttoken':
                        embedVar = discord.Embed(title=f"Tokens used : {channel_intents[intent_id]['current_token']}", color=0xf75948)
                        await channel.send(embed=embedVar)

                    elif cmd == 'currentlimit':
                        embedVar = discord.Embed(title=f"Current token limit : {channel_intents[intent_id]['token_limit']}", color=0xf75948)
                        await channel.send(embed=embedVar)

                    elif cmd == 'ping':
                        await channel.send('Pong! {0}ms'.format(round(client.latency*1000, 1)))
            elif message.content[0] == '`':
                if len(message.content) > 1:
                    cmd = message.content[1:]
                    if channel_intents[intent_id]['chat_gpt']:
                        msg = cmd
                        channel_intents[intent_id]['chat_msgs'].append({'role' : 'user', 'content' : msg})
                        response = openai.ChatCompletion.create(model=channel_intents[intent_id]['model'], messages=channel_intents[intent_id]['chat_msgs'])

                        response_msg = response.choices[0].message.content
                        used_tokens = response.usage.total_tokens
                        channel_intents[intent_id]['current_token'] = used_tokens

                        print(f'ChatGPT Response : {response_msg}')
                        
                        if used_tokens > channel_intents[intent_id]['token_limit']:
                            channel_intents[intent_id]['chat_msgs'] = channel_intents[intent_id]['chat_msgs'][2:]

                        channel_intents[intent_id]['chat_msgs'].append({'role' : 'assistant', 'content' : response_msg})

                        await channel.send(response_msg)

client.run(TOKEN)