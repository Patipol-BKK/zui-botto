import os
from dotenv import load_dotenv
import openai
import tiktoken

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def format_msg(role: str, msg: str):
	return {"role": role, "content": msg}

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
models = openai.Model.list()
# print(openai.Model.list())

msg_list = []
msg_list.append(format_msg('user', '`Please provide a detailed overview of the history, evolution, and different types of Pole arms. Include historical key points, influential historical figure, and fighting techniques, along with their strengths and weaknesses. Also, discuss how other weapons and armors influence their development.'))

completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=msg_list)
num_char = 0
msg_list = completion.choices[0].message.content.split('\n')
chunk_list =[]
for message in msg_list:
    while(len(message) > 1990):
        print(message[:1990])
        message = message[1990:]

    chunk_list.append(message)
    num_char  = num_char + len(message)
    if num_char > 1990 - len(chunk_list):
        chunk_list = chunk_list[:-1]
        num_char  = num_char - len(message)
        print("\n".join(chunk_list))

        chunk_list = [message]
print("\n".join(chunk_list))

# print(completion.choices[0].message.content)
print(completion.usage.total_tokens)
# msg_list.append(format_msg('assistant', completion.choices[0].message.content))

# msg_list.append(format_msg('user', 'how to do that in python?'))
# completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=msg_list)
# print(completion.choices[0].message.content)

# num_tokens_from_string("tiktoken is great!", "cl100k_base")
# print()