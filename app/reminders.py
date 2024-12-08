from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import execute_query

scheduler = AsyncIOScheduler()

async def send_reminders(bot):
    tasks = execute_query("SELECT * FROM tasks WHERE status = 'pending' AND deadline = CURRENT_DATE;")
    for task in tasks:
        await bot.send_message(chat_id=task["user_id"], text=f"Напоминание: Сегодня дедлайн задачи: {task['title']}")

def start_scheduler(bot):
    scheduler.add_job(send_reminders, "cron", hour=9, args=[bot])  # Уведомления в 9 утра
    scheduler.start()
