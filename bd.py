import aiosqlite
import distancelib

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
                description TEXT,
                image TEXT,
                location TEXT
            )''')
            
            await cursor.execute('''CREATE TABLE IF NOT EXISTS likes (
                user_id INTEGER,
                other_id INTEGER,
                action TEXT CHECK(action IN ('like', 'dislike')),
                PRIMARY KEY (user_id, other_id),
                FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE,
                FOREIGN KEY (other_id) REFERENCES profiles(user_id) ON DELETE CASCADE
            )''')

            await cursor.execute('''CREATE TABLE IF NOT EXISTS traits(
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')
            
            await cursor.execute('''CREATE TABLE IF NOT EXISTS preferences(
                user_id INTEGER,
                trait_id INTEGER,
                PRIMARY KEY (user_id, trait_id),
                FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE,
                FOREIGN KEY (trait_id) REFERENCES traits(id) ON DELETE CASCADE
            )''')
            
            await cursor.execute('''CREATE TABLE IF NOT EXISTS selfcharacters(
                user_id INTEGER,
                trait_id INTEGER,
                PRIMARY KEY (user_id, trait_id),
                FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE,
                FOREIGN KEY (trait_id) REFERENCES traits(id) ON DELETE CASCADE
            )''')
        
        await conn.commit()
    finally:
        await conn.close()

async def create_user(user_id, name, gender, search_gender, goal, description, image, location):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''INSERT OR REPLACE INTO profiles
                                (user_id, name, gender, search_gender, goal, description, image, location)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                             (user_id, name, gender, search_gender, goal, description, image, location))
        await conn.commit()

async def get_user(user_id):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''SELECT name, gender, search_gender, goal, description, image, location 
                            FROM profiles WHERE user_id = ?''', (user_id, ))
        base_row = await cursor.fetchone()
        if not base_row:
                return None
        res = {
                "name": base_row[0],
                "gender": base_row[1],
                "search_gender": base_row[2],
                "goal": base_row[3],
                "description": base_row[4],
                "image": base_row[5],
                "location": base_row[6]
            }
        await cursor.execute('''SELECT trait_id FROM preferences WHERE user_id = ?''', (user_id,))
        preference_rows = await cursor.fetchall()
        preference_trait_ids = [row[0] for row in preference_rows]
        await cursor.execute('''SELECT trait_id FROM selfcharacters WHERE user_id = ?''', (user_id,))
        selfcharacter_rows = await cursor.fetchall()
        selfcharacter_trait_ids = [row[0] for row in selfcharacter_rows]
        preferences = await get_traits_by_ids(cursor, preference_trait_ids)
        selfcharacters = await get_traits_by_ids(cursor, selfcharacter_trait_ids)
        res.update({
                "preferences": ", ".join(preferences) if preferences else None,
                "selfcharacters": ", ".join(selfcharacters) if selfcharacters else None
        })
    return res

async def matching_profiles(user_id):
    conn = await aiosqlite.connect('database.db')
    current_user = await get_user(user_id)
    if current_user is None:
        return None
    else:
        async with conn.cursor() as cursor:
                await cursor.execute('''SELECT name, gender, search_gender, goal, description, image, location 
                                        FROM profiles 
                                        WHERE gender = ? AND goal = ? AND search_gender = ? AND user_id != ?''', 
                                    (current_user["search_gender"], current_user["goal"], current_user["gender"], user_id))
                rows = await cursor.fetchall()
        profiles = []
        if current_user["location"] is None:
            for row in rows:
                profiles.append(
                    {
                    "name": row[0],
                    "gender": row[1],
                    "search_gender": row[2],
                    "goal": row[3],
                    "description": row[4],
                    "image": row[5],
                    "distance": None
                    }
                )
        else:
            current_location = distance.parse_location(current_user["location"])
            for row in rows:
                if row[7] is None:
                    profiles.append(
                    {
                    "name": row[0],
                    "gender": row[1],
                    "search_gender": row[2],
                    "goal": row[3],
                    "description": row[4],
                    "image": row[5],
                    "distance": None
                    }
                    )
                else:
                    profile_location = distancelib.parse_location(row[7])
                    distance = distancelib.calculate_distance(current_location, profile_location)
                    if distance <= 10:
                        profiles.append(
                            {
                            "name": row[0],
                            "gender": row[1],
                            "search_gender": row[2],
                            "goal": row[3],
                            "description": row[4],
                            "image": row[5],
                            "distance": distance
                            }
                        )
        return profiles  

async def add_trait(name):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''INSERT INTO traits (name) VALUES (?)''', (name, ))
        await conn.commit()

async def get_traits():
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''SELECT name 
                            FROM traits''')
        rows = await cursor.fetchall()
        traits = []
        for row in rows:
            traits.append(row[0])
    return traits 
        
async def set_preference(user_id, name):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''SELECT id FROM traits WHERE name = ?''', (name, ))
        trait_id = (await cursor.fetchone())[0]
        await cursor.execute('''INSERT INTO preferences (user_id, trait_id) VALUES (?, ?)''', (user_id, trait_id))
        await conn.commit()

async def set_selfcharacters(user_id, name):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''SELECT id FROM traits WHERE name = ?''', (name, ))
        trait_id = (await cursor.fetchone())[0]
        await cursor.execute('''INSERT INTO selfcharacters (user_id, trait_id) VALUES (?, ?)''', (user_id, trait_id))
        await conn.commit()

async def get_traits_by_ids(cursor, trait_ids):
    placeholders = ",".join(["?"] * len(trait_ids))
    await cursor.execute(f'''SELECT name FROM traits WHERE id IN ({placeholders})''', trait_ids)
    return [row[0] for row in await cursor.fetchall()]

async def delete_user(user_id):
    conn = await aiosqlite.connect('database.db')
    await conn.execute("PRAGMA foreign_keys = ON;")
    async with conn.cursor() as cursor:
        await cursor.execute('DELETE FROM profiles WHERE user_id = ?', (user_id,))
        await conn.commit()
