import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

from constants import MESSAGE, DATE_TYPE, DATE, TIME, CUSTOM_DAYS, ONE_TIME, DAILY, DAY_NAMES, VALID_DAYS
from task_manager import tasks, save_tasks

# Configure logger
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    
    # Create keyboard with user-friendly button labels
    keyboard = [
        ['➕ Add Reminder'],
        ['📋 My Reminders'],
        ['🗑️ Delete Reminder']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"Welcome to your personal Reminder Bot! 🎯\n"
        f"I can help you remember your tasks and send you daily reminders.\n"
        f"Use the buttons below or these commands:\n"
        f"• Add a new task: /add\n"
        f"• See all your tasks: /list\n"
        f"• Remove a task: /delete\n"
        f"Let's get started!"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add task conversation."""
    # Add a cancel button
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Let's add a new reminder! First, what would you like me to remind you about?",
        reply_markup=reply_markup
    )
    return MESSAGE

async def task_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the task message and ask for date type."""
    # Check if this is a cancel button click
    if update.callback_query and update.callback_query.data == "cancel":
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Reminder creation cancelled.")
        return ConversationHandler.END
    
    context.user_data['message'] = update.message.text
    
    # Create inline keyboard with date type options with improved UI
    keyboard = [
        [
            InlineKeyboardButton("📅 One-time reminder", callback_data='one_time'),
            InlineKeyboardButton("🔄 Recurring reminder", callback_data='daily')
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]  # Cancel button
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Great! Now, do you want this to be a one-time reminder or a recurring one?",
        reply_markup=reply_markup
    )
    return DATE_TYPE

async def date_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the date type and ask for specific details."""
    query = update.callback_query
    await query.answer()
    
    # Check if user clicked cancel
    if query.data == "cancel":
        await query.edit_message_text("Reminder creation cancelled.")
        return ConversationHandler.END
    
    task_type = query.data
    context.user_data['type'] = task_type
    
    if task_type == ONE_TIME:
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 Please enter the due date in YYYY-MM-DD format (e.g., 2025-03-15).",
            reply_markup=reply_markup
        )
        return DATE
    else:  # DAILY
        # Create inline keyboard with daily options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Every day", callback_data='everyday'),
                InlineKeyboardButton("📆 Select days", callback_data='custom')
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]  # Cancel button
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "How often should I remind you?",
            reply_markup=reply_markup
        )
        return DATE

async def date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process date input or daily frequency selection."""
    # Handle callback query (for daily frequency)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Check if user clicked cancel
        if query.data == "cancel":
            await query.edit_message_text("Reminder creation cancelled.")
            return ConversationHandler.END
        
        frequency = query.data
        context.user_data['frequency'] = frequency
        
        if frequency == 'custom':
            # Add cancel button
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please enter the first two letters of each day you want reminders, "
                "separated by commas (e.g., Mo,Tu,Fr for Monday, Tuesday, Friday).\n\n"
                "Options: Mo, Tu, We, Th, Fr, Sa, Su",
                reply_markup=reply_markup
            )
            return CUSTOM_DAYS
        else:  # everyday
            # Add cancel button
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please enter the time for your reminder in HH:MM format (e.g., 11:50).",
                reply_markup=reply_markup
            )
            return TIME
    
    # Handle text input (for one_time date)
    else:
        date_str = update.message.text
        
        try:
            # Validate date format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Store the date
            context.user_data['date'] = date_str
            
            # Add cancel button
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Please enter the time for your reminder in HH:MM format (e.g., 11:50).",
                reply_markup=reply_markup
            )
            return TIME
        
        except ValueError:
            # Add cancel button
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-03-15).",
                reply_markup=reply_markup
            )
            return DATE

async def custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process custom days for recurring reminders."""
    # Check if it's a callback query for cancel
    if update.callback_query and update.callback_query.data == "cancel":
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Reminder creation cancelled.")
        return ConversationHandler.END
        
    days_input = update.message.text
    
    # Parse and validate the days
    days = [day.strip() for day in days_input.split(',')]
    
    # Check if all days are valid
    invalid_days = [day for day in days if day not in VALID_DAYS]
    if invalid_days:
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Invalid day(s): {', '.join(invalid_days)}. "
            f"Please use: Mo, Tu, We, Th, Fr, Sa, Su",
            reply_markup=reply_markup
        )
        return CUSTOM_DAYS
    
    # Store the days
    context.user_data['days'] = days
    
    # Add cancel button
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Please enter the time for your reminder in HH:MM format (e.g., 11:50).",
        reply_markup=reply_markup
    )
    return TIME

async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query and update.callback_query.data == "cancel":
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Reminder creation cancelled.")
        return ConversationHandler.END

    chat_id = str(update.effective_chat.id)
    time_str = update.message.text

    try:
        # Validate time format
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        
        # Create task data
        task_data = {
            'message': context.user_data['message'],
            'type': context.user_data['type'],
            'time': time_str
        }

        if task_data['type'] == ONE_TIME:
            task_data['date'] = context.user_data['date']
        else:  # DAILY
            task_data['frequency'] = context.user_data['frequency']
            if task_data['frequency'] == 'custom':
                task_data['days'] = context.user_data['days']

        if chat_id not in tasks:
            tasks[chat_id] = []

        tasks[chat_id].append(task_data)
        save_tasks(tasks)
        
        # Format task description for confirmation message
        if task_data['type'] == ONE_TIME:
            task_desc = f"on {task_data['date']}"
        else:  # DAILY
            if task_data['frequency'] == 'everyday':
                task_desc = "every day"
            else:  # custom
                days_full = [DAY_NAMES[day] for day in task_data['days']]
                task_desc = f"every {', '.join(days_full)}"

        await update.message.reply_text(
            f"✅ Task added successfully!\n\n"
            f"I'll remind you: \"{task_data['message']}\"\n"
            f"⏰ {task_desc} at {time_str}"
        )
        
        # Clear user data
        context.user_data.clear()

        return ConversationHandler.END

    except ValueError:
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Invalid time format. Please use HH:MM format (e.g., 11:50).",
            reply_markup=reply_markup
        )
        return TIME

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all tasks for the user."""
    user_id = str(update.effective_user.id)
    user_tasks = tasks.get(user_id, [])
    
    if not user_tasks:
        await update.message.reply_text("You don't have any reminders set up.")
        return
    
    # Format and display tasks
    response = "📝 Your reminders:\n\n"
    
    for i, task in enumerate(user_tasks):
        # Format task description
        if task['type'] == ONE_TIME:
            task_desc = f"on {task['date']}"
        else:  # DAILY
            if task['frequency'] == 'everyday':
                task_desc = "every day"
            else:  # custom
                days_full = [DAY_NAMES[day] for day in task['days']]
                task_desc = f"every {', '.join(days_full)}"
        
        response += f"{i+1}. \"{task['message']}\"\n"
        response += f"   ⏰ {task_desc} at {task['time']}\n\n"
    
    await update.message.reply_text(response)

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of tasks for deletion."""
    user_id = str(update.effective_user.id)
    user_tasks = tasks.get(user_id, [])
    
    if not user_tasks:
        await update.message.reply_text("You don't have any reminders to delete.")
        return
    
    # Create inline keyboard with improved task options
    keyboard = []
    for i, task in enumerate(user_tasks):
        # Format task description
        if task['type'] == ONE_TIME:
            task_desc = f"📅 {task['date']}"
        else:  # DAILY
            if task['frequency'] == 'everyday':
                task_desc = "🔄 Every day"
            else:  # custom
                days_full = [DAY_NAMES[day] for day in task['days']]
                days_text = ', '.join(days_full)
                task_desc = f"🔄 Every {days_text}"
        
        # Truncate message if too long for button
        message = task['message']
        if len(message) > 30:
            message = message[:27] + "..."
            
        button_text = f"🗑️ {i+1}. \"{message}\" • {task_desc} • ⏰ {task['time']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Select a reminder to delete:",
        reply_markup=reply_markup
    )

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process delete task selection with improved UX."""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    # Extract task index from callback data
    task_index = int(query.data.split('_')[1])
    
    # Delete the task
    if user_id in tasks and 0 <= task_index < len(tasks[user_id]):
        # Get task details for confirmation message
        task = tasks[user_id][task_index]
        task_message = task['message']
        
        # Delete the task
        del tasks[user_id][task_index]
        save_tasks(tasks)
        
        await query.edit_message_text(
            f"✅ Reminder deleted successfully!\n\n"
            f"Deleted: \"{task_message}\""
        )
    else:
        await query.edit_message_text(f"❌ Failed to delete reminder. Please try again.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation."""
    # Check if it's a callback query
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Reminder creation cancelled.")
    else:
        await update.message.reply_text("Operation cancelled.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Send message to the user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again or start over with /start."
        )