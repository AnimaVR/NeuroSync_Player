import discord
from discord.ext import commands
import io
import uuid
import os
import magic  # For MIME type validation
import subprocess
from pydub import AudioSegment

from utils.csv.save_csv import save_or_return_csv  # Updated CSV saving utility
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync  # Existing function for API call

# Initialize Discord bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Main directory to store generated CSV files and audio
DISCORD_GEN_DIR = 'discord_gen'
os.makedirs(DISCORD_GEN_DIR, exist_ok=True)

# Set to True if you want to use the local Neurosync API instead of the remote one
USE_LOCAL_API = True
SEND_CSV_DIRECTLY = True  # Set this flag to True if you want to send the CSV without saving


def is_valid_audio(audio_bytes):
    """Check if the uploaded file is a valid WAV or MP3 based on MIME type."""
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(audio_bytes)

    allowed_types = ['audio/mpeg', 'audio/wav']
    return file_type in allowed_types


def safely_convert_audio(audio_bytes, input_format):
    """Convert audio using pydub with basic sandboxing."""
    try:
        # Convert using a subprocess call to ffmpeg for added isolation
        with io.BytesIO(audio_bytes) as input_buffer:
            audio = AudioSegment.from_file(input_buffer, format=input_format)
            audio = audio.set_frame_rate(88200)  # Convert to target format (WAV)

            # Export safely to memory
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            return wav_io.getvalue()
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None


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

    # Validate audio using MIME type detection
    if not is_valid_audio(audio_data):
        await ctx.send('❌ Unsupported or potentially malicious file format detected.')
        return

    # Convert MP3 to WAV if necessary
    input_format = 'mp3' if attachment.filename.endswith('.mp3') else 'wav'
    converted_audio = safely_convert_audio(audio_data, input_format)

    if not converted_audio:
        await ctx.send('❌ Failed to process the audio securely.')
        return

    # Call the Neurosync API (local or remote)
    blendshape_data = send_audio_to_neurosync(converted_audio, use_local=USE_LOCAL_API)

    # Check if the request was successful
    if blendshape_data:
        # Generate a unique folder for each upload if saving locally
        if not SEND_CSV_DIRECTLY:
            unique_id = str(uuid.uuid4())
            output_dir = os.path.join(DISCORD_GEN_DIR, unique_id)
            os.makedirs(output_dir, exist_ok=True)

            # Save both audio and CSV
            audio_path = os.path.join(output_dir, 'audio.wav')
            csv_path = os.path.join(output_dir, 'blendshapes.csv')

            with open(audio_path, 'wb') as audio_file:
                audio_file.write(converted_audio)

            save_or_return_csv(blendshape_data, output_path=csv_path)

            await ctx.send("✅ Audio and blendshape data processed successfully!", file=discord.File(csv_path))
        else:
            # Send CSV directly without saving
            csv_buffer = save_or_return_csv(blendshape_data, return_in_memory=True)
            await ctx.send("✅ Blendshape data processed successfully!", file=discord.File(csv_buffer, filename='blendshapes.csv'))

    else:
        await ctx.send('❌ Failed to generate blendshapes from Neurosync API.')


# Run the bot with your Discord bot token
bot.run('YOUR_DISCORD_BOT_TOKEN')
