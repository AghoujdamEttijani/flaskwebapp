from pymongo import MongoClient

# Replace with your actual MongoDB URI
client = MongoClient("mongodb://localhost:27017/")

# Access a database
db = client["milk_store"]

# Access a collection (like a table)
collection = db["personal_information"]

# Get all documents
documents = collection.find()

# Print each document
for doc in documents:
    print(doc)
