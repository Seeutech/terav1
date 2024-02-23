import os
import pyshorteners
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as ikb, InlineKeyboardMarkup as ikm
from pyrogram.enums import ChatMemberStatus
from terabox import getUrl
import pymongo
import asyncio
import youtube_dl
import tempfile


bot = Client(
    "TestBOt",
    bot_token="6790916216:AAE19YJqas4CjTOhr74lYflmVvjPv_Fr7QM",
    api_id=1712043,
    api_hash="965c994b615e2644670ea106fd31daaf"
    
)

admin_ids = [6121699672, 1111214141]  # Add all admin IDs here
shortener = pyshorteners.Shortener()

# Create a temporary directory
temp_dir = tempfile.mkdtemp()

# Specify a temporary file path within the temporary directory
temp_file_path = os.path.join(temp_dir, 'video.mp4')

# Initialize MongoDB client and database
ConnectionString = "mongodb+srv://whatsappbot:WbFWxnSrzNvXMzAA@whatsappbot.n058qik.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(ConnectionString)
db = client["terabox"]
user_links_collection = db["user_links"]
plans_collection = db["plans"]

# Initialize plans
try:
    plans_collection.insert_many([
        {"_id": 1, "name": "7 days", "price": 10},
        {"_id": 2, "name": "15 days", "price": 10},
        {"_id": 3, "name": "24 days", "price": 30},
        {"_id": 4, "name": "30 days", "price": 40}
    ])

except:
    pass

def check_limit(user_id):
    user = user_links_collection.find_one({"user_id": user_id})
    if user:
        links_count = user.get("links_count", 0)
        last_conversion = user.get("last_conversion")
        if links_count >= 3 and datetime.now() - last_conversion < timedelta(days=1):
            return False
    return True

def update_limit(user_id):
    user = user_links_collection.find_one({"user_id": user_id})
    if user:
        links_count = user.get("links_count", 0) + 1
        user_links_collection.update_one({"user_id": user_id}, {
                                         "$set": {"links_count": links_count, "last_conversion": datetime.now()}})
    else:
        user_links_collection.insert_one(
            {"user_id": user_id, "links_count": 1, "last_conversion": datetime.now()})

async def subscribe_premium(bot, user_id, plan_id):
    # Retrieve plan details
    plan = plans_collection.find_one({"_id": plan_id})
    if not plan:
        return False
    user_links_collection.update_one({"user_id": user_id}, {"$set": {
                                     "plan_id": plan_id, "plan_name": plan["name"], "plan_price": plan["price"]}})
    try:
        await bot.send_message(user_id, f"Congratulations! You have been subscribed to the {plan['name']} Validity.\n **Unlimited Premium plan.**")
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")

    return True




@bot.on_message(filters.command('adduser') & filters.private)
async def add_user_to_premium(bot, message):
    # Check if user is admin
    if message.from_user.id not in admin_ids:
        await bot.send_message(message.chat.id, "Only admin can add users to premium plans.")
        return

    # Parse command arguments
    try:
        _, user_identifier, plan_id_str = message.text.split(maxsplit=2)
        plan_id = int(plan_id_str)
    except ValueError:
        await bot.send_message(message.chat.id, "Invalid command format. Please use: /adduser @username_or_userID plan_id")
        return

    # Check if the plan exists
    plan = plans_collection.find_one({"_id": plan_id})
    if not plan:
        await bot.send_message(message.chat.id, "Invalid plan ID.")
        return

    # Get user ID from username or use user identifier directly
    try:
        user = await bot.get_users(user_identifier)
        user_id = user.id
    except ValueError:
        user_id = int(user_identifier)

    # Subscribe user to premium plan and notify the user
    success = await subscribe_premium(bot, user_id, plan_id)
    if success:
        await bot.send_message(message.chat.id, f"User {user_identifier} has been subscribed to the {plan['name']} premium plan.")
    else:
        await bot.send_message(message.chat.id, "Failed to subscribe user to the premium plan.")

@bot.on_message(filters.command('stats') & filters.private)
async def get_users_info(bot, message):
    # Check if user is admin
    if message.from_user.id not in admin_ids:
        await message.reply_text("You are not authorized to use this command.")
        return

    # Check if the command is for premium users list
    if len(message.command) > 1 and message.command[1].lower() == 'premium':
        # Get all premium users
        premium_users = user_links_collection.find({"plan_id": {"$ne": 0}})
        
        # Prepare response message
        response_msg = "Premium Users List:\n"
        for user in premium_users:
            response_msg += (
                f"User ID: {user['user_id']}, "
                f"Plan: {user.get('plan_name', 'Unknown')}, "
                f"Price: {user.get('plan_price', 0)}\n"
            )
    else:
        # Get the count of premium users
        premium_users_count = user_links_collection.count_documents({"plan_id": {"$ne": 0}})

        # Get the count of free users
        free_users_count = user_links_collection.count_documents({"plan_id": 0})

        # Get the total number of users
        total_users_count = user_links_collection.count_documents({})

        # Prepare response message
        response_msg = (
            "<b>Statistics 📊</b>\n\n"
            f"⚡️ |<b> Premium Users: </b>{premium_users_count}\n"
            f"🆓 |<b> Free Users: </b>{free_users_count}\n"
            f"👥 |<b> Total Users: </b>{total_users_count}\n\n"
            "\t**Use** '/stats premium' <b>to view Premium users List</b>\n\n"
        )

    await message.reply_text(response_msg)

@bot.on_message(filters.command('start') & filters.private)
async def start(bot, message):
    welcomemsg = (f"Hello {message.from_user.first_name} ,"
                           
                    "\nI can Download Files from Terabox." 
                    "\nMade with ❤️ by"
                    "\n@mrxed_bot & @mrwhite7206_bot")
    inline_keyboard = ikm(
    [
        [
            ikb("Report Bugs", url="https://t.me/telebotsupdategroup"),
            ikb("Support Channel", url="https://t.me/TeleBotsUpdate")
        ]
    ]
)

    await message.reply_text(welcomemsg, reply_markup=inline_keyboard)


@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(bot, message):
    # Check if user is admin
    if message.from_user.id not in admin_ids:
        await message.reply_text("You are not authorized to use this command.")
        return

    # Extract message from command
    try:
        _, msg = message.text.split(maxsplit=1)
    except ValueError:
        await message.reply_text("Invalid command format. Please use: /broadcast your_message")
        return

    # Get all users using the bot
    users = user_links_collection.find({})

    # Send the message to all users
    for user in users:
        try:
            await bot.send_message(user['user_id'], msg)
        except Exception as e:
            print(f"Failed to send broadcast message to user {user['user_id']}: {e}")

    await message.reply_text("Broadcast sent successfully.")

@bot.on_message(filters.command('admin') & filters.private)
async def admincommand(bot,message):
    if message.from_user.id not in admin_ids:
        await bot.send_message(message.chat.id, "Only admin can Use this command. 🥲")
        return
    
    await bot.send_message(message.chat.id,
                           "<b>Admin Commands </b>😁\n\n"
                           "/adduser <b>: to add user to premium plan. </b>\n"
                           "/stats <b>: to check how many users are using the bot.</b>\n" 
                           "/broadcast <b>: to broadcast a message to all the users. </b> \n"
                           )



@bot.on_message(filters.command("info") & filters.private)
async def user_info(bot, message):
    user_id = message.from_user.id
    user = user_links_collection.find_one({"user_id": user_id})
    
    if user:
        plan_name = user.get("plan_name", "Free")
        plan_price = user.get("plan_price", 0)
        
        response_msg = f"User ID: {user_id}\n"
        response_msg += f"Plan: {plan_name} (Price: {plan_price})\n"
    else:
        response_msg = "No plan subscribed"
    
    await message.reply_text(response_msg)


@bot.on_message(filters.command('plans') & filters.private)
async def plansList(bot, message):
    msg_text = ("INR PRICING \n\n"
                "**10₹ - 7 days**\n"
                "**20₹ - 15 days** \n"
                "**30₹ - 24 days** \n"
                "**40₹ - 30 days**\n\n"
                "CRYPTO PRICING \n\n"
                "**$1 - 30 days** \n\n"
                "**Contact** @mrxed_bot **to add paid plan 💥**")

    inline_keyboard = ikm(
        [
            [
                ikb("Buy Now 💰", url="https://t.me/mrxed_bot")
            ]
        ]
    )
    await message.reply_text(msg_text, reply_markup=inline_keyboard)

@bot.on_message(filters.command('support') & filters.private)
async def support(bot, message):
    ContactUs = "**Contact US** : @mrxed_bot & @mrwhite7206_bot"
    await bot.send_message(message.chat.id,ContactUs)

# Function to download video using youtube-dl
async def download_video(url, temp_file_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': temp_file_path
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
    return filename

@bot.on_message(filters.text & filters.private)
async def teraBox(bot, message):
    user_id = message.from_user.id
    user = user_links_collection.find_one({"user_id": user_id})
    if not user:
        user_links_collection.insert_one(
            {"user_id": user_id, "links_count": 0, "last_conversion": datetime.now(), "plan_id": 0})
        user = user_links_collection.find_one({"user_id": user_id})

    plan_id = user.get("plan_id", 0)
    if plan_id == 0:
        if not check_limit(user_id):
            await bot.send_message(message.chat.id, "You have reached your daily conversion limit. Please try again later or subscribe to a premium plan.")
            return

    msg = message.text

    ProcessingMsg = await bot.send_message(message.chat.id, "Processing your link...")
try:
    LinkConvert = getUrl(msg)
    ShortUrl = shortener.tinyurl.short(LinkConvert)
    print(ShortUrl)
    # Specify the path where you want to save the downloaded video
    # For example, you can use a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, 'video.mp4')
    VideoPath = await download_video(ShortUrl, temp_file_path)  # Download the video using youtube-dl
except Exception as e:
    await ProcessingMsg.delete()
    ErrorMsg = await bot.send_message(message.chat.id, f"<code>Error: {e}</code>")
    await asyncio.sleep(3)
    await ErrorMsg.delete()
else:
    await ProcessingMsg.delete()
    SendVideoMsg = await bot.send_message(message.chat.id, "<code>Sending Video, Please Wait...</code>")
    try:
        await bot.send_video(message.chat.id, VideoPath)
        await bot.send_message(message.chat.id, f"Here's the link: {ShortUrl}\n\n<code>If the video doesn't appear, you can download it through the link.</code>")
    except Exception as e:
        await bot.send_message(message.chat.id, f"<code>Error: {e}</code>")
    finally:
        await SendVideoMsg.delete()
        
    update_limit(user_id)

    
print("Started..")
bot.run()
