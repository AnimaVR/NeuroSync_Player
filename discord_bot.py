# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import discord
from discord.ext import commands
import uuid
import os

from utils.csv.save_csv import save_or_return_csv  
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync  
from utils.audio.convert_audio import safely_convert_audio, is_valid_audio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DISCORD_GEN_DIR = 'discord_gen'
os.makedirs(DISCORD_GEN_DIR, exist_ok=True)

USE_LOCAL_API = True
SEND_CSV_DIRECTLY = True 


@bot.command()
async def upload_audio(ctx):
    if len(ctx.message.attachments) == 0:
        await ctx.send('❌ Please upload an audio file with this command.')
        return

    attachment = ctx.message.attachments[0]
    if attachment.size > 20 * 1024 * 1024:
        await ctx.send('❌ File size exceeds 20 MB limit. Please upload a smaller file.')
        return

    audio_data = await attachment.read()
    if not is_valid_audio(audio_data):
        await ctx.send('❌ Unsupported or potentially malicious file format detected.')
        return
    
    input_format = 'mp3' if attachment.filename.endswith('.mp3') else 'wav'
    converted_audio = safely_convert_audio(audio_data, input_format)

    if not converted_audio:
        await ctx.send('❌ Failed to process the audio securely.')
        return

    blendshape_data = send_audio_to_neurosync(converted_audio, use_local=USE_LOCAL_API)
    if blendshape_data:
        if not SEND_CSV_DIRECTLY:
            unique_id = str(uuid.uuid4())
            output_dir = os.path.join(DISCORD_GEN_DIR, unique_id)
            os.makedirs(output_dir, exist_ok=True)
            audio_path = os.path.join(output_dir, 'audio.wav')
            csv_path = os.path.join(output_dir, 'blendshapes.csv')

            with open(audio_path, 'wb') as audio_file:
                audio_file.write(converted_audio)

            save_or_return_csv(blendshape_data, output_path=csv_path)

            await ctx.send("✅ Audio and blendshape data processed successfully!", file=discord.File(csv_path))
        else:
            csv_buffer = save_or_return_csv(blendshape_data, return_in_memory=True)
            await ctx.send("✅ Blendshape data processed successfully!", file=discord.File(csv_buffer, filename='blendshapes.csv'))

    else:
        await ctx.send('❌ Failed to generate blendshapes from Neurosync API.')

bot.run('YOUR_DISCORD_BOT_TOKEN')
