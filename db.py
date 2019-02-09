import sqlite3, os

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

dbname = 'gallery.db'
db = sqlite3.connect(dbname, check_same_thread = False)
db.row_factory = dict_factory
cursor = db.cursor()

def create():
    cursor.execute("""CREATE TABLE IF NOT EXISTS user (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            type VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL
            )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS scene (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            path VARCHAR(255) NOT NULL,
            type VARCHAR(255) NOT NULL,
            parent_id INTEGER
            )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS panorama (
            id INTEGER NOT NULL,
            child_id INTEGER NOT NULL PRIMARY KEY,
            x_ratio FLOAT NOT NULL,
            y_ratio FLOAT NOT NULL
            )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message VARCHAR(255) NOT NULL,
            date VARCHAR(255) NOT NULL,
            scene_id INTEGER NOT NULL
            )""")
    db.commit()

def getUser(username):
    cursor.execute("SELECT * FROM user WHERE name = ?", (username,))
    result = cursor.fetchall()
    if result == []: return None
    return result[0]

def getAllUser():
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    return users

def addUser(username, type, user_password, salt):
    sql = "INSERT INTO user (name, type, hashed_password, salt) VALUES (?, ?, ?, ?)"
    cursor.execute(sql, (username, type, user_password, salt))
    db.commit()

def getUserID(username):
    cursor.execute("SELECT id FROM user WHERE name = ?", (username,))
    result = cursor.fetchall()
    if result == []: return None
    return result[0]

def getAllStory():
    cursor.execute("SELECT scene.*, x_ratio, y_ratio FROM scene LEFT OUTER JOIN panorama ON scene.id = panorama.child_id")
    story = cursor.fetchall()
    return story

def get_scene(scene_id):
    cursor.execute("SELECT * FROM scene WHERE id = ?", (scene_id,))
    scene = cursor.fetchall()
    if scene == []: return None
    return scene[0]

def update_scene(scene_id, column, value):
    sql = "UPDATE scene SET {} = ? WHERE id = ?".format(column)
    cursor.execute(sql, (value, scene_id))
    db.commit()

def add_scene(name, path, scene_type, parent_id):
    sql = "INSERT INTO scene (name, path, type, parent_id) VALUES (?, ?, ?, ?)"
    cursor.execute(sql, (name, path, scene_type, parent_id))
    db.commit()
    cursor.execute("SELECT * FROM scene")
    scene = cursor.fetchall()
    return scene[-1]

def add_to_panorama(scene_id, child_id, x_ratio, y_ratio):
    if not child_id:
        cursor.execute("SELECT MAX(id) FROM scene")
        child_id = cursor.fetchone()["MAX(id)"]
    sql = "INSERT INTO panorama (id, child_id, x_ratio, y_ratio) VALUES (?, ?, ?, ?)"
    cursor.execute(sql, (scene_id, child_id, x_ratio, y_ratio))
    db.commit()

def delete_scene(scene_id):
    cursor.execute("SELECT id FROM scene WHERE parent_id = ?", (scene_id,))
    child_ids = cursor.fetchall()
    for child_id in child_ids:
        delete_scene(child_id["id"])
    os.remove("./static/" + get_scene(scene_id)["path"])
    cursor.execute("DELETE FROM scene WHERE id = ?" , (scene_id,))
    cursor.execute("DELETE FROM panorama WHERE id = ?", (scene_id,))
    cursor.execute("DELETE FROM feedback WHERE scene_id = ?", (scene_id,))
    db.commit()

def addFeedback(user_id, message, date, scene_id):
    sql = "INSERT INTO feedback (user_id, message, date, scene_id) VALUES (?, ?, ?, ?)"
    cursor.execute(sql, (user_id, message, date, scene_id))
    db.commit()

def selectFeedback(scene_ID):
    cursor.execute("SELECT * FROM feedback WHERE scene_id = ?", (scene_ID,))
    child_ids = cursor.fetchall()
    db.commit()
    return child_ids

def deleteFeedback(feedback_id):
    cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
