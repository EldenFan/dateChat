import aiosqlite
import math

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
        print(current_user["location"])
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
            current_location = parse_location(current_user["location"])
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
                    profile_location = parse_location(row[7])
                    distance = calculate_distance(current_location, profile_location)
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



def parse_location(location):
    latitude, longitude = map(float, location.split(","))
    return latitude, longitude

def calculate_distance(loc1, loc2):
    lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
    lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    R = 6371.0
    distance = R * c
    return distance