from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from database.users import get_all_user_ids_by_role


class SchedulerSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.scheduler = AsyncIOScheduler()
        return cls._instance


def get_scheduler() -> AsyncIOScheduler:
    scheduler_object = SchedulerSingleton()
    return scheduler_object.scheduler


async def send_event_reminder(bot: Bot, theme: str, place: str, event_datetime: str):
    """
    Send event reminder to all users 24 hours before the event.
    """
    # Parse the event datetime to extract just the time part for the message
    try:
        event_dt = datetime.strptime(event_datetime, '%Y-%m-%d %H:%M:%S')
        event_time = event_dt.strftime('%H:%M')  # Extract just HH:MM
        event_date = event_dt.strftime('%d.%m.%Y')  # Format date nicely
    except ValueError:
        # Fallback if parsing fails
        event_time = "указанное время"
        event_date = "указанную дату"

    # Get all users (not just 'user' role, but all active users)
    user_ids = get_all_user_ids_by_role('user')

    if not user_ids:
        print("Warning: No users found to send event reminder to")
        return

    # Create a better formatted message
    msg = f"📅 <b>Напоминание о событии!</b>\n\n"
    msg += f"📆 <b>Дата:</b> {event_date}\n"
    msg += f"⏰ <b>Время:</b> {event_time}\n"
    msg += f"🎯 <b>Событие:</b> {theme}\n"
    msg += f"📍 <b>Место:</b> {place}\n\n"
    msg += f"💪 Не пропустите!"

    sent_count = 0
    failed_count = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, msg, parse_mode="HTML")
            sent_count += 1
        except Exception as e:
            print(f"Failed to send event reminder to user {uid}: {e}")
            failed_count += 1

    print(f"Event reminder sent: {sent_count} successful, {failed_count} failed")
    print(f"Event: {theme} at {place} on {event_date} {event_time}")


async def schedule_reminder(bot: Bot, event_datetime: str, event_id: int, theme: str, place: str):
    """
    Schedule an event reminder 24 hours before the event.
    If the event is less than 24 hours away, send immediately.
    """
    try:
        event_dt = datetime.strptime(event_datetime, '%Y-%m-%d %H:%M:%S')
        reminder_time = event_dt - timedelta(days=1)
        now = datetime.now()

        if reminder_time <= now:
            # Event is less than 24 hours away, send reminder immediately
            print(f"Event '{theme}' is scheduled for {event_datetime}, sending immediate reminder")
            await send_event_reminder(bot, theme, place, event_datetime)
        else:
            # Schedule reminder for 24 hours before the event
            scheduler = get_scheduler()
            job_id = f"reminder_{event_id}"

            # Remove any existing job with the same ID (in case of event update)
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)

            scheduler.add_job(
                send_event_reminder,
                DateTrigger(run_date=reminder_time),
                args=[bot, theme, place, event_datetime],
                id=job_id,
                name=f"Reminder for event: {theme}"
            )

            reminder_str = reminder_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Scheduled reminder for event '{theme}' at {reminder_str}")

    except ValueError as e:
        print(f"Error parsing event datetime '{event_datetime}': {e}")
    except Exception as e:
        print(f"Error scheduling reminder for event '{theme}': {e}")
