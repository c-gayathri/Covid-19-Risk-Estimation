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

# Generating a dataframe from the sheet 'P_inf'
inf = sh.worksheet('P_inf')
p_inf = inf.get_all_values()
p_inf = pd.DataFrame.from_records(p_inf)
p_inf.columns = list(p_inf.iloc[0])
p_inf = p_inf.drop(0)
print(p_inf)
print()

# Generating a dataframe from the sheet 'P_adverse'
adv = sh.worksheet('P_adverse')
p_adv = adv.get_all_values()
p_adv = pd.DataFrame.from_records(p_adv)
p_adv.columns = list(p_adv.iloc[0])
p_adv = p_adv.drop(0)
print(p_adv)
print()

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

layout = html.Div([
    dcc.Store(id='risk_store', storage_type='session'), # Used to store a value that can be used across pages. 
    # This will store the final value due to prevalence risk and will beused to calculate the overall risk later

    dbc.Row(
        html.H1("Risk Profile", style={'text-align': 'center'})
    ),

    dbc.Row([
        # Dropdown for selecing gender
        dbc.Col([
            html.H3('Select your gender', style={'text-align': 'left'}),
            dcc.Dropdown(id = 'gender', 
            options = [
                {'label': 'Male', 'value': 2}, 
                {'label': 'Female', 'value': 1}
            ],
            value = gender, # By dafault, it displays the value chosen by the user when filling the form
            placeholder = 'Select your gender',
            persistence = True, persistence_type = 'memory' # So that the value selected by the user is retained even when the page is changed
            )],
            width={'size': 5, "offset": 1}
        ),

        # Dropdown for selecing age
        dbc.Col([
            html.H3('Select your age', style={'text-align': 'left'}),
            dcc.Dropdown(id = 'age', 
            options = [
                {'label': 'Less than 20 years', 'value': 1}, 
                {'label': '20 to 50 years', 'value': 2},
                {'label': 'Greater than 50 years', 'value': 3}
            ],
            value = age, # By dafault, it displays the value chosen by the user when filling the form
            persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
            placeholder = 'Select your age'
            )],
            width={'size': 5, "offset": 1}
        )
    ]),

    dbc.Row([
        # Dropdown for selecing city
        dbc.Col([
            html.H3('Select your City', style={'text-align': 'left'}),
            dcc.Dropdown(id = 'city', options = [
                {'label': 'Delhi', 'value': 1}, 
                {'label': 'Chennai', 'value': 2}
                ],
            value = city, # By dafault, it displays the value chosen by the user when filling the form
            persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
            placeholder = 'Select your City'
            )],
        width={'size': 5, "offset": 1}
        ),

        # Dropdown for selecing if they have diabetes
        dbc.Col([
            html.H3('Do you have diabetes?', style={'text-align': 'left'}),
            dcc.Dropdown(id = 'diabetes', options = [
                {'label': 'Have diabetes', 'value': 1}, 
                {'label': 'Don\'t have diabetes', 'value': 0}
                ],
            value = diabetes, # By dafault, it displays the value chosen by the user when filling the form
            persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
            placeholder = 'Do you have diabetes?'
            )],
        width={'size': 5, "offset": 1}
        )
        
    ]),

    dbc.Row([
        # Dropdown for selecing if they have hypertension
        
        dbc.Col([
            html.H3('Do you have hypertension?', style={'text-align': 'left'}),
            dcc.Dropdown(id = 'hyper', options = [
                {'label': 'Have hypertension', 'value': 1}, 
                {'label': 'Don\'t have hypertension', 'value': 0}
                ],
            value = hyper, # By dafault, it displays the value chosen by the user when filling the form
            persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
            placeholder = 'Do you have hypertension?'
            )],
        width={'size': 5, "offset": 1}
        )

    ]),

    html.H1("Household Member", style={'text-align': 'left'}),

    dbc.Row([
        # Dropdown for selecing gender
        html.H3('Select household member\'s gender', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(
            id = 'hh_gender', 
            options = [
                {'label': 'Male', 'value': 2}, 
                {'label': 'Female', 'value': 1}
            ],
            # The details of the household member was not encoded in a string
            # For the time being the details of the index person are used by default
            # This can however be manually changed using the dropdown boxes
            value = gender,
            persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
            placeholder = 'Select your gender'
        )
        
        ]),

        # Dropdown for selecing age
        html.H3('Select their age', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'hh_age', options = [
            {'label': 'Less than 20 years', 'value': 1}, 
            {'label': '20 to 50 years', 'value': 2},
            {'label': 'Greater than 50 years', 'value': 3}
        ],
        value = age,
        persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
        placeholder = 'Select your age'
        )

        ])
    ]),

    dbc.Row([
        # Dropdown for selecing if they have diabetes
        html.H3('Do they have diabetes?', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'hh_diabetes', options = [
            {'label': 'Have diabetes', 'value': 1}, 
            {'label': 'Don\'t have diabetes', 'value': 0}
        ],
        value = diabetes,
        persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
        placeholder = 'Do you have diabetes?'
        )

        ]),
        
        # Dropdown for selecing if they have hypertension
        html.H3('Do they have hypertension?', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'hh_hyper', options = [
            {'label': 'Have hypertension', 'value': 1}, 
            {'label': 'Don\'t have hypertension', 'value': 0}
        ],
        value = hyper,
        persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
        placeholder = 'Do you have hypertension?'
        )

        ])

    ]),

    dbc.Row([
        dbc.Col([
            html.H2('Personal Risk'),
            dcc.Graph(id='graph'), 
            html.Div(id='risk')
        ])
    ])

])

# --------------------------- The Backend Processing for Calculating and Displaying Outputs -------------------------------- 

@app.callback(
    # Defining what to expect as output
    [Output(component_id = 'graph', component_property = 'figure'),
    Output(component_id = 'risk', component_property = 'children'),
    Output(component_id = 'risk_store', component_property = 'data')],
    # Defining what to expect as input
    [Input(component_id = 'gender', component_property = 'value'), 
    Input(component_id = 'age', component_property = 'value'),
    Input(component_id = 'city', component_property = 'value'),
    Input(component_id = 'diabetes', component_property = 'value'),
    Input(component_id = 'hyper', component_property = 'value'),
    Input(component_id = 'hh_gender', component_property = 'value'), 
    Input(component_id = 'hh_age', component_property = 'value'),
    Input(component_id = 'hh_diabetes', component_property = 'value'),
    Input(component_id = 'hh_hyper', component_property = 'value')]
)
def update_graph(gender_up, age_up, city_up, diab_up, hyper_up, gender_hh, age_hh, diab_hh, hyper_hh):

    # the dataframe generated from the sheet stores all values as String
    gender_up = str(gender_up)
    age_up = str(age_up)
    city_up = str(city_up)
    diab_up = str(diab_up)
    hyper_up = str(hyper_up)

    gender_hh = str(gender_hh)
    age_hh = str(age_hh)
    diab_hh = str(diab_hh)
    hyper_hh = str(hyper_hh)

    # -------------------- Calculating the risk profile of index person ------------------------
    # Get probability of infection from DataFrame
    p_infection = float(p_inf[(p_inf['Gender'] == gender_up) & (p_inf['City_code'] == city_up)]['Prob']) 
    # Get probability of adverse effect from DataFrame
    hosp_death = p_adv[(p_adv['Age'] == age_up) & (p_adv['Diabetes'] == diab_up) & (p_adv['Hypertension'] == hyper_up)]
    p_adverse = float(hosp_death['Hosp']) + float(hosp_death['Death'])
    # Calculate risk profile by multiplying
    risk = p_infection*p_adverse*100

    # Calculate the probability of adverse affect for Household member
    SAR = 0.2
    hosp_death_hh = p_adv[(p_adv['Age'] == age_hh) & (p_adv['Diabetes'] == diab_hh) & (p_adv['Hypertension'] == hyper_hh)]
    p_adverse_hh = float(hosp_death_hh['Hosp']) + float(hosp_death_hh['Death'])
    # Update the risk profile by adding the risk faced byt eh household member
    # The risk of the household member is  aproduct of prob. of infection, prob. of adverse affect and SAR
    risk += p_infection*SAR*p_adverse_hh*100

    # Get the names of all indicators or 'fields'
    f = 'Risk Profile' # Here, there is only one indicator
    limit = 15 # Define the upper limit of this indicator. 
    # This is not a theoretical limit and is a choice based on observed values
    
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "gauge",
        value = risk,
        delta = {'reference': limit},
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [None, limit]},
            'steps': [
                # Set the colour for each threshold range
                {'range': [0, limit/4], 'color': '#fbc4ab'},
                {'range': [limit/4, limit/2], 'color': '#f8ad9d'},
                {'range': [limit/2, limit*3/4], 'color': '#f4978e'},
                {'range': [limit*3/4, limit], 'color': '#f08080'}],
            'bar': {'color': '#FFFFFF'}})) # Set the clour of the horizontal pointer bar to white

    fig.update_layout(height = 80, margin = {'t':0, 'b':0, 'l':0})

    level = int(risk*4/limit)
    text = {0:'very low', 1:'low', 2:'high', 3:'very high'} # Assign text levels for each indicator value

    # output the linear gauge figure, the text level and the normalised value of the indicator
    # This will be used in a different page to calculate the overall risk
    return (fig, text[level], risk/limit) 

if __name__ == '__main__':
    app.run_server(debug=True)