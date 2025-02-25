
import discord
from discord.ext import commands
import io
import uuid
from pydub import AudioSegment
import os

from utils.csv.save_csv import save_generated_data_as_csv  # Existing CSV save function
from utils.neurosync_api_connect import send_audio_to_neurosync  # Existing function for API call

# Initialize Discord bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Main directory to store generated CSV files and audio
DISCORD_GEN_DIR = 'discord_gen'
os.makedirs(DISCORD_GEN_DIR, exist_ok=True)  # Ensure the base folder exists

# Set to True if you want to use the local Neurosync API instead of the remote one
USE_LOCAL_API = True

@bot.command()
async def upload_audio(ctx):
    # Ensure an audio file is uploaded
    if len(ctx.message.attachments) == 0:
        await ctx.send('❌ Please upload an audio file with this command.')
        return

    attachment = ctx.message.attachments[0]

    # Check file size limit (20 MB)
    if attachment.size > 20 * 1024 * 1024:
        await ctx.send('❌ File size exceeds 20 MB limit. Please upload a smaller file.')
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
        await ctx.send('❌ Please upload a WAV or MP3 audio file.')
        return

    # Directly call the Neurosync API (local or remote)
    blendshape_data = send_audio_to_neurosync(audio_data, use_local=USE_LOCAL_API)

    # Check if the request was successful
    if blendshape_data:
        # Generate a unique folder for each upload
        unique_id = str(uuid.uuid4())
        output_dir = os.path.join(DISCORD_GEN_DIR, unique_id)
        os.makedirs(output_dir, exist_ok=True)

        # Define paths for both CSV and audio files
        csv_path = os.path.join(output_dir, 'blendshapes.csv')
        audio_path = os.path.join(output_dir, 'audio.wav')

        # Save the audio file locally
        try:
            with open(audio_path, 'wb') as audio_file:
                audio_file.write(audio_data)

            # Save the blendshape data to a CSV file
            save_generated_data_as_csv(blendshape_data, csv_path)

            # Only send back the blendshapes CSV
            await ctx.send("✅ Blendshape data processed successfully!", file=discord.File(csv_path))
        except Exception as e:
            await ctx.send(f'❌ Failed to save audio or blendshape data: {e}')
    else:
        await ctx.send('❌ Failed to generate blendshapes from Neurosync API.')

# Run the bot with your Discord bot token
bot.run('YOUR_DISCORD_BOT_TOKEN')
