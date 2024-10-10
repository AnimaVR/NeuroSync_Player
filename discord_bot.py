# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import discord
from discord.ext import commands
import requests
import json
import io
from pydub import AudioSegment  

# Set your API key and the Neurosync API URL
NEUROSYNC_API_URL = "https://api.neurosync.info/audio_to_blendshapes"
API_KEY = "YOUR_NEUROSYNC_API_KEY"  # Replace with your actual API key

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def upload_audio(ctx):
    # Ensure an audio file is uploaded
    if len(ctx.message.attachments) == 0:
        await ctx.send('Please upload an audio file with this command.')
        return

    attachment = ctx.message.attachments[0]
    
    # Check file size limit (20 MB)
    if attachment.size > 20 * 1024 * 1024:
        await ctx.send('File size exceeds 20 MB limit. Please upload a smaller file.')
        return

    audio_data = await attachment.read()

    # Convert MP3 to WAV if necessary
    if attachment.filename.endswith('.mp3'):
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        audio_segment = audio_segment.set_frame_rate(88200)
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        audio_data = wav_io.getvalue()
    elif not attachment.filename.endswith('.wav'):
        await ctx.send('Please upload a WAV or MP3 audio file.')
        return

    # Send the audio data to the Neurosync API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/octet-stream"
    }

    r = requests.post(NEUROSYNC_API_URL, headers=headers, data=audio_data)

    # Check if the request was successful
    if r.status_code == 200:
        blendshape_data = r.json()

        # Save the blendshape data to a text file
        with open('blendshapes.txt', 'w') as f:
            json.dump(blendshape_data, f, indent=4)

        # Send the text file back to Discord
        await ctx.send(file=discord.File('blendshapes.txt'))
    else:
        await ctx.send(f'Failed to generate blendshapes. Status Code: {r.status_code}')

# Run the bot with your Discord bot token
bot.run('YOUR_DISCORD_BOT_TOKEN')
