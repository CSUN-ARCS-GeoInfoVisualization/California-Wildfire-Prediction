from flask import Flask, render_template, url_for, request, send_file
from io import BytesIO
from datetime import date

# LIST OF STRINGS FILLED WITH CALIFORNA COUNTY NAMES
# Format: <BLANK>,<COUNTY NAME>,...
CountyList = ["","Alameda",
              "","Alpine",
              "","Amador",
              "","Butte",
              "","Calaveras",
              "","Colusa",
              "","Contra Costa",
              "","Del Norte",
              "","El Dorado",
              "","Fersno",
              "","Glenn",
              "","Humboldt",
              "","Imperial",
              "","Inyo",
              "","Kern",
              "","Kings",
              "","Lake",
              "","Lassen",
              "","Los Angeles",
              "","Madera",
              "","Marin",
              "","Mariposa",
              "","Mendocino",
              "","Merced",
              "","Modoc",
              "","Mono",
              "","Monterey",
              "","Napa",
              "","Nevada",
              "","Orange",
              "","Placer",
              "","Plumas",
              "","Riverside",
              "","Sacramento",
              "","San Benito",
              "","San Bernardino",
              "","San Diego",
              "","San Francisco",
              "","San Joaquin",
              "","San Luis Obispo",
              "","San Mateo",
              "","Santa Barbara",
              "","Santa Clara",
              "","Santa Cruz",
              "","Shasta",
              "","Sierra",
              "","Siskiyou",
              "","Solano",
              "","Sonama",
              "","Stanislaus",
              "","Sutter",
              "","Tehama",
              "","Trinity",
              "","Tulare",
              "","Tuolume",
              "","Ventura",
              "","Yolo",
              "","Yuba"
              ]

## Generates the file to download ##
def createFile(data):
    file_data = bytearray('\n'.join(data) , "utf-8")
    return send_file(BytesIO(file_data), download_name = "dataset.txt", as_attachment = True)

## Finds and returns a value from file 'filePath' from day 'date' and county 'county' ##
## Returns an empty array if it can't find a value ##
def findValue(start_date, end_date, county, filePath):
    file = open(filePath, 'r')
    line = file.readline()
    line = file.readline() # Skip Header
    matches = []

    if (end_date == ""): # Only Start Date
        end_date = start_date

    while (line != ''):
        line_check = [str(x) for x in line.split(",")]
        if ((start_date <= date.fromisoformat(toISO(line_check[0])) <= end_date)
        and (county in line)):
            matches.append(line_check)
        line = file.readline()

    file.close()

    if matches == []:
        return []

    for i in matches:
        i[0] = date.fromisoformat(toISO(i[0]))
        
    ret_list = []
    for i in matches:
        # <County>  |  <Date>  |  <Value>
        ap_str = i[3][:-1] + "  |  " + str(i[0]) + "  |  " + i[1]
        ret_list.append(ap_str)

    ret_list.sort()
    ret_list.append("")
    
    return ret_list

## Converts the county id into a string ##
def formatCounty(county):
    try:
        return "," + f"{county:03d}"+ "," + CountyList[county] + "\n"
    except:         # Out of range index
        return ""
        
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
    county = request.args.getlist('county', type = int)
    print(sd)       # DEBUG
    print(ed)       # DEBUG
    print(county)   # DEBUG

    if (len(county) == 0 or sd == ""): # NO DATA ENTERED
        return render_template('data.html')
    
    try:
        start_date = date.fromisoformat(sd)
        end_date = date.fromisoformat(ed) if (not ed == "") else ""
    except: ## INVALID DATE ENTRY
        print("Invalid date entry!")
        return render_template('data.html')    

    print(start_date)     # DEBUG date : <year>-<month>-<day>
    print(end_date)
    
    value_NDVI = []
    value_NDVI.append(["<County>  |  <Date>  |  <NDVI>", ""])
        
    for i in county:
        find_county = formatCounty(i)
        print(find_county)                  # DEBUG

        value_NDVI.append(
            findValue(start_date, end_date, find_county, "Data Processing/output/NDVI_result.csv")
        )

    value_NDVI = sum(value_NDVI, []) # Flatens the list
    
    for i in value_NDVI: # DEBUG, OUTPUT
        print(i)
    
    return createFile(value_NDVI)

@app.route('/models')
def models():
    return render_template('models.html')


if __name__ == "__main__":
    app.run(debug=True)
