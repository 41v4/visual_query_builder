from pymongo import MongoClient

class Connect():
    @staticmethod    
    def get_connection(URI=None, timeout=None):
    	if URI:
            return MongoClient(URI, serverSelectionTimeoutMS=timeout)
    	else:
    		return MongoClient(serverSelectionTimeoutMS=timeout)

class Explore():
	@staticmethod
	def get_databases(connection):
		return connection.list_database_names()
	def get_collections(connection, database):
		db = connection[database]
		return db.list_collection_names()