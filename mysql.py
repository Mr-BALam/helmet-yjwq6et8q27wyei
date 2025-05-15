# import mysql.connector
# from flask import Flask, request, jsonify

# app = Flask(__name__)

# # Configure your database connection
# db_config = {
#     'host': 'localhost',
#     'user': 'your_username',
#     'password': 'your_password',
#     'database': 'your_database'
# }

# @app.route('/data', methods=['POST'])
# def receive_data():
#     data = request.json
#     if data:
#         person_id = data.get("person_id")
#         name = data.get("name")
#         timestamp = data.get("timestamp")

#         if not person_id:
#             return jsonify({"error": "No person ID provided"}), 400

#         try:
#             conn = mysql.connector.connect(**db_config)
#             cursor = conn.cursor()

#             # Replace table_name and columns with your actual table/columns
#             cursor.execute(
#                 "INSERT INTO your_table (person_id, name, timestamp) VALUES (%s, %s, %s)",
#                 (person_id, name, timestamp)
#             )
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return jsonify({"message": "Data saved to MySQL"}), 200

#         except mysql.connector.Error as err:
#             return jsonify({"error": f"Database error: {err}"}), 500

#     return jsonify({"error": "No data received"}), 400





# @app.route('/data', methods=['GET'])
# def fetch_data():
#     try:
#         conn = mysql.connector.connect(**db_config)
#         cursor = conn.cursor(dictionary=True)  # dictionary=True gives us a list of dicts

#         cursor.execute("SELECT * FROM your_table")
#         results = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         return jsonify(results), 200

#     except mysql.connector.Error as err:
#         return jsonify({"error": f"Database error: {err}"}), 500
