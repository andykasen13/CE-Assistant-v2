import asyncio
import datetime
import functools
import typing
from discord.ext import tasks
import discord
from Classes.CE_User import CEUser
from Classes.CE_User_Game import CEUserGame
from Classes.CE_User_Objective import CEUserObjective
from Classes.CE_Game import CEAPIGame, CEGame
from Classes.OtherClasses import UpdateMessage
from Exceptions.FailedScrapeException import FailedScrapeException
from Modules import CEAPIReader, Discord_Helper, Mongo_Reader
from Modules.Screenshot import Screenshot
import Modules.hm as hm


# selenium and beautiful soup stuff
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import io
from PIL import Image

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


def check_category_roles(old_games : list[CEUserGame], new_games : list[CEUserGame],
                         database_name : list[CEGame], user : CEUser
                         ) -> list[UpdateMessage] :
    "Takes in the old and newly completed games and returns a list of `UpdateMessage`s to send."

    # ----- set up variables -----
    oldt1s, oldt2s, oldt3s, oldt4s, oldt5s = (0,)*5
    oldac, oldar, oldbh, oldfp, oldpl, oldst = (0,)*6
    newt1s, newt2s, newt3s, newt4s, newt5s = (0,)*5
    newac, newar, newbh, newfp, newpl, newst = (0,)*6
    updates : list[UpdateMessage] = []

    # ----- sort old games -----
    for game in old_games :
        points = game.get_user_points() # grab the points
        database_game = hm.get_item_from_list(game.ce_id, database_name) # get the official game
        
        # if the game was deleted, continue
        if database_game == None : continue

        if game.is_completed(database_name) :
            match(database_game.get_tier()) :
                case "Tier 1" : oldt1s += points
                case "Tier 2" : oldt2s += points
                case "Tier 3" : oldt3s += points
                case "Tier 4" : oldt4s += points
                case "Tier 5" : oldt5s += points
                case "Tier 6" : oldt5s += points # t6
                case "Tier 7" : oldt5s += points # t7

        
        match(database_game.category) :
            case "Action" : oldac += points
            case "Arcade" : oldar += points
            case "Bullet Hell" : oldbh += points
            case "First-Person" : oldfp += points
            case "Platformer" : oldpl += points
            case "Strategy" : oldst += points

    # ----- sort new games -----
    for game in new_games :
        points = game.get_user_points()
        database_game = hm.get_item_from_list(game.ce_id, database_name)
        if database_game == None : continue
        if game.is_completed(database_name) :
            match(database_game.get_tier()) :
                case "Tier 1" : newt1s += points
                case "Tier 2" : newt2s += points
                case "Tier 3" : newt3s += points
                case "Tier 4" : newt4s += points
                case "Tier 5" : newt5s += points
                case "Tier 6" : newt5s += points # t6
                case "Tier 7" : newt5s += points # t7
        match(database_game.category) :
            case "Action" : newac += points
            case "Arcade" : newar += points
            case "Bullet Hell" : newbh += points
            case "First-Person" : newfp += points
            case "Platformer" : newpl += points
            case "Strategy" : newst += points

    old_categories = (oldac, oldar, oldbh, oldfp, oldpl, oldst)
    new_categories = (newac, newar, newbh, newfp, newpl, newst)
    old_tiers = (oldt1s, oldt2s, oldt3s, oldt4s, oldt5s)
    new_tiers = (newt1s, newt2s, newt3s, newt4s, newt5s)

    CATEGORY_ROLE_NAMES = ["Master", "Grandmaster", "Grandmaster (Black Role)"]

    # ----- actually check -----
    # categories
    for point_index, point_value in enumerate([500, 1000, 2000]) :
        for i, category in enumerate(list(typing.get_args(hm.CATEGORIES))) :
            if old_categories[i] < point_value and new_categories[i] >= point_value :
                updates.append(UpdateMessage(
                    location="log",
                    message=(f"Congratulations to <@{user.discord_id}>! " +
                             f"You have unlocked {category} {CATEGORY_ROLE_NAMES[point_index]} ({point_value}+ points)")
                ))
    # tiers
    for i in range(1, 6) : # 1, 2, 3, 4, 5
        #if    oldt1s       < 500   and    newt1s        >= 500
        if old_tiers[i - 1] < i*500 and new_tiers[i - 1] >= i * 500 :
            updates.append(UpdateMessage(
                location="log",
                message=(
                    f"Congratulations to <@{user.discord_id}>! " +
                    f"You have unlocked Tier {i} Enthusiast ({i * 500} points in Tier {i} completed games)."
                )
            ))

    return updates


def user_update(user : CEUser, site_data : CEUser, database_name : list[CEGame], database_user : list[CEUser]) -> tuple[list[UpdateMessage], CEUser, list[CEUser]] :
    """Takes in a user and updates it, and returns a list of things to send."""
    updates : list[UpdateMessage] = []
    # if a partner needs to be returned, it'll be placed here
    partners : list[CEUser] = []
    

    original_points = user.get_total_points()
    original_completed_games = user.get_completed_games_2(database_name)
    original_rank = user.get_rank()
    original_games = user.owned_games

    user.owned_games = site_data.owned_games

    new_points = user.get_total_points()
    new_completed_games = user.get_completed_games_2(database_name)
    new_rank = user.get_rank()
    new_games = user.owned_games

    # get the role messages
    updates += (check_category_roles(original_games, new_games, database_name, user))

    # search for newly completed games
    for game in new_completed_games :

        # if game is too low anyway, skip it
        TIER_MINIMUM = 4
        """int: The minimum tier for a game to be reported."""
        
        if not game.get_tier_num() >= TIER_MINIMUM : continue

        # check to see if it was completed before
        completed_before = False
        for old_game in original_completed_games :
            # it was completed before, so skip this
            if game.ce_id == old_game.ce_id : 
                completed_before = True
        if completed_before : continue
        
        updates.append(UpdateMessage(
            location="log",
            message=(f"Wow <@{user.discord_id}>! You've completed {game.game_name}, a {game.get_tier_emoji()} " + 
                     f"worth {game.get_total_points()} points {hm.get_emoji('Points')}!")
        ))

    # rank update
    if new_rank != original_rank and new_points > original_points :
        updates.append(UpdateMessage(
            location="log",
            message=(f"Congrats to <@{user.discord_id}> for ranking up from Rank {hm.get_emoji(original_rank)} " +
                     f"to Rank {hm.get_emoji(new_rank)}!")
        ))

    # check cooldowns
    for i, cooldown in enumerate(user.cooldowns) :
        if cooldown.end_time <= hm.get_unix('now') :
            updates.append(UpdateMessage(
                location="casino",
                message=f"<@{user.discord_id}>, your {cooldown.roll_name} cooldown has ended."
            ))
            del user.cooldowns[i]
    
    # check pendings
    for i, pending in enumerate(user.pending_rolls) :
        if pending.end_time <= hm.get_unix('now') :
            del user.pending_rolls[i]

    # check rolls
    for index, roll in enumerate(user.current_rolls) :
        # step 0: check multistage rolls
        # if the roll is multi stage AND its not in the final stage...
        # note: skip this if we're in the final stage because
        #       if it's in its final stage we can finish it out,
        #       this if statement just preps for the next one.
        if (roll.is_multi_stage() and not roll.in_final_stage() and 
            (roll.is_won(database_name=database_name, database_user=database_user))) :
            # if we've already hit this roll before, keep moving
            if roll.due_time == None : continue

            # add the update message
            updates.append(UpdateMessage(
                location="casino",
                message=(
                    f"<@{user.discord_id}>, you've finished your current stage in {roll.roll_name}. " +
                    f"To roll your next stage, type `/solo-roll {roll.roll_name}` in <#{hm.CASINO_ID}>."
                )
            ))

            # and kill the due time
            roll.due_time = None

        elif roll.is_won(database_name=database_name, database_user=database_user) :
            # add the update message
            updates.append(UpdateMessage(
                location="log",
                message=(
                    roll.get_win_message(database_name=database_name, database_user=database_user)
                )
            ))
            # set the completed time to now
            roll.completed_time = hm.get_unix("now")

            # add the object to completed rolls, and
            # remove it from current
            user.add_completed_roll(roll)
            del user.current_rolls[index]

            if roll.is_co_op() :
                partner = hm.get_item_from_list(roll.partner_ce_id, database_user)
                partner_roll = partner.get_current_roll(roll.roll_name)
                if roll.is_pvp() : partner_roll.winner = not roll.winner
                partner.remove_current_roll(partner_roll.roll_name)
                partner_roll.completed_time = hm.get_unix('now')
                partner.add_completed_roll(partner_roll)
                partners.append(partner)

        
        elif roll.is_expired() :
            # add the update message
            updates.append(UpdateMessage(
                location="casino",
                message=(
                    roll.get_fail_message(database_name=database_name, database_user=database_user)
                )
            ))
            
            # remove this roll from current rolls
            del user.current_rolls[index]
            if roll.is_co_op() :
                partner = hm.get_item_from_list(roll.partner_ce_id, database_user)
                partner.remove_current_roll(roll.roll_name)
                partners.append(partner)
    
    return (updates, user, partners)






def get_image(driver : webdriver.Chrome, new_game) -> io.BytesIO :
    "Takes in the `driver` (webdriver) and the game's `ce_id` and returns an image to be screenshotted."

    # set type hinting
    from Classes.CE_Game import CEGame, CEAPIGame
    new_game : CEGame = new_game

    OBJECTIVE_LIMIT = 7
    "The maximum amount of objectives to be screenshot before cropping." 

    # initiate selenium
    url = f"https://cedb.me/game/{new_game.ce_id}/"
    driver.get(url)
    
    # set up variables
    start_time = hm.get_unix('now')
    timeout = hm.get_unix('now') - start_time > 5
    objective_list = []

    # give it five seconds to load the elements.
    while (len(objective_list) < 1 or not objective_list[0].is_displayed()) and not timeout :
        # run this to just fully load the page...
        html_page = driver.execute_script("return document.documentElement.innerHTML;")
        # ...and now get the list.
        objective_list = driver.find_elements(By.CLASS_NAME, "bp4-html-table-striped")
        timeout = hm.get_unix('now') - start_time > 5
    
    # if it took longer than 5 seconds, just return the image failed image.
    if timeout : return "Assets/image_failed.png"

    primary_table = driver.find_element(By.CLASS_NAME, "css-c4zdq5")
    objective_list = primary_table.find_elements(By.CLASS_NAME, "bp4-html-table-striped")
    title = driver.find_element(By.TAG_NAME, "h1")
    top_left = driver.find_element(By.CLASS_NAME, "GamePage-Header-Image").location
    title_size = title.size['width']
    title_location = title.location['x']

    bottom_right = objective_list[len(objective_list)-2].location
    size = objective_list[len(objective_list)-2].size

    objective_list[0]

    header_elements = [
        'bp4-navbar',
        'tr-fadein',
        'css-1ugviwv'
    ]

    BORDER_WIDTH = 15*2

    #NOTE: i multiplied these by two. dk why it's working.
    top_left_x = (top_left['x'])*2 - BORDER_WIDTH
    top_left_y = (top_left['y'])*2 - BORDER_WIDTH
    bottom_right_y = (bottom_right['y'] + size['height'])*2 + BORDER_WIDTH

    if title_location + title_size > bottom_right['x'] + size['width']:
        bottom_right_x = (title_location + title_size)*2 + BORDER_WIDTH
    else:
        bottom_right_x = (bottom_right['x'] + size['width'])*2 + BORDER_WIDTH

    ob = Screenshot(bottom_right_y)
    im = ob.full_screenshot(driver, save_path=r'Pictures/', image_name="ss.png", 
                            is_load_at_runtime=True, load_wait_time=10, hide_elements=header_elements)
    im = io.BytesIO(im)
    im_image = Image.open(im)

    SAVE_FULL_IMAGE_LOCALLY = False
    if SAVE_FULL_IMAGE_LOCALLY :
        im_image.save('ss.png')

    im_image = im_image.crop((top_left_x, top_left_y, bottom_right_x, bottom_right_y))

    imgByteArr = io.BytesIO()
    im_image.save(imgByteArr, format='PNG')
    final_im = imgByteArr.getvalue()
    ss = io.BytesIO(final_im)

    SAVE_CROPPED_IMAGE_LOCALLY = False

    if SAVE_CROPPED_IMAGE_LOCALLY :
        im_image.save('ss.png')

    return ss


utc = datetime.timezone.utc
times = [
  datetime.time(hour=0, minute=0, tzinfo=utc),
  datetime.time(hour=0, minute=30, tzinfo=utc),
  datetime.time(hour=1, minute=0, tzinfo=utc),
  datetime.time(hour=1, minute=30, tzinfo=utc),
  datetime.time(hour=2, minute=0, tzinfo=utc),
  datetime.time(hour=2, minute=30, tzinfo=utc),
  datetime.time(hour=3, minute=0, tzinfo=utc),
  datetime.time(hour=3, minute=30, tzinfo=utc),
  datetime.time(hour=4, minute=0, tzinfo=utc),
  datetime.time(hour=4, minute=30, tzinfo=utc),
  datetime.time(hour=5, minute=0, tzinfo=utc),
  datetime.time(hour=5, minute=30, tzinfo=utc),
  datetime.time(hour=6, minute=0, tzinfo=utc),
  datetime.time(hour=6, minute=30, tzinfo=utc),
  datetime.time(hour=7, minute=0, tzinfo=utc),
  datetime.time(hour=7, minute=30, tzinfo=utc),
  datetime.time(hour=8, minute=0, tzinfo=utc),
  datetime.time(hour=8, minute=30, tzinfo=utc),
  datetime.time(hour=9, minute=0, tzinfo=utc),
  datetime.time(hour=9, minute=30, tzinfo=utc),
  datetime.time(hour=10, minute=0, tzinfo=utc),
  datetime.time(hour=10, minute=30, tzinfo=utc),
  datetime.time(hour=11, minute=0, tzinfo=utc),
  datetime.time(hour=11, minute=30, tzinfo=utc),
  datetime.time(hour=12, minute=0, tzinfo=utc),
  datetime.time(hour=12, minute=30, tzinfo=utc),
  datetime.time(hour=13, minute=0, tzinfo=utc),
  datetime.time(hour=13, minute=30, tzinfo=utc),
  datetime.time(hour=14, minute=0, tzinfo=utc),
  datetime.time(hour=14, minute=30, tzinfo=utc),
  datetime.time(hour=15, minute=0, tzinfo=utc),
  datetime.time(hour=15, minute=30, tzinfo=utc),
  datetime.time(hour=16, minute=0, tzinfo=utc),
  datetime.time(hour=16, minute=30, tzinfo=utc),
  datetime.time(hour=17, minute=0, tzinfo=utc),
  datetime.time(hour=17, minute=30, tzinfo=utc),
  datetime.time(hour=18, minute=0, tzinfo=utc),
  datetime.time(hour=18, minute=30, tzinfo=utc),
  datetime.time(hour=19, minute=0, tzinfo=utc),
  datetime.time(hour=19, minute=30, tzinfo=utc),
  datetime.time(hour=20, minute=0, tzinfo=utc),
  datetime.time(hour=20, minute=30, tzinfo=utc),
  datetime.time(hour=21, minute=0, tzinfo=utc),
  datetime.time(hour=21, minute=30, tzinfo=utc),
  datetime.time(hour=22, minute=0, tzinfo=utc),
  datetime.time(hour=22, minute=30, tzinfo=utc),
  datetime.time(hour=23, minute=0, tzinfo=utc),
  datetime.time(hour=23, minute=30, tzinfo=utc),
]


@tasks.loop(time=times)
async def master_loop(client : discord.Client) :
    """The main looping function that runs every half hour."""
    print('loop began...')
    # get channels
    log_channel = client.get_channel(hm.LOG_ID)
    casino_channel = client.get_channel(hm.CASINO_ID)
    private_log_channel = client.get_channel(hm.PRIVATE_LOG_ID)
    game_additions_channel = client.get_channel(hm.GAME_ADDITIONS_ID)

    # ---- game ----
    SKIP_GAME_SCRAPE = False
    if not SKIP_GAME_SCRAPE :
        database_name = await Mongo_Reader.get_mongo_games()
        try :
            new_games = await CEAPIReader.get_api_games_full()
            # get the embeds
            embeds = Discord_Helper.game_additions_updates(old_games=database_name, new_games=new_games)

            # send embeds
            for embed in embeds :
                await game_additions_channel.send(embed=embed.embed, file=embed.file)

            # dump the games
            await Mongo_Reader.dump_games(new_games)
        
        except FailedScrapeException as e :
            await private_log_channel.send(e.get_message())
    
    

    # ---- users ----
    SKIP_USER_SCRAPE = True
    if not SKIP_USER_SCRAPE :
        if SKIP_GAME_SCRAPE : database_name = await Mongo_Reader.get_mongo_games()
        database_user = await Mongo_Reader.get_mongo_users()
        try :
            new_users = await CEAPIReader.get_api_users_all()

            # get the updates
            user_returns : tuple[list[UpdateMessage], list[CEUser]] = await thread_user_update(database_user, new_users, database_name)

            # send update messages
            for update_message in user_returns[0] :
                match(update_message.location) :
                    case "log" : await log_channel.send(update_message.message, allowed_mentions=discord.AllowedMentions.none())
                    case "gameadditions" : await game_additions_channel.send(update_message.message)
                    case "casino" : await casino_channel.send(update_message.message)
                    case "privatelog" : await private_log_channel.send(update_message.message)
                    
            # and dump updated users
            await Mongo_Reader.dump_users(user_returns[1])
        except FailedScrapeException as e :
            await private_log_channel.send(e.get_message())
    
    print('loop complete.')




@to_thread
def thread_game_update(old_data : list[CEGame], new_data : list[CEAPIGame]) :

    pass

@to_thread
def thread_user_update(old_data : list[CEUser], new_data : list[CEUser], database_name : list[CEGame]) -> tuple[list[UpdateMessage], list[CEUser]] :
    """Update the users."""
    messages : list[UpdateMessage] = []
    users : list[CEUser] = []
    for old_user in old_data :
        new_user = hm.get_item_from_list(old_user.ce_id, new_data)

        # if the old user isn't on the site, alert someone!
        if new_user == None : 
            messages.append(UpdateMessage(
                location="privatelog",
                message=f"user not found in scrape: {old_user}"
            ))
            continue
        
        user_updates = user_update(
            user=old_user,
            site_data=new_user,
            database_name=database_name,
            database_user=old_data
        )

        messages += user_updates[0]
        users.append(user_updates[1])
        partners = user_updates[2]

        # if some partners were sent back up, replace them!
        for partner in partners :
            index = hm.get_index_from_list(partner.ce_id, old_data)
            old_data[index] = partner

    return (messages, users)
    """
    how the fuck does this work?
    andy and brooks enter winner takes all
    andy wins
    andy's code runs, a message is sent that his thing is completed, moves from current to completed
    keep iterating...
    get to brooks
    sees he loses
    """