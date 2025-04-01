from pymongo import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

# Access the database and collection
db = client.students_database  # Replace with your database name
students_collection = db.students  # Collection named 'students'

# Prepare student data
# permission = 0 for students, 1 for teachers
students_data = [
    {"id": 1, "name": "Mercedes Tyler", "netid": "21000000D", "role": "teacher", "permission": "teacher", "email": "mercedes_tyler@connect.polyu.hk", "password": "password1", "group":"1"},
    {"id": 2, "name": "John Doe", "netid": "21000001D",  "role": "student", "permission": "leader", "email": "john_doe@connect.polyu.hk", "password": "password2",  "group":" "},
    {"id": 3, "name": "Jane Smith", "netid": "21000002D", "role": "student", "permission": "member", "email": "jane_smith@connect.polyu.hk", "password": "password3", "group":" "},
    {"id": 4, "name": "Alice Johnson", "netid": "21000003D", "role": "student", "permission": "member", "email": "alice_johnson@connect.polyu.hk", "password": "password4", "group":" "},
    {"id": 5, "name": "Bob Brown", "netid": "21000004D", "role": "student", "permission": "member", "email": "bob_brown@connect.polyu.hk", "password": "password5", "group":" "},
    {"id": 6, "name": "Charlie Davis", "netid": "21000005D", "role": "student", "permission": "teacher", "email": "charlie_davis@connect.polyu.hk", "password": "password6","group":" "},
    {"id": 7, "name": "Diana Prince", "netid": "21000006D", "role": "student", "permission": "leader", "email": "diana_prince@connect.polyu.hk", "password": "password7", "group":" "},
    {"id": 8, "name": "Ethan Hunt", "netid": "21000007D", "role": "student", "permission": "member", "email": "ethan_hunt@connect.polyu.hk", "password": "password8", "group":""},
    {"id": 9, "name": "Fiona Gallagher", "netid": "21000008D", "role": "student", "permission": "member", "email": "fiona_gallagher@connect.polyu.hk", "password": "password9", "group":""},
    {"id": 10, "name": "George Clooney", "netid": "21000009D", "role": "student", "permission": "member", "email": "george_clooney@connect.polyu.hk", "password": "password10" , "group":" "},
    {"id": 11, "name": "Hannah Montana", "netid": "21000010D", "role": "student", "permission": "teacher", "email": "hannah_montana@connect.polyu.hk", "password": "password11", "group":" "},
    {"id": 12, "name": "Ivy League", "netid": "21000011D", "role": "student", "permission": "leader", "email": "ivy_league@connect.polyu.hk", "password": "password12", "group":""},
    {"id": 13, "name": "Jack Sparrow", "netid": "21000012D", "role": "student", "permission": "member", "email": "jack_sparrow@connect.polyu.hk", "password": "password13" , "group":" "},
    {"id": 14, "name": "Katy Perry", "netid": "21000013D", "role": "student", "permission": "member", "email": "katy_perry@connect.polyu.hk", "password": "password14", "group":" "},
    {"id": 15, "name": "Liam Neeson", "netid": "21000014D", "role": "student", "permission": "member", "email": "liam_neeson@connect.polyu.hk", "password": "password15"  , "group":" "},
    {"id": 16, "name": "Mia Wallace", "netid": "21000015D",  "role": "teacher", "permission": "teacher", "email": "mia_wallace@connect.polyu.hk", "password": "password16", "group":" "},
    {"id": 17, "name": "Nina Simone", "netid": "21000016D", "role": "student", "permission": "leader", "email": "nina_simone@connect.polyu.hk", "password": "password17", "group":" "},
    {"id": 18, "name": "Oscar Wilde", "netid": "21000017D", "role": "student", "permission": "member", "email": "oscar_wilde@connect.polyu.hk", "password": "password18", "group":" "},
    {"id": 19, "name": "Peter Parker", "netid": "21000018D", "role": "student", "permission": "member", "email": "peter_parker@connect.polyu.hk", "password": "password19", "group":" "},
    {"id": 20, "name": "Quinn Fabray", "netid": "21000019D", "role": "student", "permission": "member", "email": "quinn_fabray@connect.polyu.hk", "password": "password20"  , "group":" "},
]

# Update existing records
for student in students_data:
    query = {"netid": student["netid"]}
    update = {"$set": {key: value for key, value in student.items() if key != "netid" and key != "id"}}
    
    result = students_collection.update_one(query, update)
    if result.modified_count > 0:
        print(f"Updated record for netid: {student['netid']}")
    else:
        print(f"No changes made for netid: {student['netid']} (might not exist or already up to date)")

print("Records processed.")