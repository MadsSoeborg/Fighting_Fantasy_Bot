import discord
import random
import asyncio

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')
        print('------')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!guess'):
            await message.channel.send('Guess a number between 1 and 10.')

            def is_valid_guess(m):
                return m.author == message.author and m.content.isdigit()

            answer = random.randint(1, 10)

            try:
                guess = await self.wait_for('message', check=is_valid_guess, timeout=5.0)
            except asyncio.TimeoutError:
                return await message.channel.send(f'Sorry, you took too long it was {answer}.')
            if int(guess.content) == answer:
                await message.channel.send(f'You are right! {answer}.')
            else:
                await message.channel.send(f'You are wrong. It is actually {answer}')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('MTIxNjc5MTU4NTMyMTM5MDE0MQ.Gj9kLY.scdWcdiFI-PM-yvAOGekVs6Zft9qndokc6PUhA')