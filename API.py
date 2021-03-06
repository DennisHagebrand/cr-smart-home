import MySQLdb
import collections
import sys
import json
from flask import Flask, jsonify, abort, make_response, request
from flask.ext.httpauth import HTTPBasicAuth
from Lamp import Lamp
from Config import Config

app = Flask(__name__)
auth = HTTPBasicAuth()

#---------------------------------------------------------------------------# 
# Hello World
#---------------------------------------------------------------------------#
@app.route("/")
@auth.login_required
def hello():
	return "Hello World!"

#---------------------------------------------------------------------------# 
# Get all lamps
#---------------------------------------------------------------------------#
@app.route("/ha/api/v1.0/lamps", methods=['GET'])
@auth.login_required
def get_lamps():
	lamps = []

	#Connect to MySQL
	db = MySQLdb.connect(Config.DbHost, Config.DbUser, Config.DbPassword, Config.DbName)
	cursor = db.cursor()

	try:
		#Execure SQL-Query
		cursor.execute("SELECT * FROM ha_lamp_objects ORDER BY LampOrder ASC")
		results = cursor.fetchall()
	
		#Loop result from database
		for row in results:
			#Move database row to variables
			d = collections.OrderedDict()
			d['Id'] = row[0]
			d['RoomId'] = row[1]
			d['Name'] = row[2]
			d['Type'] = row[3]
			d['PowerOn'] = row[4]
			d['PowerOnMan'] = row[5]
			d['CmdOn'] = row[6]
			d['CmdOff'] = row[7]
			d['IncInAll'] = row[8]
			d['Order'] = row[9]
			lamps.append(d)
	except MySQLdb.Error, e:
		#Log exceptions
		try:
			return make_response(jsonify({'MySQL-Error': e.args[1]}), 500)
		except IndexError:
			return make_response(jsonify({'MySQL-Error': str(e)}), 500)

	finally:
		#Close database connection
		cursor.close()
		db.close()

	return jsonify({'lamps': lamps})

#---------------------------------------------------------------------------# 
# Get one lamp
#---------------------------------------------------------------------------#
@app.route('/ha/api/v1.0/lamps/<int:lamp_id>', methods=['GET'])
@auth.login_required
def get_lamp(lamp_id):
	#Connect to MySQL
	db = MySQLdb.connect(Config.DbHost, Config.DbUser, Config.DbPassword, Config.DbName)
	cursor = db.cursor()

	try:
		#Execure SQL-Query
		cursor.execute("SELECT * FROM ha_lamp_objects WHERE LampId=%d", lamp_id)
		results = cursor.fetchall()
	
		#Loop result from database
		for row in results:
			#Move database row to variables
			d = collections.OrderedDict()
			d['Id'] = row[0]
			d['Name'] = row[1]
			d['Type'] = row[2]
			d['PowerOn'] = row[3]
			d['PowerOnMan'] = row[4]
			d['CmdOn'] = row[5]
			d['CmdOff'] = row[6]
	except MySQLdb.Error, e:
		#Log exceptions
		try:
			return make_response(jsonify({'MySQL-Error': e.args[1]}), 500)
		except IndexError:
			return make_response(jsonify({'MySQL-Error': str(e)}), 500)

	finally:
		#Close database connection
		cursor.close()
		db.close()

	return jsonify({'lamps': d})

#---------------------------------------------------------------------------# 
# Send power to single lamp
#---------------------------------------------------------------------------#
@app.route('/ha/api/v1.0/lamps/single', methods=['POST'])
@auth.login_required
def powersingle():
	if not request.json or not 'id' in request.json or not 'PowerOn' in request.json:
		abort(400)

	lamp = Lamp()
	result = lamp.PowerSingle(request.json['id'], request.json['PowerOn'])

	json = {
		'id': request.json['id'],
		'PowerOn': request.json['PowerOn'],
		'result': result
	}

	return jsonify({'lamp': json})

#---------------------------------------------------------------------------# 
# Send power to all lamps in room
#---------------------------------------------------------------------------#
@app.route('/ha/api/v1.0/lamps/room', methods=['POST'])
@auth.login_required
def powerroom():
	if not request.json or not 'id' in request.json or not 'PowerOn' in request.json:
		abort(400)
	
	lamp = Lamp()
	result = lamp.PowerRoom(request.json['id'], request.json['PowerOn'])

	json = {
		'id': request.json['id'],
		'PowerOn': request.json['PowerOn'],
		'result': result
	}

	return jsonify({'lamp': json})
	
#---------------------------------------------------------------------------# 
# Send power to all lamps
#---------------------------------------------------------------------------#
@app.route('/ha/api/v1.0/lamps/all', methods=['POST'])
@auth.login_required
def powerall():
	if not request.json or not 'PowerOn' in request.json:
		abort(400)
	
	lamp = Lamp()
	result = lamp.PowerAll(request.json['PowerOn'])

	json = {
		'PowerOn': request.json['PowerOn'],
		'result': result
	}

	return jsonify({'lamp': json})
	
#---------------------------------------------------------------------------# 
# Get dashboard
#---------------------------------------------------------------------------#
@app.route("/ha/api/v1.0/dashboard", methods=['GET'])
@auth.login_required
def get_dashboard():
	rooms = []
	lamps = []
	sun = []
	weather = []

	#Connect to MySQL
	db = MySQLdb.connect(Config.DbHost, Config.DbUser, Config.DbPassword, Config.DbName)
	cursor = db.cursor()

	try:
		#Execure SQL-Query
		cursor.execute("SELECT t1.*, IFNULL(t2.RoomName, 'Lamps'), IFNULL(t2.RoomDescription, ''), IFNULL(t2.RoomOrder, 1000) FROM ha_lamp_objects t1 LEFT JOIN ha_rooms t2 ON LampRoomId = RoomId ORDER BY -LampRoomId DESC, RoomOrder ASC, LampOrder ASC")
		results = cursor.fetchall()

		nLastRoom = 0
		nLampCount = 0
		room = collections.OrderedDict()
		
		#Loop result from database
		for row in results:
			if (nLastRoom == 0):
				room['Id'] = row[1]
				room['Name'] = row[10]
				room['Description'] = row[11]
				room['Order'] = row[12]
				nLastRoom = row[1]
			
			if (nLastRoom <> row[1]):
				room['LampCount'] = nLampCount
				room['Lamps'] = lamps
				rooms.append(room)
				
				room = collections.OrderedDict()
				room['Id'] = row[1]
				room['Name'] = row[10]
				room['Description'] = row[11]
				room['Order'] = row[12]
				nLastRoom = row[1]
				nLampCount = 0
				
				lamps = []
						
			#Move database row to variables
			d = collections.OrderedDict()
			d['Id'] = row[0]
			d['RoomId'] = row[1]
			d['Name'] = row[2]
			d['Type'] = row[3]
			d['PowerOn'] = row[4]
			d['PowerOnMan'] = row[5]
			d['CmdOn'] = row[6]
			d['CmdOff'] = row[7]
			d['IncInAll'] = row[8]
			d['Order'] = row[9]
			lamps.append(d)
			
			nLampCount = nLampCount+1
			
		if cursor.rowcount > 0:
			room['LampCount'] = nLampCount
			room['Lamps'] = lamps
			rooms.append(room)
			
		#Execure SQL-Query
		cursor.execute("SELECT * FROM ha_data WHERE DataName='Sun'")
		results = cursor.fetchone()
	
		#Move database row to variables
		d = collections.OrderedDict()
		d['Id'] = results[0]
		d['Name'] = results[1]
		d['Data'] = json.loads(results[2])
		d['Status'] = results[3]
		d['LastUpdated'] = results[4].strftime("%Y-%m-%d %H:%M:%S")
		sun.append(d)
		
		#Execure SQL-Query
		cursor.execute("SELECT * FROM ha_data WHERE DataName='Weather'")
		results = cursor.fetchone()
	
		#Move database row to variables
		d = collections.OrderedDict()
		d['Id'] = results[0]
		d['Name'] = results[1]
		d['Data'] = json.loads(results[2])
		d['Status'] = results[3]
		d['LastUpdated'] = results[4].strftime("%Y-%m-%d %H:%M:%S")
		weather.append(d)
	except MySQLdb.Error, e:
		#Log exceptions
		try:
			return make_response(jsonify({'MySQL-Error': e.args[1]}), 500)
		except IndexError:
			return make_response(jsonify({'MySQL-Error': str(e)}), 500)

	finally:
		#Close database connection
		cursor.close()
		db.close()

	return jsonify({'rooms': rooms, 'sun': sun, 'weather': weather})

#---------------------------------------------------------------------------# 
# Login
#---------------------------------------------------------------------------#
@app.route('/ha/api/v1.0/login', methods=['POST'])
def login():
	if not request.json or not 'username' in request.json or not 'password' in request.json:
		abort(400)
		
	db = MySQLdb.connect(Config.DbHost, Config.DbUser, Config.DbPassword, Config.DbName)
	cursor = db.cursor()
	
	cursor.execute("SELECT SHA2(CONCAT(%s, UserSalt), 512) FROM ha_users WHERE UserName=%s AND SHA2(CONCAT(UserPassword, %s), 512) = SHA2(CONCAT(SHA2(CONCAT(%s, UserSalt), 512), %s), 512)", (request.json['password'], request.json['username'], request.user_agent.string, request.json['password'], request.user_agent.string))
	data = cursor.fetchone()
    
	if data is None:
		abort(401)
	else:
		json = {
			'username': request.json['username'],
			'password': data[0]
		}

	return jsonify({'login': json})

#---------------------------------------------------------------------------# 
# Authenticate
#---------------------------------------------------------------------------#
@auth.verify_password
def verify_password(username, password):
	
	db = MySQLdb.connect(Config.DbHost, Config.DbUser, Config.DbPassword, Config.DbName)
	cursor = db.cursor()
	
	cursor.execute("SELECT * FROM ha_users WHERE UserName = %s AND SHA2(CONCAT(UserPassword, %s), 512) = %s", (username, request.user_agent.string, password))
	data = cursor.fetchone()
    
	if data is None:
		return False
	else:
		return True

#---------------------------------------------------------------------------# 
# 404 Error
#---------------------------------------------------------------------------#
@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

#---------------------------------------------------------------------------# 
# Start app
#---------------------------------------------------------------------------#
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000, debug=False)
