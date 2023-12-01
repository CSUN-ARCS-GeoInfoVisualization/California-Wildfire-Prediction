from flask import Flask, render_template, url_for, request
from datetime import date

# LIST OF STRINGS FILLED WITH CALIFORNA COUNTY NAMES
# Format: <BLANK>,<COUNTY NAME>,...
# TODO: Fill in the rest of the CountyList
CountyList = ["","Alameda",
              "","Alpine"
              ]

## Finds and returns a value from file 'filePath' from day 'date' and county 'county' ##
## Returns the string "No Value" if it can't find a value ##
def findValue(start_date, end_date, county, filePath):
    file = open(filePath, 'r')
    line = file.readline()
    line = file.readline() # Skip Header
    matches = []

    while (line != ''):
        line_check = [str(x) for x in line.split(",")]
        if ((start_date <= date.fromisoformat(toISO(line_check[0])) <= end_date)
        and (county in line)):
            matches.append(line_check)
        line = file.readline()

    file.close()

    if matches == []:
        return "No Value"

    for i in matches:
        i[0] = date.fromisoformat(toISO(i[0]))
        
    ret_list = []
    for i in matches:
        # <County>  |  <Date>  |  <Value>
        ap_str = i[3][:-1] + "  |  " + str(i[0]) + "  |  " + i[1]
        ret_list.append(ap_str)

    ret_list.sort()
    
    return ret_list

## Converts the county id into a string ##
def formatCounty(county):
    return "," + f"{county:03d}"+ "," + CountyList[county] + "\n"

## Converts the date from mm/dd/yyyy to yyyy-mm-dd##
def toISO(date):
    m, d, y = [str(x) for x in date.split('/')]
    return y + "-" + m + "-" + d

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
    sd = request.args.get('start_date', default = "", type = str)
    ed = request.args.get('end_date', default = "", type = str)
    county = request.args.get('county', default = 0, type = int)
    print(sd)       # DEBUG
    print(ed)       # DEBUG
    print(county)   # DEBUG

    # REFACTOR 'county' to allow multiple inputs
    if (county < 1 or sd == ""): # NO DATA ENTERED
        print("No Data Entered")
        return render_template('data.html')
    
    try:
        start_date = date.fromisoformat(sd)
        end_date = date.fromisoformat(ed) if (not ed == "") else ""
    except: ## INVALID DATE ENTRY
        print("Invalid date entry!")
        return render_template('data.html')    

    print(start_date)     # DEBUG date : <year>-<month>-<day>
    print(end_date)
    
    if (start_date == ""): ## ERROR - NO START DATE SELECTED
        print("ENTER START DATE!")
        return render_template('data.html')

    if (end_date != "" and start_date > end_date): ## ERROR - INVALID END DATE
        print("END DATE IS LARGER THAN START DATE")
        return render_template('data.html')

    if (county > 115 or county % 2 == 0): #ERROR - INVALID COUNTY
        return render_template('data.html')
    
    # TODO: Find info in file(s)
    find_county = formatCounty(county)
    print(find_county)                  # DEBUG

    value_NDVI = findValue(start_date, end_date, find_county, "Data Processing/output/NDVI_result.csv")
    for i in value_NDVI:
        print(i)
    
    return render_template('data.html')

@app.route('/models')
def models():
    return render_template('models.html')


if __name__ == "__main__":
    app.run(debug=True)
