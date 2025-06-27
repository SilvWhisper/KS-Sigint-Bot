import os
import random
import discord
from discord.ext import commands

print("Current working directory:", os.getcwd()) #Tell console where we're at.
print("Writing to:", os.path.abspath("sigintraw.txt")) # Partially outdated; I don't really make only one file anymore.

intents = discord.Intents.default() # I still don't quite understand intents.
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def obfuscate(text): #Need a function for randomly obfuscating text generated in the channels.
    words = text.split()
    for i in range(len(words)): #Dynamically in length from the text generated
        if random.random() < 0.15: #Obfuscate 15% of words
            words[i] = "[XXXXX]" #Replacement text
    return " ".join(words) #Output

@bot.event # When the bot pops in for the first time
async def on_ready():
    print(f'Logged on as {bot.user}!')

@bot.command() # Specific command definition. Not sure if I'll need this for each command as this bot expands.
async def signalreport(ctx, target_channel: str = None): # Command(context, optional target channel is a string provided
    role_names = [role.name for role in ctx.author.roles] # For checking roles of the user sending the command; want it to only be usable by folks with the "Umpire" role.
    if "Umpire" not in role_names:
        await ctx.send(f"You need to be an Umpire") # Bounce if not right role.
        return

    channel_name = target_channel or ctx.channel.name # if the target is defined do that, or do the channel command is sent from
    filename = f"sigintraw_{channel_name}.txt" # Just defining the log files.

    try:
        with open(filename, "r+") as file: # Open the file r+ because we want to read it, but also append to it maybe?
            report = file.readlines() # Read each line, fill the report.
            f_report = [line for line in report if "!signalreport" not in line] # Iterate through the report variable to make a list that we can manipulate later.

        if not f_report: # Check to make sure there's data to actually log.
            await ctx.send(f"No signal traffic to report for `{channel_name}`.")
            return

        with open(filename, "w") as file: # Writing to the text file from f_report. I'm doubling up here because I think r+ isn't working above as intended. Need to circle back to this.
            # File manipulation in python eludes me a little. Need to make sure I'm doing this in an efficient manner.
            file.writelines(f_report)

        output_filename = f"report_{channel_name}.txt" # output as a new file
        with open(output_filename, "w") as output_file:
            for line in f_report:

                if '"' in line: # Toying with the lines.
                    before, quoted, after = line.partition('"') # Marking the line partition as a "
                    msg, _, end = after.partition('"') #
                    redacted = obfuscate(msg) # Call the obfuscation function
                    new_line = f'{before}"{redacted}"\n' # Edit the line.
                else:
                    new_line = line

                output_file.write(new_line)


        await ctx.send(file=discord.File(output_filename)) # send the file

    except FileNotFoundError:
        await ctx.send(f"No signal traffic recorded yet for `{channel_name}`.")
    except Exception as e:
        await ctx.send(f"Error reading signal report for `{channel_name}`: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name not in ["chat-1", "chat-2"]: # Hard coded channels for now. Kind of want in future for serve/users with the right role to be able to define this.
        # Probably call a JSON? Good excuse to learn to manipulate those
        await bot.process_commands(message) # Gotta wait for the bot to do its thing or it hangs
        return

    if isinstance(message.author, discord.Member): # Check if message is sent by a specific role and not a bot or something
        role_names = [role.name for role in message.author.roles] # For checking roles pulled from message.author parameter

        if "TestRole" in role_names: # Hard coded test role; kind of want in future for server/users with the right role to define this.
            if message.content.startswith("!signalreport"): # Don't log !signalreport
                await bot.process_commands(message)
                return

            try:
                filename = f"sigintraw_{message.channel.name}.txt" # Make the file if it doesn't exist, according to channel
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M") # Making the timestamp part of the message reasonable
                with open(filename, "a") as file: # Append to file
                    file.write(f"{timestamp} [CHANNEL: {message.channel.name}] {message.author.display_name} \"{message.content}\"\n") # Formatting the lines in the log.
            except Exception as e:
                print("Error writing to file:", e)

    else:
        await message.channel.send(f"Something went wrong.")

    await bot.process_commands(message)
bot.run('TOKEN')
