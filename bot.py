import pexpect
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
import os




API_TOKEN = os.environ.get("BOT_TOKEN")
authorized_users = int(os.environ.get("ADMIN_USER_ID"))

# API_TOKEN = '7061991377:AAFerA2_N6htPslQAbifVRiclEENE_tTIJY'
# authorized_users = 5987705584

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
subprocess_result_template = "Command executed successfully:\n{}\n\nCommand output:\n{}"
subprocess_error_template = "Command execution failed:\n{}\n\nCommand error:\n{}"
user_states = {}


@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):
    user_id = message.from_user.id
    
    if user_id == authorized_users:
        keyboard = InlineKeyboardMarkup(row_width=2)
        install_config = InlineKeyboardButton(text='Install Config', callback_data='install_config')
        delete_config = InlineKeyboardButton(text='Delete Config', callback_data='delete_config')
        creat_user = InlineKeyboardButton(text='Creat User', callback_data='creat_user')
        delete_user = InlineKeyboardButton(text='Delete User', callback_data='delete_user')
        change_password = InlineKeyboardButton(text='Change Password', callback_data='change_password')
        lock_user = InlineKeyboardButton(text='Lock User', callback_data='lock_user')
        unlock_user = InlineKeyboardButton(text='UnLock User', callback_data='unlock_user')
        keyboard.insert(install_config)
        keyboard.insert(delete_config)
        keyboard.insert(creat_user)
        keyboard.insert(delete_user)
        keyboard.insert(change_password)
        keyboard.insert(lock_user)
        keyboard.insert(unlock_user)
        
        await message.reply("Welcome to the bot! Click the  button to run command.", reply_markup=keyboard)
    else:
        await message.reply("🚫 Sorry, you don't have permission to access this bot. 🚫")


@dp.callback_query_handler(text='install_config')
async def install_config(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    install_commands = [
        "ip=$(hostname -I|cut -f1 -d ' ')",
        "echo Your Server IP address is:$ip",
        "echo -e \"\\e[32mInstalling gnutls-bin\\e[39m\"",
        "apt install gnutls-bin",
        "mkdir certificates",
        "cd certificates",
        # ... (other commands)
        # ...
        "echo -e \"\\e[32mStarting ocserv service\\e[39m\"",
        "service ocserv start",
        "echo OpenConnect Server Configured Succesfully"
    ]
    
    output = ""
    for command in install_commands:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            output += f"Command executed successfully:\n{command}\n\nCommand output:\n{result.stdout}\n\n"
        else:
            output += f"Command execution failed:\n{command}\n\nCommand error:\n{result.stderr}\n\n"
    
    await bot.send_message(callback_query.message.chat.id, output)


@dp.callback_query_handler(text='delete_config')
async def delete_config(callback_query: types.CallbackQuery):
    await callback_query.answer()

    delete_command = "sudo apt-get purge ocserv"
    
    result = subprocess.run(delete_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        await bot.send_message(callback_query.message.chat.id, f"Command executed successfully:\n{delete_command}\n\nCommand output:\n{result.stdout}")
    else:
        await bot.send_message(callback_query.message.chat.id, f"Command execution failed:\n{delete_command}\n\nCommand error:\n{result.stderr}")




@dp.callback_query_handler(text='creat_user')
async def create_user(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.message.chat.id, "Enter a username:")

    # Set the user state to 'waiting_for_username'
    user_states[callback_query.from_user.id] = 'waiting_for_username'

# Define the message handler to handle user responses
@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'waiting_for_username')
async def handle_username(message: types.Message):
    username = message.text.strip()
    await bot.send_message(message.chat.id, f"Enter a password for user '{username}':")
    
    # Update the user state to 'waiting_for_password'
    user_states[message.from_user.id] = {'username': username}
    user_states[message.from_user.id]['state'] = 'waiting_for_password'

# Define another message handler to handle password input
@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_password')
async def handle_password(message: types.Message):
    user_info = user_states[message.from_user.id]
    password = message.text.strip()
    
    added = add_user_with_password(user_info['username'], password)
    
    if added:
        await message.reply(f"User '{user_info['username']}' added successfully.")
    else:
        await message.reply(f"Failed to add user '{user_info['username']}'.")
    
    # Clear the user state after handling the password
    user_states.pop(message.from_user.id)

def add_user_with_password(username, password):
    try:
        p = subprocess.Popen(['ocpasswd', '-c', '/etc/ocserv/ocpasswd', username], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.stdin.write(password + '\n')
        p.stdin.flush()
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Error:", e)
        return False


@dp.callback_query_handler(text='delete_user')
async def delete_user(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.message.chat.id, "Enter a username to delete:")

    # Set the user state to 'waiting_for_delete_username'
    user_states[callback_query.from_user.id] = {'state': 'waiting_for_delete_username'}



@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_delete_username')
async def handle_delete_username(message: types.Message):
    username = message.text.strip()
    
    deleted = delete_user(username)
    
    if deleted:
        await message.reply(f"User '{username}' deleted successfully.")
    else:
        await message.reply(f"Failed to delete user '{username}'.")
    
    # Clear the user state after handling the delete operation
    user_states[message.from_user.id] = {}

def delete_user(username):
    try:
        p = subprocess.Popen(['ocpasswd', '-c', '/etc/ocserv/ocpasswd', '-d', username], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Error:", e)
        return False

# Define the callback query handler for changing a user's password
@dp.callback_query_handler(text='change_password')
async def change_password(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.message.chat.id, "Enter your username:")

    # Set the user state to 'waiting_for_change_username'
    user_states[callback_query.from_user.id] = {'state': 'waiting_for_change_username'}

# Define the message handler to handle username input for changing password
@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_change_username')
async def handle_change_username(message: types.Message):
    username = message.text.strip()
    await bot.send_message(message.chat.id, f"Enter your new password for user '{username}':")
    
    # Update the user state to 'waiting_for_change_password'
    user_states[message.from_user.id]['state'] = 'waiting_for_change_password'
    user_states[message.from_user.id]['username'] = username

# Define another message handler to handle password input for changing password
@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_change_password')
async def handle_change_password(message: types.Message):
    user_info = user_states[message.from_user.id]
    new_password = message.text.strip()
    
    changed = change_user_password(user_info['username'], new_password)
    
    if changed:
        await message.reply(f"Password for user '{user_info['username']}' changed successfully.")
    else:
        await message.reply(f"Failed to change password for user '{user_info['username']}'.")
    
    # Clear the user state after handling the password change
    user_states[message.from_user.id] = {}

def change_user_password(username, new_password):
    try:
        p = subprocess.Popen(['ocpasswd', '-c', '/etc/ocserv/ocpasswd', username], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.stdin.write(new_password + '\n')
        p.stdin.flush()
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Error:", e)
        return False


# Define the callback query handler for locking a user's account
@dp.callback_query_handler(text='lock_user')
async def lock_user(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.message.chat.id, "Enter a username to lock:")

    # Set the user state to 'waiting_for_lock_username'
    user_states[callback_query.from_user.id] = {'state': 'waiting_for_lock_username'}

# Define the message handler to handle username input for locking
@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_lock_username')
async def handle_lock_username(message: types.Message):
    username = message.text.strip()
    
    locked = lock_user_account(username)
    
    if locked:
        await message.reply(f"User '{username}' locked successfully.")
    else:
        await message.reply(f"Failed to lock user '{username}'.")
    
    # Clear the user state after handling the lock operation
    user_states[message.from_user.id] = {}

def lock_user_account(username):
    try:
        p = subprocess.Popen(['ocpasswd', '-c', '/etc/ocserv/ocpasswd', '-l', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Error:", e)
        return False

# Define the callback query handler for unlocking a user's account
@dp.callback_query_handler(text='unlock_user')
async def unlock_user(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.message.chat.id, "Enter a username to unlock:")

    # Set the user state to 'waiting_for_unlock_username'
    user_states[callback_query.from_user.id] = {'state': 'waiting_for_unlock_username'}

# Define the message handler to handle username input for unlocking
@dp.message_handler(lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_unlock_username')
async def handle_unlock_username(message: types.Message):
    username = message.text.strip()
    
    unlocked = unlock_user_account(username)
    
    if unlocked:
        await message.reply(f"User '{username}' unlocked successfully.")
    else:
        await message.reply(f"Failed to unlock user '{username}'.")
    
    # Clear the user state after handling the unlock operation
    user_states[message.from_user.id] = {}

def unlock_user_account(username):
    try:
        p = subprocess.Popen(['ocpasswd', '-c', '/etc/ocserv/ocpasswd', '-u', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Error:", e)
        return False

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
