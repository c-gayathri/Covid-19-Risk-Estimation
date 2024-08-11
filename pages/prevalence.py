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

# Generating a dataframe from the sheet 'Prevalence'
prev = sh.worksheet('Prevalence')
prev = prev.get_all_values()
prev = pd.DataFrame.from_records(prev)
prev.columns = list(prev.iloc[0]) # Reassigning the first row as column names
prev = prev.drop(0)

# Generating a dataframe from the sheet 'Prevalence_Live'
live = sh.worksheet('Prevalence_Live')
live = live.get_all_values()
live = pd.DataFrame.from_records(live)
dropping = list(range(10))
dropping.extend([16,17,18])
# Drop the columns that don't correspond to active case number and growth rate
live = live.drop(dropping, axis = 1) 
live = live.drop(0)
live.columns = list(live.iloc[0]) # Use the first row as column names
live = live.drop(1)
live.reset_index(drop=True, inplace=True) # Reset indices

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
    html.H1("Prevalence", style={'text-align': 'center'}),
    dcc.Store(id='prev_store', storage_type='session'), # Used to store a value that can be used across pages. 
    # This will store the final value due to prevalence risk and will beused to calculate the overall risk later

    dbc.Row([

        # Dropdown for selecing city
        html.H3('Select your City', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'city', options = [
            {'label': 'Delhi', 'value': 1}, 
            {'label': 'Chennai', 'value': 2}
        ],
        value = city, # By dafault, it displays the value chosen by the user when filling the form
        placeholder = 'Select your City',
        persistence = True, persistence_type = 'memory' # So that the value selected by the user is retained even when the page is changed
        )

        ])

    ]),

    # Placeholders for graphs/figures
    dbc.Row([html.H2('Active cases'), html.Div(id = 'case_count'), dcc.Graph(id='cases_fig'), html.Div(id='cases_level')]),
    dbc.Row([html.H2('Growth rate of new cases'), html.Div(id = 'growth_rate'), dcc.Graph(id='growth_fig'), html.Div(id='growth_level')]),
    dbc.Row([html.H2('Prevalence (Cumulative)'), dcc.Graph(id='prevalence_fig'), html.Div(id='prevalence_level')])

])

# --------------------------- The Backend Processing for Calculating and Displaying Outputs -------------------------------- 

@app.callback(
    # Defining what to expect as output
    [Output(component_id = 'cases_fig', component_property = 'figure'), Output(component_id = 'cases_level', component_property = 'children'), 
    Output(component_id = 'growth_fig', component_property = 'figure'), Output(component_id = 'growth_level', component_property = 'children'),
    Output(component_id = 'prevalence_fig', component_property = 'figure'), Output(component_id = 'prevalence_level', component_property = 'children'),
    Output(component_id = 'prev_store', component_property = 'data'),
    Output(component_id = 'case_count', component_property = 'value'),
    Output(component_id = 'growth_rate', component_property = 'value')
    ],
    # Defining what to expect as input
    Input(component_id = 'city', component_property = 'value')
)
def update_graph(city_up):

    city_up = str(city_up) # the dataframe generated from the sheet stores all values as String

    fields = ['Active cases', 'Growth rate of new cases', 'Prevalence']
    values = pd.DataFrame({fields[0]: [0,4,0.0], fields[1]: [0,4,0.0], fields[2]: [0,4,0.0]})
    # Created a dataframe where each column is for one indicator
    # The first row (index 0) will store the value the linear gauge uses to set the pointer (here it takes discrete values and has 4 levels)
    # The second row (index 1) stores the upper limit this can obtain.
    # The third row (index 2) stores the original value of the indicator. This can be continuous and can thoretically take inifinite values

    # -------------------- Calculating the Prevalence ------------------------
    # Getting information about the number of active cases and growth rate from data frames

    active_col = live['active_'+city_up] # Get the column with number of active cases on all days
    growth_col = live['growth_'+city_up] # Get the column with growth rate on all days
    # The live data is not always up to date and some of the latest values might be missing and display an error
    # Get the value of the first cell that doesn't display the error messge 'NA'
    active_col = active_col[active_col.apply(lambda x: x != 'NA')] 
    growth_col = growth_col[growth_col.apply(lambda x: x != 'NA')]
    active_col.reset_index(drop=True, inplace=True)
    growth_col.reset_index(drop=True, inplace=True)
    # Get the latest value that is present in the first row of the newly constructed dataframe
    active = float(active_col.iloc[0])
    growth = float(growth_col.iloc[0])

    # Original value of the indicator stored in the third row (index 2) - see above
    values.iloc[2][fields[0]] = active 
    values.iloc[2][fields[1]] = growth

    # Create a list of the integer quotients when number of beds is divided by the threshold values 500, 1000, 1500 (number of cases)
    # The four levels are defined as
    # < 500
    # between 500 and 1000
    # between 1000 and 1500
    # > 1500
    active_quotients = [int(active/d) for d in [500,1000,1500]]
    # Find the position of last non-zero quotient in the list.
    # This will be two less than the level mentioned in 'Indicators estimation.xlsx', that is, if the levels were 1,2,3,4
    active_nonzero = np.nonzero(active_quotients)[0]
    if len(active_nonzero) == 0:
        active_level = 1
    else:
        active_level = active_nonzero[-1] + 2

    # Use the similar method from above for getting the equivalent level
    growth_quotients = [int(growth/d) for d in [1,5]]
    growth_nonzero = np.nonzero(growth_quotients)[0]
    if growth < 0:
        growth_level = 1
    elif len(growth_nonzero) == 0:
        growth_level = 2
    else:
        growth_level = growth_nonzero[-1] + 3

    # Create a lookup table for getting the prevalence level from the level of active cases and growth rate
    # This table was based on the values given in the sheet 'Estimates' in 'Indicators estimation.xlsx'
    prev_lookup = np.array([[1,2,2,3],[2,2,3,3],[2,3,3,4],[3,3,4,4]])
    prevalence = prev_lookup[active_level - 1][growth_level - 1] # The indices are numbered from 0 and not 1

    # Update the values the linear gauge must be set to
    values.iloc[0][fields[0]] = active_level
    values.iloc[0][fields[1]] = growth_level
    values.iloc[0][fields[2]] = prevalence

    outputs = [] # The outputs will be stored here

    reds = ['#fbc4ab', '#f8ad9d', '#f4978e', '#f08080'] # The colour hexcodes for the red linear gauge
    violets = ['#c77dff', '#9d4edd', '#5a189a', '#240046'] # The colour hexcodes for the purple linear gauge
    colours = {fields[0]: reds, fields[1]: reds, fields[2]: violets} # Allot the colours for each indicator

    # Loop through all sub-indicators to create a linear gauge for each indicator and store this in the list 'outputs'
    for f in fields:

        fig = go.Figure()

        palette = colours[f]

        limit = values.iloc[1][f] # Get the upper limit for this indicator
        value = values.iloc[0][f] # Get the value the linear gauge must be set to for this indicator

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
            outputs.extend([fig, text[value - 1]]) # This is the normalised value of the indicator that will passed on to the page for calculating overall risk

    outputs.append(prevalence/4)
    outputs.extend([active, growth])

    return outputs

if __name__ == '__main__':
    app.run_server(debug=True)