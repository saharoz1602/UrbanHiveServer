from flask import Flask, request, jsonify
from flask_pymongo import PyMongo, ObjectId

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

# Reference to the students collection
students = mongo.db.students


@app.route('/users', methods=['GET'])
def get_user():
    return



@app.route('/student', methods=['POST'])
def add_user():
    return


@app.route('/student/<id>', methods=['GET'])
def get_user(id):
    return


@app.route('/student/<id>', methods=['PUT'])
def update_user(id):
    return


@app.route('/student/<id>', methods=['DELETE'])
def delete_user(id):
    return jsonify({"message": "Student deleted successfully"})


if __name__ == "__main__":
    app.run(debug=True)
