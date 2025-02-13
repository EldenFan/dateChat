import aiosqlite
import asyncio


async def start_bd(): 
    conn = await aiosqlite.connect('database.db')
    
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('''CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                gender TEXT,
                search_gender TEXT,
                goal TEXT,
                preferences TEXT,
                description TEXT,
                image TEXT,
                location TEXT
            )''')
            
            await cursor.execute('''CREATE TABLE IF NOT EXISTS likes (
                user_id INTEGER,
                profile_id INTEGER,
                action TEXT, -- 'like' или 'dislike'
                PRIMARY KEY (user_id, profile_id)
            )''')
        
        await conn.commit()
    finally:
        await conn.close()

async def create_user(user_id, name, gender, search_gender, goal, preferences, description, image, location):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''INSERT OR REPLACE INTO profiles
                                (user_id, name, gender, search_gender, goal, preferences, description, image, location)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (user_id, name, gender, search_gender, goal, preferences, description, image, location))
        await conn.commit()


async def get_user(user_id):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''SELECT name, gender, search_gender, goal, preferences, description, image, location 
                            FROM profiles WHERE user_id = ?''', (user_id, ))
        row = await cursor.fetchone()
        if row:
            return {
                    "name": row[0],
                    "gender": row[1],
                    "search_gender": row[2],
                    "goal": row[3],
                    "preferences": row[4],
                    "description": row[5],
                    "image": row[6],
                    "location": row[7]
                }
        else:
            return None
    await conn.close()
