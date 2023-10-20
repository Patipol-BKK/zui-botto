import os

import discord
import openai
import functools
import typing
import asyncio
from dotenv import load_dotenv
import datetime
import re
import tiktoken
import time

from discord_formatting_utils import markdown_to_text

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

DEFAULT_PROMPT = os.getenv('DEFAULT_PROMPT')

openai.api_key = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

emotes_dict = {
    '751668390455803994': '(Cat smiling and crying and putting thumb up emote)',
    '751668390455803995': '(Cat smiling and crying and putting thumb down emote)',
    'wuuuaaat': '(Usada Pekora saying "whattttttt!!!?" emote)',
    'urrrrrrrr':'(Usada Pekora being frustrated emote)',
    '602092952159780874': '(huh? emote)',
    '884491552594985080': '("brain not working" emote)',
    'Abbbbbbb': '(dab emote)',
    'CuteQuestion':'(person having a question emote)',
    'Waow': '(Wow! emote)',
    'xdw':'(xD emote)',
    'xd':'(xD emote)',
    'Deb':'(fox girl dabbing emote)',
    'toad':'(toad dancing emote)',
}

gpt_versions = [
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-0301',
    'gpt-3.5-turbo-0613',
    'gpt-3.5-turbo-16k',
    'gpt-3.5-turbo-16k-0613',
    'gpt-4',
    'gpt-4-0314',
    'gpt-4-0613',
]

default_response = []

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

def init_intent():
    return {
        'chat_gpt' : True,
        'model' : 'gpt-3.5-turbo',
        'chat_msgs' : default_response,
        'command_txt' : {'role' : 'system', 'content' : ''},
        'token_limit' : 3000
    }

def format_msg(role: str, msg: str):
    return {"role": role, "content": msg}

def contains_botto(message):
    return message.find('[zui-botto]:')

@to_thread
def generate(model, messages):
    return openai.ChatCompletion.create(model=model, messages=messages, temperature=0.2)


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

ignore_commands = [
    'needsmorejpeg',
    'bigmoji',
    'triggered'
]

def parse_command(text):
    cmd_tag = text[0]
    split_text = text[1:].split(' ')
    cmd = split_text[0]
    arg = ' '.join(split_text[1:])
    return [cmd_tag, cmd, arg]

channel_intents = {}

@client.event
async def on_message(message):
    if message.author.bot:
            return
    try:
        guild_id = message.guild.id
        if not ('bot' in str(message.channel) or 'gpt' in str(message.channel) or 'chat' in str(message.channel)):
            return
    except:
        guild_id = 'dm'
    channel = message.channel
    channel_id = message.channel.id

    intent_id = str(channel_id) + '_' + str(guild_id)
    global channel_intents
    if intent_id not in channel_intents:
        channel_intents[intent_id] = init_intent()

    print(f'[{intent_id}] {message.author}: {message.content}')
    cmd_tag, cmd, arg = parse_command(message.content)
    if cmd in ignore_commands:
        return
    match cmd_tag:
        case '!':
            match cmd:
                ## Chat Commands
                case 'newchat':
                    embedVar = discord.Embed(title="New chat started!", color=0xBA68C8)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)
                    channel_intents[intent_id]['chat_gpt'] = True
                    channel_intents[intent_id]['chat_msgs'] = []

                ## Token Commands
                case 'total_token':
                    loading_msg = await channel.send('<a:pluzzlel:959061506568364042>', reference=message, mention_author=False)
                    # Setup tiktoken encoder with current model
                    encoding = tiktoken.encoding_for_model(channel_intents[intent_id]['model'])

                    # Count token for each types of message in the current channel
                    prompt_token_count = len(encoding.encode(channel_intents[intent_id]['command_txt']['content']))
                    user_token_count = 0
                    response_token_count = 0
                    for chat_msg in channel_intents[intent_id]['chat_msgs']:
                        if chat_msg['role'] == 'user':
                            user_token_count += len(encoding.encode(chat_msg['content']))
                        elif chat_msg['role'] == 'assistant':
                            response_token_count += len(encoding.encode(chat_msg['content']))
                    total_token_count = prompt_token_count + user_token_count + response_token_count

                    await loading_msg.delete()
                    # Send result as embed to Discord
                    embedVar = discord.Embed(title=f"Total Chat Tokens: {total_token_count}", 
                        description=f'- Prompt: {prompt_token_count}\n- User: {user_token_count}\n- Response: {response_token_count}',
                        color=0x64FFDA)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'prev_token':
                    loading_msg = await channel.send('<a:pluzzlel:959061506568364042>', reference=message, mention_author=False)
                    error = False
                    if len(channel_intents[intent_id]['chat_msgs']) < 2:
                        channel_intents[intent_id]['chat_msgs'] = []
                        error = True

                    if not error:
                        # Setup tiktoken encoder with current model
                        encoding = tiktoken.encoding_for_model(channel_intents[intent_id]['model'])

                        # Count token for each types of message in the current channel
                        prompt_token_count = len(encoding.encode(channel_intents[intent_id]['command_txt']['content']))
                        user_token_count = len(encoding.encode(channel_intents[intent_id]['chat_msgs'][len(channel_intents[intent_id]['chat_msgs']) - 2]['content']))
                        response_token_count = len(encoding.encode(channel_intents[intent_id]['chat_msgs'][len(channel_intents[intent_id]['chat_msgs']) - 1]['content']))
                    else:
                        prompt_token_count = 0
                        user_token_count = 0
                        response_token_count = 0

                    total_token_count = prompt_token_count + user_token_count + response_token_count
                    await loading_msg.delete()
                    # Send result as embed to Discord
                    embedVar = discord.Embed(title=f"Previous Chat Tokens: {total_token_count}", 
                        description=f'- Prompt: {prompt_token_count}\n- User: {user_token_count}\n- Response: {response_token_count}',
                        color=0x64FFDA)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'token_count':
                    loading_msg = await channel.send('<a:pluzzlel:959061506568364042>', reference=message, mention_author=False)
                    # Setup tiktoken encoder with current model
                    encoding = tiktoken.encoding_for_model(channel_intents[intent_id]['model'])

                    num_tokens = len(encoding.encode(arg))

                    await loading_msg.delete()
                    # Send result as embed to Discord
                    embedVar = discord.Embed(title=f"Total Tokens: {num_tokens}", color=0x64FFDA)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)                        

                case 'token_limit':
                    embedVar = discord.Embed(title=f"Current Token Limit: {channel_intents[intent_id]['token_limit']}", color=0x64FFDA)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'set_token_limit':
                    error = False
                    try:
                        token_limit = int(arg)
                    except Exception as e:
                        embedVar = discord.Embed(title=f'Input Value Error:', description=f'{str(e)[:4096]}', color=0xf75948)
                        await channel.send(embed=embedVar, reference=message, mention_author=False)
                        error = True

                    if not error:
                        channel_intents[intent_id]['token_limit'] = token_limit
                        embedVar = discord.Embed(title=f"Set Token Limit to: {channel_intents[intent_id]['token_limit']}", color=0x64FFDA)
                        await channel.send(embed=embedVar, reference=message, mention_author=False)
                ## Model Version Commands
                case 'set_gpt':
                    if not arg in gpt_versions:
                        embedVar = discord.Embed(title=f"Invalid GPT version", description=f"Available versions: \n{str(gpt_versions)}", color=0xf75948)
                        await channel.send(embed=embedVar, reference=message, mention_author=False)
                    else:
                        channel_intents[intent_id]['model'] = arg
                        embedVar = discord.Embed(title=f"Set ChatGPT Model to: {channel_intents[intent_id]['model'][:220]}", color=0xFFF176)
                        await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'list_gpt':
                    embedVar = discord.Embed(title=f"Available versions:", description=f"{str(gpt_versions)}", color=0xFFF176)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'gpt': 
                    embedVar = discord.Embed(title=f"Currently Using: {channel_intents[intent_id]['model'][:220]}", color=0xFFF176)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                ## Prompt Commands
                case 'set_prompt':
                    channel_intents[intent_id]['command_txt'] = {'role' : 'system', 'content' : arg}
                    embedVar = discord.Embed(title=f"Set Prompt as:", description=f'{channel_intents[intent_id]["command_txt"]["content"][:4096]}', color=0x8D6E63)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case 'prompt':
                    embedVar = discord.Embed(title=f"Current Prompt:", description=f'{channel_intents[intent_id]["command_txt"]["content"][:4096]}', color=0x8D6E63)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                ## Msc Commands
                case 'ping':
                    await channel.send('Pong! {0}ms'.format(round(client.latency*1000, 1)), reference=message, mention_author=False)

                case 'help':
                    with open('cmd_desc.txt', 'r') as f:
                        help_txt = f.read()
                    embedVar = discord.Embed(title=f"Commands List:", description=f'{help_txt[:4096]}', color=0xE1F5FE)
                    await channel.send(embed=embedVar, reference=message, mention_author=False)

                case '':
                    await channel.send('!' + cmd, reference=message, mention_author=False)
        case '`':
            msg = (cmd + ' ' + arg).strip()

            for key in emotes_dict.keys():
                msg = re.sub(key, emotes_dict[key], msg)
            msg = re.sub(r"<:\(", "(", msg)
            msg = re.sub(":[0-9]*>", "", msg)

            current_chat_msgs = channel_intents[intent_id]['chat_msgs'] + [{'role' : 'user', 'content' : msg}]
            loading_msg = await channel.send('<a:pluzzlel:959061506568364042>', reference=message, mention_author=False)

            # Count total token
            encoding = tiktoken.encoding_for_model(channel_intents[intent_id]['model'])

            # Count token for each types of message in the current channel
            prompt_token_count = len(encoding.encode(channel_intents[intent_id]['command_txt']['content']))
            token_count_list = []
            response_token_count = 0
            for chat_msg in current_chat_msgs:
                if chat_msg['role'] == 'user':
                    token_count_list.append(len(encoding.encode(chat_msg['content'])))
                elif chat_msg['role'] == 'assistant':
                    token_count_list.append(len(encoding.encode(chat_msg['content'])))

            total_token_count = sum(token_count_list) + prompt_token_count
            while total_token_count > channel_intents[intent_id]['token_limit']:
                token_count_list = token_count_list[1:]
                current_chat_msgs = current_chat_msgs[1:]
                total_token_count = sum(token_count_list) + prompt_token_count


            prompt = channel_intents[intent_id]['command_txt']

            error = False
            try:
                response = await generate(model=channel_intents[intent_id]['model'], messages=[prompt] + current_chat_msgs)
            except Exception as e:
                embedVar = discord.Embed(title=f'ChatGPT API Error:', description=f'{str(e)[:4096]}', color=0xf75948)
                await channel.send(embed=embedVar, reference=message, mention_author=False)
                await loading_msg.delete()
                error = True

            try:
                if not error:
                    cumulated_msg = ''
                    prev_time = time.time()
                    response_references = []
                    text_list = []
                    try:
                        await loading_msg.delete()
                        response_text = response.choices[0].message.content
                        text_list = markdown_to_text(response_text, 2000)

                        for text in text_list:
                            await channel.send(text, reference=message, mention_author=False)

                    except Exception as e:
                        embedVar = discord.Embed(title=f'Parsing ChatGPT Response Error:', description=f'{str(e)[:4096]}', color=0xf75948)
                        await channel.send(embed=embedVar, reference=message, mention_author=False)
                        await loading_msg.delete()
                        error = True
                    
                    if not error:
                        # Append user and chatgpt's response to chat history
                        channel_intents[intent_id]['chat_msgs'] = current_chat_msgs
                        channel_intents[intent_id]['chat_msgs'].append({'role' : 'assistant', 'content' : response_text})
                        try:
                            # Update response for the last time
                            text_list = markdown_to_text(cumulated_msg, 2000)
                            text_idx = 0
                            # Update sent msgs with new responses
                            for response_reference in response_references:
                                await response_reference.edit(content=text_list[text_idx])
                                text_idx += 1

                            # If not enough sent msgs to display all responses, send out new ones
                            while text_idx < len(text_list):
                                response_reference = await channel.send(text_list[text_idx], reference=message, mention_author=False)
                                response_references.append(response_reference)
                                text_idx += 1

                            # If not all of sent msgs are used to display the new response, delete excess
                            while len(response_references) > len(text_list):
                                response_reference = response_references.pop()
                                response_reference.delete()
                        except Exception as e:
                            embedVar = discord.Embed(title=f'Discord API Error:', description=f'{str(e)[:4096]}', color=0xf75948)
                            await channel.send(embed=embedVar, reference=message, mention_author=False)
                            await loading_msg.delete()
                            error = True

            except Exception as e:
                embedVar = discord.Embed(title=f'Unexpected Error:', description=f'{str(e)[:4096]}', color=0xf75948)
                await channel.send(embed=embedVar, reference=message, mention_author=False)
                await loading_msg.delete()
                error = True
    return
client.run(TOKEN)