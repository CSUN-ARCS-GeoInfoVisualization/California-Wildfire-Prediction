from pymongo.mongo_client import MongoClient
from flask import Flask, render_template, url_for,request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

client = MongoClient('localhost', 27017)
db = client["cwp_prod"]
coll = db.main

@app.route('/dbtest')
def db_test():

    year_param = request.args.get('year')

    # 1
    _1 = coll.find({"year": int(year_param)}, {"_id": 0})
    return(list(_1))

if __name__ == "__main__":
    app.run()
