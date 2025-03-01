import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters
)

# Import our modules
from constants import MESSAGE, DATE_TYPE, DATE, TIME, CUSTOM_DAYS
from task_manager import tasks
from handlers import (
    start, add_task, task_message, date_type, date_input, 
    custom_days, time_input, list_tasks, delete_task, 
    handle_delete_callback, cancel, error_handler
)
from reminder import check_reminders

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Add conversation handler for adding tasks
    add_task_conv = ConversationHandler(
        entry_points=[
            CommandHandler('add', add_task),
            MessageHandler(filters.Regex(r'^➕ Add Reminder$'), add_task)
        ],
        states={
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_message)],
            DATE_TYPE: [CallbackQueryHandler(date_type, pattern=r'^(one_time|daily)$')],
            DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, date_input),
                CallbackQueryHandler(date_input, pattern=r'^(everyday|custom)$')
            ],
            CUSTOM_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_days)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )
    
    # Register handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(add_task_conv)
    application.add_handler(CommandHandler('list', list_tasks))
    application.add_handler(MessageHandler(filters.Regex(r'^📋 My Reminders$'), list_tasks))
    application.add_handler(CommandHandler('delete', delete_task))
    application.add_handler(MessageHandler(filters.Regex(r'^🗑️ Delete Reminder$'), delete_task))
    application.add_handler(CallbackQueryHandler(handle_delete_callback, pattern=r'^delete_'))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add job to check reminders every minute
    job_queue = application.job_queue
    job_queue.run_repeating(check_reminders, interval=60, first=1)
    
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()