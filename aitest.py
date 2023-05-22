#!/usr/bin/env python

import asyncio
import dotenv
import os
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_messages(prompt):
    return [
        {"role": "system", "content": "You are the character Poe from Altered Carbon."},
        {"role": "system", "content": "I'm a guest already at the hotel."},
        {"role": "system", "content": "We have met already, so no need for an introduction."},
        {"role": "user", "content": prompt}
    ]

async def main():
    response = await openai.ChatCompletion.acreate(
        model='gpt-3.5-turbo',
        #model="text-davinci-003",
        #messages=generate_messages('What security measures are available?'),
        messages=generate_messages('I need transportation to another sector. What is available?'),
        temperature=0.6
    )
    print(response.choices[0].message.content)

if __name__ == '__main__':
    asyncio.run(main())
