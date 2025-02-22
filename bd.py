import aiosqlite
import distance

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
                FOREIGN KEY (trait_id) REFERENCES preference_table(id) ON DELETE CASCADE
            )''')
            
            await cursor.execute('''CREATE TABLE IF NOT EXISTS selfcharacters(
                user_id INTEGER,
                trait_id INTEGER,
                PRIMARY KEY (user_id, trait_id),
                FOREIGN KEY (user_id) REFERENCES profiles(user_id) ON DELETE CASCADE,
                FOREIGN KEY (trait_id) REFERENCES preference_table(id) ON DELETE CASCADE
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

async def matching_profiles(user_id):
    conn = await aiosqlite.connect('database.db')
    current_user = await get_user(user_id)
    if current_user is None:
        return None
    else:
        async with conn.cursor() as cursor:
                await cursor.execute('''SELECT name, gender, search_gender, goal, preferences, description, image, location 
                                        FROM profiles 
                                        WHERE gender = ? AND goal = ? AND user_id != ?''', 
                                    (current_user["search_gender"], current_user["goal"], user_id))
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
                    "preferences": row[4],
                    "description": row[5],
                    "image": row[6],
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
                    "preferences": row[4],
                    "description": row[5],
                    "image": row[6],
                    "distance": None
                    }
                    )
                else:
                    profile_location = distance.parse_location(row[7])
                    distance = distance.calculate_distance(current_location, profile_location)
                    if distance <= 10:
                        profiles.append(
                            {
                            "name": row[0],
                            "gender": row[1],
                            "search_gender": row[2],
                            "goal": row[3],
                            "preferences": row[4],
                            "description": row[5],
                            "image": row[6],
                            "distance": distance
                            }
                        )
        return profiles  

async def add_trait(name):
    conn = await aiosqlite.connect('database.db')
    async with conn.cursor() as cursor:
        await cursor.execute('''INSERT INTO traits (name) VALUES (?)''', (name, ))
        await conn.commit()
    