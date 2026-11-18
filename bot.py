import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- Configurations ---
API_TOKEN = "9246879108:AAEbhixiJzOt_V_EJTsn9yZw3WA6viQvvs0"
BOT_USERNAME = "videoPhotoHubBot"  # ඔයාගේ Bot Username එක
MONGO_URI = "mongodb+srv://chathumaldevinda14_db_user:aaaa1234@cluster0.87pcrsy.mongodb.net/?retryWrites=true&w=majority"
GROUP_ID = -5226449370  # ඔයාගේ Group එකේ ID එක

# Database Setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["TelegramBotProject"]
videos_collection = db["videos"]

# Bot Setup
bot = telebot.TeleBot(API_TOKEN)

# --- 1. Group එකට video එකක් දැමූ විට markdown නොමැතිව link එක සමඟ යැවීම ---
@bot.message_handler(content_types=['video', 'document'])
def save_video_from_group(message):
    if message.chat.id == GROUP_ID:
        media = message.video or message.document
        if media:
            file_id = media.file_id
            file_name = media.file_name or "Untitled Video"
            
            video_data = {
                "title": file_name,
                "file_id": file_id
            }
            
            if not videos_collection.find_one({"file_id": file_id}):
                inserted_result = videos_collection.insert_one(video_data)
                mongo_id = str(inserted_result.inserted_id)
                print(f"Video saved to DB: {file_name}")
                
                # t.me link එක නිර්මාණය කිරීම
                deep_link = f"https://t.me/{BOT_USERNAME}?start={mongo_id}"
                
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("📥 Open & Get Video", url=deep_link))
                
                # Markdown ඉවත් කර සාමාන්‍ය text ලෙස සැකසීම (මෙයින් errors සම්පූර්ණයෙන්ම වැළකේ)
                response_text = (
                    f"✅ Video saved to database successfully!\n"
                    f"🎬 Title: {file_name}\n\n"
                    f"🔗 Link:\n{deep_link}"
                )
                
                bot.reply_to(
                    message, 
                    response_text, 
                    reply_markup=keyboard
                )
            else:
                print("Video already exists in DB.")
                bot.reply_to(message, "⚠️ This video already exists in the database!")

# --- 2. User කෙනෙක් /start දැමූ විට (Deep Linking හරහා video එක ඉල්ලුවොත්) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    command_parts = message.text.split()
    
    if len(command_parts) > 1:
        mongo_id = command_parts[1]
        try:
            video_doc = videos_collection.find_one({"_id": ObjectId(mongo_id)})
            if video_doc:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=video_doc["file_id"],
                    caption=f"🎬 {video_doc['title']}\n\n✨ Enjoy your video!"
                )
            else:
                bot.reply_to(message, "❌ Sorry, this video is not found or has been deleted!")
        except Exception as e:
            bot.reply_to(message, f"❌ Invalid video link! Error: {str(e)}")
    else:
        bot.reply_to(
            message,
            "👋 Hi! මම Video Bot කෙනෙක්.\n"
            "මම ළඟ තියෙන movies ලිස්ට් එක බලන්න /movies කියලා එවන්න."
        )

# --- 3. /movies command එක මඟින් සියලුම movies ලිස්ට් එක පෙන්වීම ---
@bot.message_handler(commands=['movies'])
def list_movies(message):
    movies = list(videos_collection.find({}, {"title": 1}))
    
    if not movies:
        bot.reply_to(message, "❌ තවම database එකේ videos නැහැ. Group එකට videos upload කරන්න.")
        return
    
    for movie in movies:
        mongo_id = str(movie["_id"])
        deep_link = f"https://t.me/{BOT_USERNAME}?start={mongo_id}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📥 Open & Get Video", url=deep_link))
        
        response_text = (
            f"🎬 {movie['title']}\n\n"
            f"🔗 {deep_link}"
        )
        
        bot.send_message(message.chat.id, response_text, reply_markup=keyboard)

# Bot එක Run කිරීම
print("Bot is running smoothly...")
bot.infinity_polling()