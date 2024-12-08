import asyncio
import logging
import re
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from config import TOKEN
from db import execute_query, create_tables
from reminders import start_scheduler

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для добавления привычки
class AddHabitStates(StatesGroup):
    waiting_for_habit_details = State()

class TaskState(StatesGroup):
    waiting_for_task_details = State()

@dp.message(CommandStart())
async def start(message: Message):
    # Передаем SQL-запрос и параметры напрямую
    execute_query(
        "INSERT INTO users (tg_id, username) VALUES (%s, %s) ON CONFLICT (tg_id) DO NOTHING;", 
        (message.from_user.id, message.from_user.username)
    )
    await message.answer("Привет! Я помогу тебе управлять задачами и отслеживать привычки.")

@dp.message(Command("add_tasking"))
async def start_task_creation(message: Message, state: FSMContext):
    """
    Начинает процесс добавления задачи. Просит пользователя ввести данные.
    """
    await message.answer(
        "✏️ Пожалуйста, введите задачу в формате: [название] [YYYY-MM-DD]\n"
        "Например: Закончить проект 2024-12-15"
    )
    # Устанавливаем состояние ожидания данных
    await state.set_state(TaskState.waiting_for_task_details)

@dp.message(TaskState.waiting_for_task_details)
async def process_task_details(message: Message, state: FSMContext):
    """
    Обрабатывает введенные пользователем данные для задачи.
    """
    try:
        match = re.match(r"(.+)\s(\d{4}-\d{2}-\d{2})$", message.text.strip())
        if not match:
            raise ValueError("Неверный формат ввода.")
        
        title = match.group(1).strip()  # Название задачи
        deadline = match.group(2).strip()  # Дата
        # Записываем задачу в базу
        execute_query(
            "INSERT INTO tasks (user_id, title, deadline) VALUES (%s, %s, %s);",
            (message.from_user.id, title, deadline)
        )
        await message.answer(f"✅ Задача '{title}' с дедлайном {deadline} успешно добавлена.")
    except ValueError:
        await message.answer(
            "⚠️ Неверный формат. Попробуй ещё раз.\n"
            "Используй формат: [название] [YYYY-MM-DD]"
        )
        return
    except Exception as e:
        await message.answer(f"⚠️ Произошла ошибка: {e}")
    
    # Сбрасываем состояние
    await state.clear()

@dp.message(Command("view_tasks"))
async def list_tasks(message: Message):
    try:
        tasks = execute_query(
            "SELECT title, deadline FROM tasks WHERE user_id = %s AND status = 'pending';",
            (message.from_user.id,)
        )
        
        if tasks:
            # Формируем список задач
            response = "\n".join([f"📌 {task[0]} — {task[1]}" for task in tasks])
            await message.answer(f"Ваши задачи:\n{response}")
        else:
            await message.answer("У вас нет задач.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при получении списка задач: {e}")


@dp.message(Command("add_habit"))
async def start_add_habit(message: Message, state: FSMContext):
    """
    Начало процесса добавления привычки. Пользователь получает инструкцию.
    """
    await message.answer("Введите название привычки и её частоту через пробел.\nПример: Занятие спортом - ежедневно")
    await state.set_state(AddHabitStates.waiting_for_habit_details)

@dp.message(AddHabitStates.waiting_for_habit_details)
async def process_add_habit(message: Message, state: FSMContext):
    """
    Обрабатывает введенные пользователем данные и сохраняет привычку в базу данных.
    """
    try:
        # Регулярное выражение для разделения названия и частоты привычки
        match = re.match(r"^(.+)\s*-\s*(.+)$", message.text)
        if not match:
            raise ValueError("Invalid format")
        
        title, frequency = match.groups()

        # Проверка на наличие частоты (например, это может быть "ежедневно", "еженедельно" и т.д.)
        if not frequency:
            await message.answer("⚠️ Частота не может быть пустой.")
            return

        # Сохраняем привычку в базе данных
        execute_query(
            "INSERT INTO habits (user_id, title, frequency) VALUES (%s, %s, %s);",
            (message.from_user.id, title.strip(), frequency.strip())
        )
        await message.answer(f"✅ Привычка '{title.strip()}' добавлена с частотой: {frequency.strip()}.")
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите данные в формате: название - частота.\nПример: Занятие спортом - ежедневно")
    except Exception as e:
        await message.answer("⚠️ Произошла ошибка при добавлении привычки. Попробуйте ещё раз.")
        logging.error(f"Ошибка добавления привычки: {e}")
    finally:
        # Завершаем состояние
        await state.clear()

@dp.message(Command("view_habits"))
async def list_habits(message: Message):
    habits = execute_query("SELECT title, streak FROM habits WHERE user_id = %s;", 
                           (message.from_user.id,))
    if habits:
        response = "\n".join([f"{habit[0]} (стрик: {habit[1]} дней)" for habit in habits])
        await message.answer(f"Ваши привычки:\n{response}")
    else:
        await message.answer("У вас нет привычек.")


async def main():
    start_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        create_tables()
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')