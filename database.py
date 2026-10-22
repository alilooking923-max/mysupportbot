import os
import aiosqlite
from datetime import datetime
from typing import Optional

DB_DIR = "/data" if os.path.exists("/data") else "."
DB_FILE = os.path.join(DB_DIR, "support.db")


async def init_db():
    """Инициализация таблиц базы данных."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                admin_message_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                user_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'open', -- 'open' или 'closed'
                rating INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP DEFAULT NULL
            )
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: Optional[str], full_name: str) -> dict:
    """Получить или сохранить пользователя в БД."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id, username, full_name, is_banned FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"user_id": row[0], "username": row[1], "full_name": row[2], "is_banned": bool(row[3])}
        
        await db.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()
        return {"user_id": user_id, "username": username, "full_name": full_name, "is_banned": False}

async def is_user_banned(user_id: int) -> bool:
    """Проверка, заблокирован ли пользователь."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def set_ban_status(user_id: int, is_banned: bool):
    """Блокировка или разблокировка пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (1 if is_banned else 0, user_id)
        )
        await db.commit()

async def save_message_link(admin_message_id: int, user_id: int, user_message_id: int):
    """Связывание ID сообщения в чате операторов с ID пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO messages (admin_message_id, user_id, user_message_id) VALUES (?, ?, ?)",
            (admin_message_id, user_id, user_message_id)
        )
        await db.commit()

async def get_user_by_admin_message(admin_message_id: int) -> Optional[int]:
    """Получение ID пользователя по сообщению в чате поддержки."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM messages WHERE admin_message_id = ?", (admin_message_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_or_create_ticket(user_id: int) -> int:
    """Получить ID текущего открытого тикета или создать новый."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
        
        cursor = await db.execute("INSERT INTO tickets (user_id, status) VALUES (?, 'open')", (user_id,))
        await db.commit()
        return cursor.lastrowid

async def close_ticket(user_id: int) -> Optional[int]:
    """Закрыть открытый тикет пользователя и вернуть его ID."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            ticket_id = row[0]
            
        await db.execute("UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
        await db.commit()
        return ticket_id

async def set_ticket_rating(ticket_id: int, rating: int):
    """Установить оценку обслуживания тикета."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE tickets SET rating = ? WHERE id = ?", (rating, ticket_id))
        await db.commit()

async def get_statistics() -> dict:
    """Получение общей статистики для администратора."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM tickets") as c:
            total_tickets = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'") as c:
            open_tickets = (await c.fetchone())[0]
            
        async with db.execute("SELECT AVG(rating) FROM tickets WHERE rating IS NOT NULL") as c:
            row = await c.fetchone()
            avg_rating = round(row[0], 2) if row and row[0] else 0.0

        return {
            "total_users": total_users,
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "avg_rating": avg_rating
        }
