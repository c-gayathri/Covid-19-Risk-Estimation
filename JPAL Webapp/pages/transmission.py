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

# Generating a dataframe from the sheet 'Transmission'
trans = sh.worksheet('Transmission')
transmission = trans.get_all_values()
transmission = pd.DataFrame.from_records(transmission)
transmission.columns = list(transmission.iloc[0]) # Reassigning the first row as column names
transmission = transmission.drop(0)

# Get the ID string of the latest form response
latest = sh.worksheet('Looking up latest')
string = latest.get('F2') # ID string stored in F2 cell of sheet named 'Looking up latest'

# Based on inputs from the user, an ID string is generated for each user. 
# The input parameters are gender, city, age and whether they have diabetes and hypertension
# Each parameter value is coded with a digit
# eg: 1 for female and 2 for male
# eg ID string: 11100
gender, city, age, diabetes, hyper = list(string[0][0])

# --------------------------- Defining the App Layout -------------------------------- 

layout = dbc.Container([
    html.H1("Transmission", style={'text-align': 'center'}),
    dcc.Store(id='trans_store', storage_type='session'), # Used to store a value that can be used across pages. 
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
    dbc.Row([html.H2('Transmission'), dcc.Graph(id='trans')]),

    html.Div(id='trial')

])

# --------------------------- The Backend Processing for Calculating and Displaying Outputs -------------------------------- 

@app.callback(
    # Defining what to expect as output
    [Output(component_id = 'trans', component_property = 'figure'),
    Output(component_id = 'trans_store', component_property = 'data'),
    ],
    # Defining what to expect as input
    Input(component_id = 'city', component_property = 'value')
)
def update_graph(city_up):

    city_up = str(city_up) # the dataframe generated from the sheet stores all values as String

    # Get the transmission values for the selected city
    data = transmission[transmission['City_code'] == city_up]
    data = data.astype({'Transmission': float})

    # Generate a bar graph with the values for transmission
    fig = px.bar(data, x = 'Place', y = 'Transmission', orientation='v', color = 'Type', barmode = 'group', width = 1500, height = 500)
    trans = 10 # Ideally the bar graph will be interactive and the value corresponding to the bar chosen by the user will be used as the transmisson risk for caluculating overall risk

    # Return the bar graph and the value to be passed on to the page for calculating overall risk
    return (fig, trans/100)

if __name__ == '__main__':
    app.run_server(debug=True)