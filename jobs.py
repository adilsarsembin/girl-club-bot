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


async def send_event_reminder(bot: Bot, theme: str, place: str, event_time: str):
    user_ids = get_all_user_ids_by_role('user')
    msg = f"Reminder: Tomorrow at {event_time} - {theme} at {place} 📅"
    for uid in user_ids:
        try:
            await bot.send_message(uid, msg)
        except Exception as e:
            print(e)


async def schedule_reminder(bot: Bot, event_datetime: str, event_id: int, theme: str, place: str):
    scheduler = get_scheduler()
    event_dt = datetime.strptime(event_datetime, '%Y-%m-%d %H:%M:%S')
    reminder_time = event_dt - timedelta(days=1)
    if reminder_time <= datetime.now():
        await send_event_reminder(bot, theme, place, event_datetime)
    else:
        scheduler.add_job(
            send_event_reminder,
            DateTrigger(run_date=reminder_time),
            args=[bot, theme, place, event_datetime],
            id=f"reminder_{event_id}"
        )
