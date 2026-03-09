import aiosqlite
from typing import Optional
from .models import User, Profile, Interaction
import config


async def init_db(db_path: str = config.DB_PATH) -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                nickname TEXT NOT NULL,
                world_level INTEGER NOT NULL,
                main_dps TEXT NOT NULL,
                server TEXT NOT NULL,
                description TEXT,
                photo_file_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id),
                UNIQUE (from_user_id, to_user_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_from ON interactions(from_user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_to ON interactions(to_user_id)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_user_id INTEGER NOT NULL,
                reported_user_id INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (reporter_user_id) REFERENCES users (id),
                FOREIGN KEY (reported_user_id) REFERENCES users (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                banned_at TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_views (
                user_id INTEGER NOT NULL,
                view_date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, view_date),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_seen_at TEXT")
        except aiosqlite.OperationalError:
            pass
        await db.commit()


def get_db_path() -> str:
    return config.DB_PATH


async def get_or_create_user(telegram_id: int) -> User:
    """Get user by telegram_id or create new one."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, telegram_id, created_at FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return User(id=row["id"], telegram_id=row["telegram_id"], created_at=row["created_at"])

        from datetime import datetime
        created_at = datetime.utcnow().isoformat()
        cursor = await db.execute(
            "INSERT INTO users (telegram_id, created_at) VALUES (?, ?)",
            (telegram_id, created_at)
        )
        await db.commit()
        return User(id=cursor.lastrowid, telegram_id=telegram_id, created_at=created_at)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user by telegram_id."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, telegram_id, created_at FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return User(id=row["id"], telegram_id=row["telegram_id"], created_at=row["created_at"])
        return None


async def get_profile_by_user_id(user_id: int) -> Optional[Profile]:
    """Get profile by user_id."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, user_id, nickname, world_level, main_dps, server, description, photo_file_id
               FROM profiles WHERE user_id = ?""",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return Profile(
                id=row["id"],
                user_id=row["user_id"],
                nickname=row["nickname"],
                world_level=row["world_level"],
                main_dps=row["main_dps"],
                server=row["server"],
                description=row["description"],
                photo_file_id=row["photo_file_id"]
            )
        return None


async def get_telegram_id_by_user_id(user_id: int) -> Optional[int]:
    """Get telegram_id by internal user_id."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def create_profile(user_id: int, nickname: str, world_level: int, main_dps: str,
                        server: str, description: Optional[str] = None,
                        photo_file_id: Optional[str] = None) -> Profile:
    """Create new profile."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """INSERT INTO profiles (user_id, nickname, world_level, main_dps, server, description, photo_file_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, nickname, world_level, main_dps, server, description or "", photo_file_id or "")
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, user_id, nickname, world_level, main_dps, server, description, photo_file_id FROM profiles WHERE id = ?",
            (cursor.lastrowid,)
        )
        row = await cursor.fetchone()
        return Profile(
            id=row["id"],
            user_id=row["user_id"],
            nickname=row["nickname"],
            world_level=row["world_level"],
            main_dps=row["main_dps"],
            server=row["server"],
            description=row["description"] or None,
            photo_file_id=row["photo_file_id"] or None
        )


async def update_profile(user_id: int, **kwargs) -> None:
    """Update profile fields. Allowed: nickname, world_level, main_dps, server, description, photo_file_id."""
    allowed = {"nickname", "world_level", "main_dps", "server", "description", "photo_file_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            f"UPDATE profiles SET {set_clause} WHERE user_id = ?",
            values
        )
        await db.commit()


async def update_last_seen(telegram_id: int) -> None:
    """Обновить время последней активности."""
    from datetime import datetime
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_seen_at = ? WHERE telegram_id = ?",
            (datetime.utcnow().isoformat(), telegram_id)
        )
        await db.commit()


async def get_user_stats(user_id: int) -> dict:
    """Статистика пользователя."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT created_at, last_seen_at FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        reg_date = (row[0][:10] if row and row[0] else "—")
        last_seen = (str(row[1])[:10] if row and row[1] is not None else "—")

        cursor = await db.execute(
            "SELECT COUNT(*) FROM interactions WHERE from_user_id = ? AND action = 'like'",
            (user_id,)
        )
        likes_given = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM interactions WHERE to_user_id = ? AND action = 'like'",
            (user_id,)
        )
        likes_received = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM interactions WHERE from_user_id = ? AND action = 'dislike'",
            (user_id,)
        )
        dislikes_given = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM interactions WHERE to_user_id = ?",
            (user_id,)
        )
        profile_views = (await cursor.fetchone())[0]

        return {
            "reg_date": reg_date,
            "last_seen": last_seen,
            "likes_given": likes_given,
            "likes_received": likes_received,
            "dislikes_given": dislikes_given,
            "profile_views": profile_views,
        }


async def add_report(reporter_user_id: int, reported_user_id: int, reason: str = "") -> None:
    """Добавить жалобу."""
    from datetime import datetime
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO reports (reporter_user_id, reported_user_id, reason, created_at) VALUES (?, ?, ?, ?)",
            (reporter_user_id, reported_user_id, reason, datetime.utcnow().isoformat())
        )
        await db.commit()


async def get_daily_views_count(user_id: int) -> int:
    """Сколько раз пользователь просмотрел карточки сегодня."""
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT count FROM daily_views WHERE user_id = ? AND view_date = ?",
            (user_id, today)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def increment_daily_view(user_id: int) -> None:
    """Увеличить счётчик просмотров за сегодня."""
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """INSERT INTO daily_views (user_id, view_date, count) VALUES (?, ?, 1)
               ON CONFLICT(user_id, view_date) DO UPDATE SET count = count + 1""",
            (user_id, today)
        )
        await db.commit()


async def is_banned(user_id: int) -> bool:
    """Забанен ли пользователь."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None


async def ban_user_by_telegram_id(telegram_id: int, reason: str = "") -> bool:
    """Забанить по telegram_id. Возвращает True если забанили."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return False
    await ban_user(user.id, reason)
    return True


async def ban_user(user_id: int, reason: str = "") -> None:
    """Забанить пользователя."""
    from datetime import datetime
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO banned_users (user_id, banned_at, reason) VALUES (?, ?, ?)",
            (user_id, datetime.utcnow().isoformat(), reason)
        )
        await db.commit()


async def get_next_candidate(from_user_id: int, server_filter: Optional[str] = None) -> Optional[Profile]:
    """Get next candidate: not self, not interacted, optional server filter, prioritize same server."""
    from datetime import datetime
    my_profile = await get_profile_by_user_id(from_user_id)
    my_server = my_profile.server if my_profile else None

    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        base_sql = """
            SELECT p.id, p.user_id, p.nickname, p.world_level, p.main_dps, p.server, p.description, p.photo_file_id
            FROM profiles p
            WHERE p.user_id != ?
              AND p.user_id NOT IN (SELECT to_user_id FROM interactions WHERE from_user_id = ?)
              AND p.user_id NOT IN (SELECT user_id FROM banned_users)
        """
        params = [from_user_id, from_user_id]

        if server_filter:
            base_sql += " AND p.server LIKE ?"
            params.append(f"%{server_filter}%")

        base_sql += " ORDER BY "
        if my_server:
            base_sql += "CASE WHEN p.server LIKE ? THEN 0 ELSE 1 END, "
            params.append(f"%{my_server}%")
        base_sql += "RANDOM() LIMIT 1"

        cursor = await db.execute(base_sql, params)
        row = await cursor.fetchone()
        if row:
            return Profile(
                id=row["id"],
                user_id=row["user_id"],
                nickname=row["nickname"],
                world_level=row["world_level"],
                main_dps=row["main_dps"],
                server=row["server"],
                description=row["description"] or None,
                photo_file_id=row["photo_file_id"] or None
            )
        return None


async def add_interaction(from_user_id: int, to_user_id: int, action: str) -> None:
    """Add like or dislike interaction."""
    from datetime import datetime
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO interactions (from_user_id, to_user_id, action, created_at) VALUES (?, ?, ?, ?)",
            (from_user_id, to_user_id, action, datetime.utcnow().isoformat())
        )
        await db.commit()


async def check_mutual_like(user_id_a: int, user_id_b: int) -> bool:
    """Check if both users liked each other."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """SELECT 1 FROM interactions
               WHERE from_user_id = ? AND to_user_id = ? AND action = 'like'
               INTERSECT
               SELECT 1 FROM interactions
               WHERE from_user_id = ? AND to_user_id = ? AND action = 'like'""",
            (user_id_a, user_id_b, user_id_b, user_id_a)
        )
        return await cursor.fetchone() is not None


async def get_mutual_likes(user_id: int) -> list[Profile]:
    """Get list of profiles that have mutual likes with user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT p.id, p.user_id, p.nickname, p.world_level, p.main_dps, p.server, p.description, p.photo_file_id
            FROM profiles p
            WHERE EXISTS (
                SELECT 1 FROM interactions i1
                WHERE i1.from_user_id = ? AND i1.to_user_id = p.user_id AND i1.action = 'like'
            )
            AND EXISTS (
                SELECT 1 FROM interactions i2
                WHERE i2.from_user_id = p.user_id AND i2.to_user_id = ? AND i2.action = 'like'
            )
        """, (user_id, user_id))
        rows = await cursor.fetchall()
        return [
            Profile(
                id=row["id"],
                user_id=row["user_id"],
                nickname=row["nickname"],
                world_level=row["world_level"],
                main_dps=row["main_dps"],
                server=row["server"],
                description=row["description"] or None,
                photo_file_id=row["photo_file_id"] or None
            )
            for row in rows
        ]


async def get_admin_stats() -> dict:
    """Статистика для админ-панели."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM profiles")
        total_profiles = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM interactions WHERE action = 'like'")
        total_likes = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM reports")
        total_reports = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM banned_users")
        total_banned = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "total_profiles": total_profiles,
            "total_likes": total_likes,
            "total_reports": total_reports,
            "total_banned": total_banned,
        }


async def get_all_telegram_ids() -> list[int]:
    """Все telegram_id пользователей с профилями (для рассылки)."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """SELECT u.telegram_id FROM users u
               JOIN profiles p ON p.user_id = u.id
               WHERE u.id NOT IN (SELECT user_id FROM banned_users)"""
        )
        return [row[0] for row in await cursor.fetchall()]
