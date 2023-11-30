from flask import Flask, render_template, url_for, request

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

@app.route('/data')
def data():
    date = request.args.get('date', default = "", type = str)
    county = request.args.get('county', default = 0, type = int)
    print(date)     # DEBUG date : <year>-<month>-<day>
    print(county)   # DEBUG

    if (county < 1):
        return render_template('data.html')

    # TODO: Validate date and find info in file(s)
    return render_template('data.html')

@app.route('/models')
def models():
    return render_template('models.html')


if __name__ == "__main__":
    app.run(debug=True)
