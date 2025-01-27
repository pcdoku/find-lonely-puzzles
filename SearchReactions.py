'''
todo:
    search archives and introduce more choices based on reactions (ratings, tags)
    maybe? make username @ (only if able to not mention).  Allowed_mentiond = None
    download all data to allow making top 10 lists based on reactions.
    minimum age (0 days default?)
    on update, make title include "updated Nov 15 11:99pm"
    search my submitted puzzles.
    GAS and GAPP stats? 

    allow pinning and updating pins for archive search.
'''

import os
import io
import datetime
import pytz
import configparser
import traceback
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands
from azure.cosmos import CosmosClient

try:
    access_token= os.environ["ACCESS_TOKEN"]
    other_access_token= os.environ["OTHER_ACCESS_TOKEN"]
    guild_id = os.environ["GUILD_ID"]
    sudoku_submissions_channel_id = int(os.environ["SUDOKU_SUBMISSIONS_CHANNEL_ID"])
    other_submissions_channel_id = int(os.environ["OTHER_SUBMISSIONS_CHANNEL_ID"])
    word_submissions_channel_id = int(os.environ["WORD_SUBMISSIONS_CHANNEL_ID"])
    archive_channel_id = int(os.environ["ARCHIVE_CHANNEL_ID"])
    monthly_archive_channel_id = int(os.environ["MONTHLY_ARCHIVE_CHANNEL_ID"])
    max_puzzles_return = int(os.environ["MAX_PUZZLES_RETURN"])
    days_to_search = int(os.environ["DAYS_TO_SEARCH"])
    reaction_threshhold = int(os.environ["REACTION_THRESHHOLD"])
    solved_emoji_name = os.environ['SOLVED_EMOJI_NAME']
    broken_emoji_name = os.environ['BROKEN_EMOJI_NAME']
    calling_bot_id = int(os.environ['CALLING_BOT_ID'])
    developer_id = int(os.environ['DEVELOPER_ID'])
    log_channel_id = int(os.environ['LOG_CHANNEL_ID'])
    sql_uri = os.environ['SQL_URI']
    sql_key = os.environ['SQL_KEY']
    server_mod_id = int(os.environ['SERVER_MOD_ID'])

except:
    config = configparser.ConfigParser()
    config.read('localconfig.ini')
    access_token = config['db']['ACCESS_TOKEN']
    other_access_token= config['db']["OTHER_ACCESS_TOKEN"]
    guild_id = config['db']['GUILD_ID']
    sudoku_submissions_channel_id = int(config['db']['SUDOKU_SUBMISSIONS_CHANNEL_ID'])
    other_submissions_channel_id = int(config['db']['OTHER_SUBMISSIONS_CHANNEL_ID'])
    word_submissions_channel_id = int(config['db']["WORD_SUBMISSIONS_CHANNEL_ID"])
    archive_channel_id = int(config['db']["ARCHIVE_CHANNEL_ID"])
    monthly_archive_channel_id = int(config['db']["MONTHLY_ARCHIVE_CHANNEL_ID"])
    max_puzzles_return = int(config['db']['MAX_PUZZLES_RETURN'])
    days_to_search = int(config['db']['DAYS_TO_SEARCH'])
    reaction_threshhold = int(config['db']['REACTION_THRESHHOLD'])
    solved_emoji_name = config['db']['SOLVED_EMOJI_NAME']
    broken_emoji_name = config['db']['BROKEN_EMOJI_NAME']
    calling_bot_id = int(config['db']['CALLING_BOT_ID'])
    developer_id = int(config['db']['DEVELOPER_ID'])
    log_channel_id = int(config['db']['LOG_CHANNEL_ID'])
    sql_uri = config['db']['SQL_URI']
    sql_key = config['db']['SQL_KEY']
    server_mod_id = int(config['db']['SERVER_MOD_ID'])

_dbcontainers = {"Items":None}
def db_items():
    if (_dbcontainers["Items"] is None):
        client = CosmosClient(sql_uri, sql_key)
        database = client.get_database_client("Puzzles")
        _dbcontainers["Items"] = database.get_container_client("Items")
    return _dbcontainers["Items"]

def emojify(text):
    returntxt = ""
    for char in text:
        if char == "1":
            returntxt += "1️⃣"
        elif char == "2":
            returntxt += "2️⃣"
        elif char == "3":
            returntxt += "3️⃣"
        elif char == "4":
            returntxt += "4️⃣"
        elif char == "5":
            returntxt += "5️⃣"
        elif char == "6":
            returntxt += "6️⃣"
        elif char == "7":
            returntxt += "7️⃣"
        elif char == "8":
            returntxt += "8️⃣"
        elif char == "9":
            returntxt += "9️⃣"
        elif char == "0":
            returntxt += "0️⃣"
        elif char == "0":
            returntxt += "0️⃣"
        else:
            returntxt += char

    return returntxt
    
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default(),help_command=None)
slash = SlashCommand(bot, sync_commands=True, debug_guild=guild_id)

@slash.slash(
    name="lonelypuzzles", description="Search for puzzles which need testing", 
    options=[
        manage_commands.create_option(
            name="puzzle_type",
            description="Puzzle Type",
            required=True,
            option_type=3,
            choices=[
                manage_commands.create_choice(
                    name="Sudoku",
                    value="sudoku"
                ),
                manage_commands.create_choice(
                    name="Other Puzzles",
                    value="other"
                ),
                manage_commands.create_choice(
                    name="Word Puzzles",
                    value="word"
                ),
            ],
        ),
        manage_commands.create_option(
            name="search_terms",
            description="Words that are required to exist in the submission",
            required=False,
            option_type=3
        ),
        manage_commands.create_option(
            name="max_age",
            description="Maximum age (1 week default)",
            required=False,
            option_type=4,
            choices=[
                manage_commands.create_choice(
                    name="Day",
                    value=1
                ),
                manage_commands.create_choice(
                    name="Week",
                    value=7
                ),
                manage_commands.create_choice(
                    name="Month",
                    value=30
                ),
                manage_commands.create_choice(
                    name="Year",
                    value=365
                )
            ]
        ),
        manage_commands.create_option(
            name="solved_count",
            description="Number of people who marked it as Solved (0 default)",
            required=False,
            option_type=4
        )
    ]
)
async def _lonelypuzzles(ctx: SlashContext, puzzle_type: str, search_terms: str = "", max_age: int = days_to_search, solved_count: int = 0):
    send_channel = ctx.author.dm_channel
    if (send_channel is None):
        send_channel = await ctx.author.create_dm()

    await ctx.reply("I'm finding lonely puzzles, please check your DMs for details",hidden=True)
    
    response = await findLonelyPuzzles(puzzle_type, search_terms,max_age,solved_count,ctx.author.name)
    await send_channel.send(embed = response)

'''@bot.command()
async def lonelypuzzles(ctx,puzzle_type: str, search_terms: str = "", max_age: int = days_to_search, solved_count: int = 0):
    if (ctx.channel.id == bot_commands_channel_id):
        response = await findLonelyPuzzles(puzzle_type, search_terms,max_age,solved_count)
        await ctx.send(embed = response)'''

param_dicts_archive_name = {
        "Archive":"Archive",
        "Monthly_Archive":"Monthly Archive",
}
param_dicts_max_age = {
        1:"Day",
        7:"Week",
        30:"Month",
        365:"Year",
        99999:"No Limit",
}
param_dicts_min_age = {
        1:"Day",
        7:"Week",
        30:"Month",
        365:"Year",
        0:"No Limit",
}
param_dicts_difficulty = {
        1:"Very Easy",
        2:"Easy",
        3:"Average",
        4:"Hard",
        5:"Very Hard",
        0:"Unrated",
        -1:"No Limit",
}
param_dicts_order_by = {
        "difficulty_asc":"Difficulty (Low -> High)",
        "difficulty_desc":"Difficulty (High -> Low)",
        "rating_raw_asc":"Raw 👍⭐🌟 rating (Low -> High)",
        "rating_raw_desc":"Raw 👍⭐🌟 rating (High -> Low)",
        "rating_avg_asc":"Avg 👍⭐🌟 rating (Low -> High)",
        "rating_avg_desc":"Avg 👍⭐🌟 rating (High -> Low)",
        "reaction_count_asc":"Reaction count (Low -> High)",
        "reaction_count_desc":"Reaction count (High -> Low)",
        "beautifultheme_desc":"🌈 Beautiful theme (High -> Low)",
        "beautifullogic_desc":"❄️ Beautiful logic (High -> Low)",
        "inventivepuzzle_desc":"💡 Inventive (High -> Low)",
        "mindblowingpuzzle_desc":"🤯 Mindblowing (High -> Low)",
        "age_desc":"Age (Newest -> Oldest)",
        "age_asc":"Age (Oldest -> Newest)",
}

def list_params(param_dict):
    l = []
    for key in param_dict:
        l.append(manage_commands.create_choice(
            name=param_dict[key],
            value=key
        ))
    return l
'''
@slash.slash(
    name="searcharchive", description="Search for puzzles in the Archive or Monthly Archive on various criteria", 
    options=[
        manage_commands.create_option(
            name="archive_name",
            description="Archive Name",
            required=True,
            option_type=3,
            choices=list_params(param_dicts_archive_name)
        ),

        manage_commands.create_option(
            name="max_age",
            description="Maximum age (default No Limit)",
            required=False,
            option_type=4,
            choices=list_params(param_dicts_max_age)
        ),
        manage_commands.create_option(
            name="min_age",
            description="Minimum age (default No Limit)",
            required=False,
            option_type=4,
            choices=list_params(param_dicts_min_age)
        ),
        manage_commands.create_option(
            name="difficulty",
            description="Difficulty (default No Limit)",
            required=False,
            option_type=4,
            choices=list_params(param_dicts_difficulty)
        ),
        manage_commands.create_option(
            name="order_by",
            description="Order in which results will be displayed (default Age: Newest -> Oldest)",
            required=False,
            option_type=3,
            choices= list_params(param_dicts_order_by),
        ),

        manage_commands.create_option(
            name="search_terms",
            description="Words that are required to exist on first line of the puzzle post",
            required=False,
            option_type=3
        ),
    ]
)
'''
async def _searcharchive(ctx: SlashContext, archive_name: str, max_age: int = 99999, min_age: int = 0, difficulty: int = -1, order_by: str = "age_desc", search_terms: str = ""):

    send_channel = ctx.author.dm_channel
    if (send_channel is None):
        send_channel = await ctx.author.create_dm()

    await ctx.reply("I'm searching for puzzles, please check your DMs for details",hidden=True)
    
    #use max_age and min_age to determine from_date and to_date
    today = datetime.datetime.today().date()
    from_date = datetime.datetime(today.year, today.month, today.day) - datetime.timedelta(days = max_age)
    to_date = datetime.datetime(today.year, today.month, today.day) - datetime.timedelta(days = min_age)

    min_difficulty = difficulty
    max_difficulty = difficulty
    if difficulty == -1: #No Limit
        min_difficulty = 0
        max_difficulty = 5

    order_by_field = order_by.split("_")[0]
    order_by_direction = order_by.split("_")[1]

    response = await searchArchive(archive_name = archive_name,
                                    from_date = from_date,
                                    to_date = to_date,
                                    min_difficulty = min_difficulty,
                                    max_difficulty = max_difficulty,
                                    min_rating_raw = 0,
                                    max_rating_raw = 99999,
                                    min_rating_avg = 0,
                                    max_rating_avg = 3,
                                    order_by = order_by_field,
                                    sort_order = order_by_direction,
                                    search_terms = search_terms.split(),
                                    replytitle = "",
                                    max_results = 100,
                                    author = ctx.author.name,
                                    command_message = "/searcharchive archive_name: " + archive_name + " max_age: " + str(max_age) + " min_age: " + str(min_age) + " difficulty: " + str(difficulty) + " order_by: " + order_by + ' search_terms:"'+search_terms+'"')

    await send_channel.send(embed = response)

async def searchArchive(archive_name, max_results, from_date, to_date, min_difficulty, max_difficulty, 
                        min_rating_raw, max_rating_raw, min_rating_avg, max_rating_avg, 
                        order_by, sort_order, search_terms, replytitle, author, command_message):
    query = "SELECT top "+str(max_results)+" * FROM c where "
    conditions = []
    parameters = []

    #archive_name (one of "Archive" or "Monthly_Archive")
    channel_id = 0
    if archive_name == "Archive":
        conditions.append("c.source = 'Archive'")
        channel_id = archive_channel_id
    elif archive_name == "Monthly_Archive":
        conditions.append("c.source = 'Monthly_Archive'")
        channel_id = monthly_archive_channel_id
    else:
        print("invalid source: "+archive_name)
        return

    #   from_date (in format "dd.Month.YYYY", e.g. "21.June.2018").  Dates in UTC.
    if (from_date > datetime.datetime(2020,1,1)):
        from_date_ts = pytz.utc.localize(from_date).timestamp()  
        conditions.append("c.timestamp > "+str(from_date_ts))

    #   to_date, same format as above.  Inclusive, i.e. search results are from beginning of from_date to end of to_date.
    to_date += datetime.timedelta(days= 1)
    if (to_date < datetime.datetime.now()):
        to_date_ts = pytz.utc.localize(to_date).timestamp()  
        conditions.append("c.timestamp < "+str(to_date_ts))

    #   min_difficulty integer 0-5
    if (min_difficulty > 0):
        conditions.append("c.difficulty >= "+str(min_difficulty))

    #   max_difficulty integer 0-5 (e.g. 2 would give results with ratings up to 2.99999)
    if (max_difficulty < 5):
        conditions.append("c.difficulty < "+str(max_difficulty+1))

    #   min_rating_raw integer 0+  (e.g. 2 would give results rated 2 or higher)  Raw rating gives 1 point for goodpuzzle, 2 for greatpuzzle, 3 for exceptionalpuzzle.  No upper limit.
    if (min_rating_raw > 0):
        conditions.append("c.rating_raw >= "+str(min_rating_raw))

    #   max_rating_raw integer 0+  (e.g. 4 would give results with ratings from 0 to 4)
    conditions.append("c.rating_raw <= "+str(max_rating_raw))

    #   min_rating_avg integer 0-3 (e.g. 2 would give results rated 2 or higher)  Avg rating gives 1 point for goodpuzzle, 2 for greatpuzzle, 3 for exceptionalpuzzle, then averages based on the number of votes.
    if (min_rating_avg > 0):
        conditions.append("c.rating_avg >= "+str(min_rating_avg))

    #   max_rating_avg integer 0-3 (e.g. 1 would give results with ratings from 0 to 1)
    if (max_rating_avg < 3):
        conditions.append("c.rating_avg < "+str(max_rating_avg+1))

    #   search_terms (zero or more words that must exist in first line of puzzle submission - can include tags, author, etc.)
    #   title (zero or more words that will appear as the title of the embedded results.)
    for idx,word in enumerate(search_terms):
        conditions.append("contains(c.firstline,@s"+str(idx)+",true)")
        parameters.append({ "name":"@s"+str(idx), "value": word })

    query += " and ".join(conditions)

    #   order_by (one of "difficulty","rating_avg","rating_raw","reaction_count","beautifultheme","beautifullogic","inventivepuzzle","mindblowingpuzzle","age")
    if order_by.lower() in ("difficulty","rating_avg","rating_raw","reaction_count","beautifultheme","beautifullogic","inventivepuzzle","mindblowingpuzzle"):
        query += " order by c."+order_by
    elif order_by.lower() == "age":
        query += " order by c.timestamp"
    else:
        print("invalid order_by: "+order_by)
        return

    #   sort_order (one of "asc", "desc")
    if sort_order.lower() in ("asc", "desc"):
        query += " "+sort_order
    else:
        print("invalid sort_order: "+sort_order)
        return

    #print(query)
    #print(parameters)

    items_container = db_items()
    items = list(items_container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))

    #request_charge = items_container.client_connection.last_response_headers['x-ms-request-charge']
    #print('Query returned {0} items. Operation consumed {1} request units'.format(len(items), request_charge))

    replymsg=""

    if (len(items)==0):
        replymsg = "No results found for the given parameters."
    replyfooter = ""

    difficulty_str = ""
    if (min_difficulty == 0 and max_difficulty == 5):
        difficulty_str = param_dicts_difficulty[-1]
    elif (min_difficulty == max_difficulty ):
        difficulty_str = param_dicts_difficulty[min_difficulty]
    else:
        difficulty_str = param_dicts_difficulty[min_difficulty] + " - " + param_dicts_difficulty[max_difficulty]
    pseudofooter = "\n\nSearch Parameters: " + \
    "Archive_name = " + param_dicts_archive_name[archive_name]+ \
    ", \nDate = " + from_date.strftime("%d %B %Y") +" - " +to_date.strftime("%d %B %Y")+ \
    ", \nDifficulty = " + difficulty_str + \
    (', \nSearch Terms = "' + ' '.join(search_terms) + '"' if len(search_terms)>0 else "") + \
    "\n\nCurious?  Check out [how to search the archive](https://www.google.com)"
    
    idx = 0
    for item in items:
        idx += 1
        indexer = "•"
        if max_results < 100:
            indexer = str(idx)+"."
        #print (item)
        firstline = item['firstline']
        author = ""
        if channel_id != archive_channel_id:
            firstline = firstline[:50]
            author = " by "+str(item['author'])
        itemmsg ="\n"+indexer+" [" + firstline + "](https://discord.com/channels/"+guild_id+"/"+str(channel_id)+"/" + str(item['id']) + ")" + author + \
            "\n⠀⠀" + str(round(item['difficulty'],1))+"/5"
            #"\n⠀⠀**" + emojify(str(round(item['difficulty'],1)))+"**"
        #if (item['goodpuzzle']>0):
        #    itemmsg+="⠀👍"+str(item['goodpuzzle'])
        #if (item['greatpuzzle']>0):
        #    itemmsg+="⠀⭐"+str(item['greatpuzzle'])
        #if (item['exceptionalpuzzle']>0):
        #    itemmsg+="⠀🌟"+str(item['exceptionalpuzzle'])
        
        #use average rating to display a star rating, then show how many reacted.
        star_reacts = str(item['goodpuzzle']+item['greatpuzzle']+item['exceptionalpuzzle'])
        if (item['rating_avg']>=2.5):
            itemmsg+="⠀🌟"+star_reacts
        elif (item['rating_avg']>=1.5):
            itemmsg+="⠀⭐"+star_reacts
        elif (item['rating_avg']>=0.5):
            itemmsg+="⠀👍"+star_reacts

        if (item['beautifultheme']>0):
            itemmsg+="⠀🌈"+str(item['beautifultheme'])
        if (item['beautifullogic']>0):
            itemmsg+="⠀❄️"+str(item['beautifullogic'])
        if (item['inventivepuzzle']>0):
            itemmsg+="⠀💡"+str(item['inventivepuzzle'])
        if (item['mindblowingpuzzle']>0):
            itemmsg+="⠀🤯"+str(item['mindblowingpuzzle'])
        if (len(replymsg) + len(itemmsg) + len(pseudofooter) < 4096):
            replymsg+= itemmsg
        else:
            replyfooter = "... and "+str(len(items) - idx)+" more"
            break

    if replytitle == "":
        replytitle = "Found "+str(len(items))+" puzzles, ordered by "+param_dicts_order_by[order_by+"_"+sort_order]+":"
            
    embed = discord.Embed(title = replytitle)
    embed.description = replymsg + pseudofooter
    if replyfooter != "":
        embed.set_footer(text=replyfooter)
    #todo: handle overflow and put "...and X more" in footer.  
    #todo: put full parameter list (looking like slash commands) in footer.

    await logUsage(author, len(items), command_message)

    return embed

@bot.listen()
async def on_message(message):

    #check for archive numbers incrementing properly.
    if message.channel.id == archive_channel_id:
        puzzle_id = 0
        warning_msg = ""
        if message.content.startswith("["):
            try:
                puzzle_id = int(message.content.split("]")[0].lstrip("["))
            except:
                return
                
            async for msg in message.channel.history(limit=2):
                if message.id != msg.id:
                    previous_puzzle_id = int(msg.content.split("]")[0].lstrip("["))
                    if puzzle_id != previous_puzzle_id + 1:
                        warning_msg = "Your recent submission to the puzzle archive has an invalid Entry #.  Your post must begin with '["+str(previous_puzzle_id+1)+"]'.  Please edit your post to have the correct entry number.  Thanks!"
        if warning_msg != "":
            send_channel = message.author.dm_channel
            if (send_channel is None):
                send_channel = await message.author.create_dm()
            await send_channel.send(warning_msg)
            
            server_mod = await bot.fetch_user(server_mod_id) 
            send_channel = server_mod.dm_channel
            if (send_channel is None):
                send_channel = await server_mod.create_dm()
            await send_channel.send("Message sent to "+message.author.name+": \n"+warning_msg)

    #print(message.author.id)
    #if it mentions me, process like a command.
    if (bot.user in message.mentions and bot.user != message.author):
        send_channel = message.channel
        if (message.author.id not in (calling_bot_id,developer_id)):
            send_channel = message.author.dm_channel
            if (send_channel is None):
                send_channel = await message.author.create_dm()
                
        args = message.content.split()
        if (message.author.id in (developer_id,calling_bot_id) and args[1]=="echo"):

            await message.channel.send(embed=discord.Embed(description=message.content))

            return
        elif (message.author.id in (developer_id,calling_bot_id) and len(args)==2 and args[1]=="updatepins"):
            #updates pins in this channel
            for msg in await message.channel.pins():
                if (msg.pinned and msg.author == bot.user and len(msg.embeds)>0):
                    titleargs = msg.embeds[0].title.split(' ')
                    
                    puzzle_type=''
                    max_age=7
                    solved_count=0
                    search_terms=[]
                    finding_search_terms=False
                    while len(titleargs)>0:
                        arg = titleargs.pop(0)
                        if (puzzle_type == '' and arg in ['sudoku','other','word']):
                            puzzle_type = arg
                        elif(arg == 'past'):
                            max_age = int(titleargs.pop(0))
                        elif(arg == '≤'):
                            solved_count = int(titleargs.pop(0))
                        elif(arg[0] == '"'):
                            finding_search_terms = True

                        if (finding_search_terms):
                            if (arg[-1]=='"'):
                                finding_search_terms=False
                                search_terms.append(arg[:-1])
                                search_terms[0]=search_terms[0][1:]
                            elif (arg[-2]=='"'):
                                finding_search_terms=False
                                search_terms.append(arg[:-2])
                                search_terms[0]=search_terms[0][1:]
                            else:
                                search_terms.append(arg)

                    response = await findLonelyPuzzles(puzzle_type, ' '.join(search_terms),max_age,solved_count,"updating pins")
                    await msg.edit(embed = response)
            return
        elif (message.author.id in (developer_id,calling_bot_id) and args[1]=="downloaddb"):

            fields = [
                "id",
                "source",
                "timestamp",
                "difficulty_1",
                "difficulty_2",
                "difficulty_3",
                "difficulty_4",
                "difficulty_5",
                "difficulty",
                "goodpuzzle",
                "greatpuzzle",
                "exceptionalpuzzle",
                "rating_raw",
                "rating_avg",
                "reaction_count",
                "beautifultheme",
                "beautifullogic",
                "inventivepuzzle",
                "mindblowingpuzzle",
                "author",
                "firstline",
            ]
            myCSV = ",".join(fields)
            
            foundPuzzlesCount = 0
            for item in db_items().query_items(
                query="select * from c order by c.source, c.id",
                enable_cross_partition_query=True
            ):
                foundPuzzlesCount += 1
                myCSV += "\n"
                for field in fields:
                    myCSV += str(item[field])+","
            
            await message.channel.send("",files=[discord.File(io.StringIO(myCSV),"PuzzleDigest_"+str(datetime.datetime.now())+".csv")])
            await logUsage(message.author.name, foundPuzzlesCount, "downloaddb")

        elif (message.author.id in (developer_id,calling_bot_id) and len(args)==5 and args[1]=="updatedb"):
            #updates DB stats for archive and monthly archive, based on from_date and to_date.
            #requires channel (one of "Archive","Monthly_Archive"), from_date (in format "dd.Month.YYYY", e.g. "21.June.2018"), to_date.  
            #dates will be inclusive: i.e. beginning of from_date to end of to_date.
            #possible setups: every day, update past week's stats.  every week, update past month's stats.  Every month, update last years stats.

            channel_id = 0
            if args[2] == "Archive":
                channel_id = archive_channel_id
            elif args[2] == "Monthly_Archive":
                channel_id = monthly_archive_channel_id
            else:
                return

            from_date = datetime.datetime.strptime(args[3], "%d.%B.%Y")
            to_date = datetime.datetime.strptime(args[4], "%d.%B.%Y") + datetime.timedelta(days= 1)
            
            print(str(datetime.datetime.now().time())+ ": Getting and processing messages:")
            puzzcount = 0

            async for msg in bot.get_channel(channel_id).history(after=from_date,before=to_date,limit=None):
                difficulty_1 = 0
                difficulty_2 = 0
                difficulty_3 = 0
                difficulty_4 = 0
                difficulty_5 = 0
                goodpuzzle = 0
                greatpuzzle = 0
                exceptionalpuzzle = 0
                beautifultheme = 0
                beautifullogic = 0
                inventivepuzzle = 0
                mindblowingpuzzle = 0
                for reaction in msg.reactions:
                    emoji = reaction.emoji
                    if (reaction.custom_emoji):
                        emoji = reaction.emoji.name

                    if emoji == "1️⃣":
                        difficulty_1 = reaction.count
                    elif emoji == "2️⃣":
                        difficulty_2 = reaction.count
                    elif emoji == "3️⃣":
                        difficulty_3 = reaction.count
                    elif emoji == "4️⃣":
                        difficulty_4 = reaction.count
                    elif emoji == "5️⃣":
                        difficulty_5 = reaction.count
                    elif emoji in ("goodpuzzle","👍"):
                        goodpuzzle += reaction.count
                    elif emoji in ("greatpuzzle","⭐"):
                        greatpuzzle += reaction.count
                    elif emoji in ("exceptionalpuzzle","🌟"):
                        exceptionalpuzzle += reaction.count
                    elif emoji in ("beautifultheme","🌈"):
                        beautifultheme += reaction.count
                    elif emoji in ("beautifullogic","❄️"):
                        beautifullogic += reaction.count
                    elif emoji in ("inventivepuzzle","💡"):
                        inventivepuzzle += reaction.count
                    elif emoji in ("mindblowingpuzzle","🤯"):
                        mindblowingpuzzle += reaction.count

                if difficulty_1 > 0 and difficulty_2 > 0 and difficulty_3 > 0 and difficulty_4 > 0 and difficulty_5 > 0:
                    firstline = "untitled"
                    if (msg.content != ""):
                        firstline = msg.content.splitlines()[0].replace("~","").replace("*","").replace("_","")[:1000]

                    difficulty_1 -= reaction_threshhold
                    difficulty_2 -= reaction_threshhold
                    difficulty_3 -= reaction_threshhold
                    difficulty_4 -= reaction_threshhold
                    difficulty_5 -= reaction_threshhold
                    difficulty = 0
                    if ((difficulty_1 + difficulty_2 + difficulty_3 + difficulty_4 + difficulty_5)>0):
                        difficulty = (difficulty_1 * 1 + difficulty_2 * 2 + difficulty_3 * 3 + difficulty_4 * 4 + difficulty_5 * 5) \
                            / (difficulty_1 + difficulty_2 + difficulty_3 + difficulty_4 + difficulty_5)

                    goodpuzzle -= reaction_threshhold
                    greatpuzzle -= reaction_threshhold
                    exceptionalpuzzle -= reaction_threshhold
                    rating_raw = goodpuzzle + greatpuzzle * 2 + exceptionalpuzzle * 3
                    rating_avg = 0
                    if ((goodpuzzle + greatpuzzle + exceptionalpuzzle)>0):
                        rating_avg = (goodpuzzle + greatpuzzle * 2 + exceptionalpuzzle * 3)/(goodpuzzle + greatpuzzle + exceptionalpuzzle)

                    beautifultheme -= reaction_threshhold
                    beautifullogic -= reaction_threshhold
                    inventivepuzzle -= reaction_threshhold
                    mindblowingpuzzle -= reaction_threshhold

                    reaction_count = goodpuzzle+greatpuzzle+exceptionalpuzzle+beautifultheme+beautifullogic+inventivepuzzle+mindblowingpuzzle

                    puzzlemessage = {
                            "id" : str(msg.id),
                            "source": args[2],
                            "timestamp" : pytz.utc.localize(msg.created_at).timestamp(),
                            "firstline" : firstline,
                            "author" : msg.author.name,
                            "difficulty_1" : difficulty_1,
                            "difficulty_2" : difficulty_2,
                            "difficulty_3" : difficulty_3,
                            "difficulty_4" : difficulty_4,
                            "difficulty_5" : difficulty_5,
                            "difficulty" : difficulty,
                            "goodpuzzle" : goodpuzzle,
                            "greatpuzzle" : greatpuzzle,
                            "exceptionalpuzzle" : exceptionalpuzzle,
                            "rating_raw" : rating_raw,
                            "rating_avg" : rating_avg,
                            "reaction_count" : reaction_count,
                            "beautifultheme" : beautifultheme,
                            "beautifullogic" : beautifullogic,
                            "inventivepuzzle" : inventivepuzzle,
                            "mindblowingpuzzle" : mindblowingpuzzle,
                        }
                    #from pprint import pprint
                    #pprint(puzzlemessage)
                    puzzcount += 1
                    if puzzcount % 10 == 0:
                        print(puzzcount)
                    db_items().upsert_item(body=puzzlemessage)

            print(str(datetime.datetime.now().time())+ ": Uploaded "+str(puzzcount)+" puzzles")
            await logUsage(message.author.name, puzzcount, " ".join(args[1:]))

            return
        elif (len(args)>=14 and args[1]=="searcharchive"):
            # searches archives for puzzles fitting the criteria.  
            # e.g. Top ten mindblowing tapas of all time "@PuzzleDigestBot search Archive 21.June.2000 1.December.2021 0 5 0 99999 0 3 mindblowingpuzzle desc 10 tapa title=Show Me"
            # Parameters:
            #   archive_name (one of "Archive" or "Monthly_Archive")
            #   from_date (in format "dd.Month.YYYY", e.g. "21.June.2018").  Dates in UTC.
            #   to_date, same format as above.  Inclusive, i.e. search results are from beginning of from_date to end of to_date.
            #   min_difficulty integer 0-5
            #   max_difficulty integer 0-5 (e.g. 2 would give results with ratings up to 2.99999)
            #   min_rating_raw integer 0+  (e.g. 2 would give results rated 2 or higher)  Raw rating gives 1 point for goodpuzzle, 2 for greatpuzzle, 3 for exceptionalpuzzle.  No upper limit.
            #   max_rating_raw integer 0+  (e.g. 4 would give results with ratings up to 4)
            #   min_rating_avg integer 0-3 (e.g. 2 would give results rated 2 or higher)  Avg rating gives 1 point for goodpuzzle, 2 for greatpuzzle, 3 for exceptionalpuzzle, then averages based on the number of votes.
            #   max_rating_avg integer 0-3 (e.g. 1 would give results with ratings up to 1.99999)
            #   order_by (one of "difficulty","rating_avg","rating_raw","reaction_count","beautifultheme","beautifullogic","inventivepuzzle","mindblowingpuzzle","age")
            #   sort_order (one of "asc", "desc")
            #   max_results integer
            #   search_terms (zero or more words that must exist in first line of puzzle submission - can include tags, author, etc.)
            #   title (zero or more words that will appear as the title of the embedded results.  This parameter alone must be preceded by its name: e.g. "title=Show Me")

            search_terms = []
            replytitle = ""
            found_title = False
            for idx,word in enumerate(args[14:]):
                if not found_title:
                    if word.startswith("title="):
                        found_title = True
                        replytitle += word.lstrip("title=")
                    else:
                        search_terms.append(word)
                else:
                    replytitle += " "+word

            response = await searchArchive(archive_name = args[2],
                                            from_date = datetime.datetime.strptime(args[3], "%d.%B.%Y"),
                                            to_date = datetime.datetime.strptime(args[4], "%d.%B.%Y") ,
                                            min_difficulty = int(args[5]),
                                            max_difficulty = int(args[6]),
                                            min_rating_raw = int(args[7]),
                                            max_rating_raw = int(args[8]),
                                            min_rating_avg = int(args[9]),
                                            max_rating_avg = int(args[10]),
                                            order_by = args[11],
                                            sort_order = args[12],
                                            search_terms = search_terms,
                                            replytitle = replytitle,
                                            max_results = int(args[13]),
                                            author = message.author.name,
                                            command_message = " ".join(args[1:]))

            await send_channel.send(embed = response)

            return
        else:
            helpmsg = "Format message like: ```@PuzzleDigestBot lonelypuzzles puzzle_type max_age solved_count search terms```\npuzzle_type is 'sudoku', 'word', or 'other'  \nmax_age and solved_count must be integers.  \nSearch terms are optional, and not in quotes."

            if len(args) > 4:
                if args[1] == 'lonelypuzzles':
                    puzzle_type = args[2]
                    max_age = 0
                    try:
                        max_age = int(args[3])
                    except ValueError:
                        await send_channel.send(embed = discord.Embed(description='max_age is not an integer.\n'+helpmsg))
                        return

                    solved_count = 0
                    try:
                        solved_count = int(args[4])
                    except ValueError:
                        await send_channel.send(embed = discord.Embed(description='solved_count is not an integer.\n'+helpmsg))
                        return

                    search_terms = " ".join(args[5:])
                    response = await findLonelyPuzzles(puzzle_type, search_terms,max_age,solved_count,message.author.name)
                    await send_channel.send(embed = response)
                else:
                    await send_channel.send(embed = discord.Embed(description='No command given.\n'+helpmsg))
            else:
                await send_channel.send(embed = discord.Embed(description='Insufficient arguments given.\n'+helpmsg))

async def findLonelyPuzzles(puzzle_type, search_terms,max_age,solved_count, author):
    search_channel_id = 0
    if puzzle_type == 'sudoku':
        search_channel_id = sudoku_submissions_channel_id

    if puzzle_type == 'other':
        search_channel_id = other_submissions_channel_id

    if puzzle_type == 'word':
        search_channel_id = word_submissions_channel_id

    if search_channel_id > 0:
        replymsg = ''
        foundPuzzles = []

        searchTermsList = search_terms.lower().split()

        from_date = datetime.datetime.now() - datetime.timedelta(days= max_age)
        async for msg in bot.get_channel(search_channel_id).history(after=from_date,limit=None):
            try:
                solvedcnt = 0
                brokencnt = 0
                for reaction in msg.reactions:
                    if (reaction.custom_emoji):
                        if (reaction.emoji.name == solved_emoji_name):
                            solvedcnt += reaction.count
                        elif (reaction.emoji.name == broken_emoji_name):
                            brokencnt += reaction.count

                if solvedcnt <= reaction_threshhold + solved_count and brokencnt == reaction_threshhold:
                    #check search_terms
                    msgContentToSearch = msg.content.lower()
                    hasAllTerms = True
                    if (len(searchTermsList)>0):
                        for term in searchTermsList:
                            if term not in msgContentToSearch:
                                hasAllTerms = False
                                break
                    if hasAllTerms:
                        #post first line of text (up to 50 characters) linking to the message.
                        firstLine = msg.content.splitlines()[0].replace("~","").replace("*","").replace("_","")[:50]
                        foundPuzzles.append("\n• "+("("+str(solvedcnt - reaction_threshhold)+") " if solved_count > 0 else "")+ \
                            "[" + firstLine + "](https://discord.com/channels/"+guild_id+"/"+str(msg.channel.id)+"/" + str(msg.id) + ") by "+msg.author.name)
            except:
                print("Failed to process message:")
                print(msg)
                traceback.print_exc()

        if len(foundPuzzles) == 0:
            replymsg = "No puzzles found matching the criteria."

        foundPuzzlesCount = len(foundPuzzles)
        listedPuzzlesCount = 0
        while len(foundPuzzles) > 0 and len(replymsg+foundPuzzles[0])<4096 and listedPuzzlesCount < max_puzzles_return:
            replymsg += foundPuzzles.pop(0)
            listedPuzzlesCount += 1

        replytitle = str(foundPuzzlesCount)+' '+("Untested " if solved_count == 0 else '') + \
            puzzle_type+" puzzle"+("" if foundPuzzlesCount == 1 else "s") + \
            " in the past "+str(max_age)+" day" + ("" if max_age == 1 else "s" ) + \
            (' containing "' + search_terms +'"' if search_terms != "" else "") + \
            (" with ≤ "+str(solved_count)+" solve" + ("" if solved_count == 1 else "s") if solved_count != 0 else "") + \
            ":"
        embed = discord.Embed(title=replytitle)
        embed.description=replymsg
        if len(foundPuzzles) > 0:
            embed.set_footer(text="... and "+str(len(foundPuzzles))+" more")

        await logUsage(author, foundPuzzlesCount, "lonelypuzzles " + puzzle_type + " " + str(max_age) + " " + str(solved_count) + " " + search_terms)
        return embed

@bot.event
async def on_ready():
    print('{0.user} has logged in'.format(bot))

async def logUsage(author, found_count, command_message):
    log_channel = await bot.fetch_channel(log_channel_id)
    #get most recent Log message by this bot there.  Either edit it or create new one.
    log_title = "Log "+datetime.datetime.now(datetime.timezone.utc).strftime("%m/%d/%Y")
    log_message = None

    async for msg in log_channel.history():
        if (msg.author == bot.user and len(msg.embeds)>0 and msg.embeds[0].title == log_title):
            log_message = msg
            break

    embed = discord.Embed(title=log_title)
    embed.description=datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")+" "+author+" " +"("+str(found_count)+"): "+command_message

    if (log_message == None or len(log_message.embeds[0].description) > 3500):
        await log_channel.send(embed = embed)
    else:
        embed.description=log_message.embeds[0].description+'\n'+embed.description
        await log_message.edit(embed = embed)
        #await log_message.delete()


#bot.run(other_access_token)
bot.run(access_token)


