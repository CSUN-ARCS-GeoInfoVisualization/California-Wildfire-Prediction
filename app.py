from flask import Flask, render_template, url_for, request

# LIST OF STRINGS FILLED WITH CALIFORNA COUNTY NAMES
# Format: <BLANK>,<COUNTY NAME>,...
# TODO: Fill in the rest of the CountyList
CountyList = ["","Alameda",
              "","Alpine"
              ]

## Finds and returns a value from file 'filePath' from day 'date' and county 'county' ##
## Returns the string "No Value" if it can't find a value ##
def findValue(date, county, filePath):
    file = open(filePath, 'r')
    line = file.readline()

    while (line != ''):
        if (date in line) and (county in line):
            break
        line = file.readline()

    file.close()

    if line == '':
        return "No Value"

    # Converts 'line' into an array with each element seperated by ',' and returns the second item in it
    return [str(x) for x in line.split(",")][1]

## Converts the county id into a string ##
def formatCounty(county):
    return "," + f"{county:03d}"+ "," + CountyList[county] + "\n"

## Converts the date from yyyy-mm-dd to mm/dd/yyyy ##
def formatDate(date):
    y, m, d = [str(x) for x in date.split('-')]
    return m + "/" + d + "/" + y + ","

## Checks to see if a date entered is a valid date ##
def validDate(date):

    # Type Check
    try:
        y, m, d = [int(x) for x in date.split('-')]
    except:
        return False

    # Date Validation
    if (y < 0):
        return False
    if (m < 1 or m > 12):
        return False

    if (m == 2):                            # february
        if (y % 400 == 0):                      #LEAP
            return (d > 0 and d < 30)
        elif (y % 100 == 0 and y % 400 != 0):   #NO LEAP
            return (d > 0 and d < 29)           
        elif (y % 4 == 0 and y % 100 != 0):     #LEAP
            return (d > 0 and d < 30)
        return (d > 0 and d < 29)               #NO LEAP
    elif (m <= 7 and m != 2):
        return (d > 0 and d < 31 + (m % 2))
    else:
        return (d > 0 and d < 31 + ((m + 1) % 2))

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

    if (county < 1): # NO DATA ENTERED
        return render_template('data.html')

    if (date == ""): ## ERROR - NO DATE SELECTED
        return render_template('data.html')

    print(validDate(date)) # DEBUG - Valid Date
    if (not validDate(date)): ## ERROR - INVALID DATE
        return render_template('data.html')

    if (county > 115 or county % 2 == 0): #ERROR - INVALID COUNTY
        return render_template('data.html')
    
    # TODO: Find info in file(s)
    find_date = formatDate(date)
    print(find_date)                    # DEBUG
    find_county = formatCounty(county)
    print(find_county)                  # DEBUG

    value_NDVI = findValue(find_date, find_county, "Data Processing/output/NDVI_result.csv")
    print(value_NDVI)
    
    return render_template('data.html')

@app.route('/models')
def models():
    return render_template('models.html')


if __name__ == "__main__":
    app.run(debug=True)
