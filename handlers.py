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
    
    # Create keyboard with command buttons
    keyboard = [
        ['/add'],
        ['/list'],
        ['/delete']
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
    await update.message.reply_text(
        "Let's add a new reminder! First, what would you like me to remind you about?"
    )
    return MESSAGE

async def task_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the task message and ask for date type."""
    context.user_data['message'] = update.message.text
    
    # Create inline keyboard with date type options
    keyboard = [
        [
            InlineKeyboardButton("Specific day", callback_data='one_time'),
            InlineKeyboardButton("Daily reminder", callback_data='daily')
        ]
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
    
    task_type = query.data
    context.user_data['type'] = task_type
    
    if task_type == ONE_TIME:
        await query.edit_message_text(
            "Please enter the due date in YYYY-MM-DD format (e.g., 2025-03-15)."
        )
        return DATE
    else:  # DAILY
        # Create inline keyboard with daily options
        keyboard = [
            [
                InlineKeyboardButton("Everyday", callback_data='everyday'),
                InlineKeyboardButton("Custom", callback_data='custom')
            ]
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
        
        frequency = query.data
        context.user_data['frequency'] = frequency
        
        if frequency == 'custom':
            await query.edit_message_text(
                "Please enter the first two letters of each day you want reminders, "
                "separated by commas (e.g., Mo,Tu,Fr for Monday, Tuesday, Friday).\n\n"
                "Options: Mo, Tu, We, Th, Fr, Sa, Su"
            )
            return CUSTOM_DAYS
        else:  # everyday
            await query.edit_message_text(
                "Please enter the time for your reminder in HH:MM format (e.g., 11:50)."
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
            
            await update.message.reply_text(
                "Please enter the time for your reminder in HH:MM format (e.g., 11:50)."
            )
            return TIME
        
        except ValueError:
            await update.message.reply_text(
                "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-03-15)."
            )
            return DATE

async def custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process custom days for recurring reminders."""
    days_input = update.message.text
    
    # Parse and validate the days
    days = [day.strip() for day in days_input.split(',')]
    
    # Check if all days are valid
    invalid_days = [day for day in days if day not in VALID_DAYS]
    if invalid_days:
        await update.message.reply_text(
            f"Invalid day(s): {', '.join(invalid_days)}. "
            f"Please use: Mo, Tu, We, Th, Fr, Sa, Su"
        )
        return CUSTOM_DAYS
    
    # Store the days
    context.user_data['days'] = days
    
    await update.message.reply_text(
        "Please enter the time for your reminder in HH:MM format (e.g., 11:50)."
    )
    return TIME

async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process time input and save the task."""
    user_id = str(update.effective_user.id)
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
        
        # Add the task
        if user_id not in tasks:
            tasks[user_id] = []
        
        tasks[user_id].append(task_data)
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
        await update.message.reply_text(
            "Invalid time format. Please use HH:MM format (e.g., 11:50)."
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
    
    # Create inline keyboard with task options
    keyboard = []
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
        
        button_text = f"{i+1}. \"{task['message']}\" ({task_desc})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Select a task to delete:",
        reply_markup=reply_markup
    )

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process delete task selection."""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    # Extract task index from callback data
    task_index = int(query.data.split('_')[1])
    
    # Delete the task
    if user_id in tasks and 0 <= task_index < len(tasks[user_id]):
        del tasks[user_id][task_index]
        save_tasks(tasks)
        await query.edit_message_text(f"✅ Task deleted successfully!")
    else:
        await query.edit_message_text(f"❌ Failed to delete task. Please try again.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation."""
    context.user_data.clear()
    
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Send message to the user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again or start over with /start."
        )