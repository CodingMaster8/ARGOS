import chainlit as cl
from openai import AsyncOpenAI
import literalai as li

from data_gather import ContextGatherer
from download_github import starts_with_pattern, download_github_repo
from query_db import create_table, fetch_file
from .chat_context import chatcontext
from .data import data_gather

client = AsyncOpenAI()


# Instrument the OpenAI client
cl.instrument_openai()



settings = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    print(message_history)
    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()


@cl.on_chat_start
async def start_chat():

    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    while True:
        res = await cl.AskUserMessage(content="Paste the link of the repo (ex : https://github.com/Polo280/KL25Z_Labs)").send()
        print(res)
        if starts_with_pattern(res['output']):
            await cl.Message(
                content=f"Your repo is: {res['output']}",
            ).send()
            download_github_repo(str(res['output']))

            file = str(res['output'])

            table_name = '/'.join(file.split('/')[-2:]).replace('/', '_')

            create_table(table_name)

            gatherer = ContextGatherer(
                directory='/Users/pablovargas/Documents/repos',
                output_file='../context.txt',
                relevant_extensions=['.py', '.c'],
                max_file_size=500_000,  # 500KB
                max_tokens=60000,
                repo=str(res['output']),
                table=table_name
            )
            context, token_count, context_tree = gatherer.run()

            await cl.Message(content=f"Token count: {token_count} \n{context_tree}", language="bash").send()

            query_file = await cl.AskUserMessage(content="What file you want to query?").send()



            break
        else:
            await cl.Message(
                content=f"Incorrect repo name: {res['output']}",
            ).send()









#Add settings to change llm and its parameters

#Add functionality to visualize code files like bash or .py