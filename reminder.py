import logging
from datetime import datetime
from telegram.ext import ContextTypes

from constants import ONE_TIME, DAILY, WEEKDAY_MAP
from task_manager import tasks, save_tasks

# Configure logger
logger = logging.getLogger(__name__)

async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for reminders to send."""
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    current_date = now.strftime('%Y-%m-%d')
    weekday = now.weekday()
    current_day = WEEKDAY_MAP[weekday]

    logger.info(f"Checking reminders at {current_time}")

    # Iterate through tasks for each chat (group or private)
    for chat_id, user_tasks in list(tasks.items()):
        for i, task in enumerate(list(user_tasks)):
            # Check if time matches
            if task['time'] == current_time:
                # Check if task should run today
                should_run = False
                
                if task['type'] == ONE_TIME:
                    if task['date'] == current_date:
                        should_run = True
                        # Remove one-time task after sending
                        user_tasks.pop(i)
                        save_tasks(tasks)
                
                elif task['type'] == DAILY:
                    if task['frequency'] == 'everyday':
                        should_run = True
                    elif task['frequency'] == 'custom':
                        if current_day in task['days']:
                            should_run = True
                
                # Send reminder if conditions match
                if should_run:
                    thread_id = task.get('message_thread_id')
                    await send_reminder(context, chat_id, task['message'], thread_id)

async def send_reminder(context, chat_id, message, thread_id=None):
    try:
        kwargs = {}
        if thread_id is not None:
            kwargs["message_thread_id"] = thread_id
        await context.bot.send_message(chat_id=chat_id, text=message, **kwargs)
        logger.info(f"Sent reminder to {chat_id} (thread: {thread_id}): {message}")
    except Exception as e:
        logger.error(f"Error sending reminder to {chat_id}: {e}")
