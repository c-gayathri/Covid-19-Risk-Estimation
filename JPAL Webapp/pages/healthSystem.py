import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import gspread
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
from app import app

# --------------------------- Processing Information from the Google Sheet --------------------------------

# Getting values from the google spreadsheet
gc = gspread.service_account(filename = 'cred.json')
sh = gc.open_by_key('1TFvNZqHILzKK7VttupYZgrSNgiZXkGlEicvc50VhGvM')

# Generating a dataframe from the sheet 'HealthSystem'
healthsys = sh.worksheet('HealthSystem') # Opening the sheet named 'HealthSystem'
healthsys = healthsys.get_all_values() 
healthsys = pd.DataFrame.from_records(healthsys)
healthsys.columns = list(healthsys.iloc[0]) # Reassigning the first row as column names
healthsys = healthsys.drop(0)

# Get the ID string of the latest form response
latest = sh.worksheet('Looking up latest')
string = latest.get('F2') # ID string stored in F2 cell of sheet named 'Looking up latest'

# Based on inputs from the user, an ID string is generated for each user. 
# The input parameters are gender, city, age and whether they have diabetes and hypertension
# Each parameter value is coded with a digit
# eg: 1 for female and 2 for male
# eg ID string: 11100
gender, city, age, diabetes, hyper = list(string[0][0]) # Break the ID string to get the single digit codes for each parameter

# --------------------------- Defining the App Layout -------------------------------- 

layout = dbc.Container([
    html.H1("Health System Response", style={'text-align': 'center'}), # Heading
    dcc.Store(id='health_store', storage_type='session'), # Used to store a value that can be used across pages. 
    # This will store the final value due to health system risk and will beused to calculate the overall risk later

    dbc.Row([
        # Dropdown for selecing city
        html.H3('Select your City', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'city', options = [
            {'label': 'Delhi', 'value': 1}, 
            {'label': 'Chennai', 'value': 2}
        ],
        value = city, # By dafault, it displays the value chosen by the user when filling the form
        persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
        placeholder = 'Select your City'
        )

        ])

    ]),

    # Placeholders for graphs/figures
    dbc.Row([html.H2('Hospital Bed Occupancy'), dcc.Graph(id='bed_fig'), html.Div(id='bed_level')]),
    dbc.Row([html.H2('ICU Occupancy'), dcc.Graph(id='icu_fig'), html.Div(id='icu_level')]),
    dbc.Row([html.H2('Health System Response Risk (Cumulative)'), dcc.Graph(id='health_fig'), html.Div(id='health_level')])

])

# --------------------------- The Backend Processing for Calculating and Displaying Outputs -------------------------------- 

@app.callback(
    # Defining what to expect as output
    [Output(component_id = 'bed_fig', component_property = 'figure'), Output(component_id = 'bed_level', component_property = 'children'), 
    Output(component_id = 'icu_fig', component_property = 'figure'), Output(component_id = 'icu_level', component_property = 'children'),
    Output(component_id = 'health_fig', component_property = 'figure'), Output(component_id = 'health_level', component_property = 'children'),
    Output(component_id = 'health_store', component_property = 'data')],
    # Defining what to expect as input
    Input(component_id = 'city', component_property = 'value')
)
def update_graph(city_up):

    city_up = str(city_up) # the dataframe generated from the sheet stores all values as String

    fields = ['Hospital Bed Occupancy', 'ICU Bed Occupancy', 'Health System Response (Cumulative)'] # A list of the 3 fields that will be used for creating 3 linear gauges
    values = pd.DataFrame({fields[0]: [0,4,0.0], fields[1]: [0,4,0.0], fields[2]: [0,4,0.0]})
    # Created a dataframe where each column is for one indicator
    # The first row (index 0) will store the value the linear gauge uses to set the pointer (here it takes discrete values and has 4 levels)
    # The second row (index 1) stores the upper limit this can obtain.
    # The third row (index 2) stores the original value of the indicator. This can be continuous and can thoretically take inifinite values

    # -------------------- Calculating the Health System Response ------------------------
    # Getting information about the number of vacant beds and ICUs from data frames
    beds = float(healthsys[healthsys['City_code'] == city_up]['Beds'])
    icu = float(healthsys[healthsys['City_code'] == city_up]['ICU'])
    values.iloc[2][fields[0]] = beds # Original value of the indicator stored in the third row (index 2) - see above
    values.iloc[2][fields[1]] = icu # Original value of the indicator stored in the third row (index 2) - see above

    # Create a list of the integer quotients when number of beds is divided by the threshold values 25, 50, 75 (percentages)
    # The four levels are defined as
    # < 25
    # between 25 and 50
    # between 50 and 75
    # > 100
    beds_quotients = [int(beds/d) for d in [25,50,75]]
    # Find the position of last non-zero quotient in the list.
    # This will be two less than the level mentioned in 'Indicators estimation.xlsx', that is, if the levels were 1,2,3,4
    beds_nonzero = np.nonzero(beds_quotients)[0] 
    if len(beds_nonzero) == 0:
        beds_level = 1 # if it gives a zero quotient when divided by all thresholds, then it is at the lowest level
    else:
        beds_level = beds_nonzero[-1] + 2

    # Use the similar method from above for getting the equivalent level
    icu_quotients = [int(icu/d) for d in [25, 50, 75]]
    icu_nonzero = np.nonzero(icu_quotients)[0]
    if len(icu_nonzero) == 0:
        icu_level = 1
    else:
        icu_level = icu_nonzero[-1] + 2
    print('icu_level')
    print(icu_level)

    # Create a lookup table for getting the Health System Response level from the level of ICU vacany and Bed vacancy
    # This table was based on the values given in 
    health_lookup = np.array([[1,2,2,3],[2,2,3,3],[2,3,3,4],[3,3,4,4]])
    healthSystem = health_lookup[icu_level - 1][beds_level - 1] # The indices are from 0 and not 1

    # Update the values the linear gauge must be set to
    values.iloc[0][fields[0]] = beds_level
    values.iloc[0][fields[1]] = icu_level
    values.iloc[0][fields[2]] = healthSystem 

    outputs = [] # The outputs will be stored here
    reds = ['#fbc4ab', '#f8ad9d', '#f4978e', '#f08080'] # The colour hexcodes for the red linear gauge
    violets = ['#c77dff', '#9d4edd', '#5a189a', '#240046'] # The colour hexcodes for the purple linear gauge
    colours = {fields[0]: reds, fields[1]: reds, fields[2]: violets} # Allot the colours for each indicator

    # Loop through all sub-indicators to create a linear gauge for each indicator and store this in the list 'outputs'
    for f in fields:

        fig = go.Figure()

        limit = values.iloc[1][f] # Get the upper limit for this indicator
        value = values.iloc[0][f] # Get the value the linear gauge must be set to for this indicator

        palette = colours[f] # get the colours for this linear gauge

        fig.add_trace(go.Indicator(
            mode = 'gauge',
            value = float(value - 0.5), # Subtract the value the pointer must be set to by 0.5
            # This is so that the pointer is at the centre and not the edge of each coloured rectange in the linear gauge
            # The range of the linear gauge is broken into 4 equal parts: very low, low, high and very high
            delta = {'reference': limit}, 
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f}, 
            gauge = {
                'shape': "bullet",
                'axis': {'range': [None, limit]},
                'steps': [
                    # Set the colour for each threshold range
                    {'range': [0, limit/4], 'color': palette[0]},
                    {'range': [limit/4, limit/2], 'color': palette[1]},
                    {'range': [limit/2, limit*3/4], 'color': palette[2]},
                    {'range': [limit*3/4, limit], 'color': palette[3]}],
                'bar': {'color': '#FFFFFF'}})) # Set the clour of the horizontal pointer bar to white

        fig.update_layout(height = 80, margin = {'t':0, 'b':0, 'l':0})

        text = {0:'very low', 1:'low', 2:'high', 3:'very high'} # Assign text levels for each indicator value

        if f in fields[:2]:
            outputs.extend([fig, text[value - 1] + ' - ' + str(values.iloc[2][f])]) # Add the text level to the output
            # This is a function of the value of the indicator
        else:
            outputs.extend([fig, text[value - 1]])

    outputs.append(healthSystem/4) # This is the normalised value of the indicator that will passed on to the page for calculating overall risk

    return outputs

if __name__ == '__main__':
    app.run_server(debug=True)