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

# --------------------------- Defining the App Layout -------------------------------- 

layout = dbc.Container([
    html.H1("Overall Risk", style={'text-align': 'center'}), # Heading

    # This defines the storage which is used for recovering the stored values from other pages
    # It retains the same id as the other storage spaces
    dcc.Store(id='risk_store', storage_type='session'),
    dcc.Store(id='health_store', storage_type='session'),
    dcc.Store(id='prev_store', storage_type='session'),
    dcc.Store(id='trans_store', storage_type='session'),

    # This page technically doesn't need the user to select their city of residence
    # But loading the page threw up errors which, for some unexplainable reason, was fixed when a dropdown box was added
    # It may have to do something about how having a dropdown box may induce an app callback
    dbc.Row([

        # Dropdown for selecing city
        html.H3('Select your City', style={'text-align': 'left'}),
        dbc.Col([dcc.Dropdown(id = 'city', options = [
            # Set the colour for each threshold range
            {'label': 'Delhi', 'value': 1},
            {'label': 'Chennai', 'value': 2}
        ],
        value = 1,
        persistence = True, persistence_type = 'memory', # So that the value selected by the user is retained even when the page is changed
        placeholder = 'Select your City'
        )

        ])

    ]),

    # Placeholders for graphs/figures
    html.Div(id='city_text'),
    dbc.Row([html.H2('Overall Risk'), dcc.Graph(id='overall')]),
    html.Div(id='overall_level')
    

])

# --------------------------- The Backend Processing for Calculating and Displaying Outputs -------------------------------- 

@app.callback(
    # Defining what to expect as output
    [Output(component_id = 'overall', component_property = 'figure'),
    Output(component_id = 'overall_level', component_property = 'children'),
    Output(component_id = 'city_text', component_property = 'children')],
    # Defining what to expect as input
    [Input(component_id = 'health_store', component_property = 'data'),
    Input(component_id = 'prev_store', component_property = 'data'),
    Input(component_id = 'trans_store', component_property = 'data'),
    Input(component_id = 'risk_store', component_property = 'data'),
    Input(component_id = 'city', component_property = 'value')]
)
def update_graph(health, prev, trans, risk, city):

    overall = int(health + prev + trans + risk) # Calculate the value of overall risk
    limit = 4

    fig = go.Figure()

    # Create a linear gauge to display the overall risk

    fig.add_trace(go.Indicator(
        mode = "gauge",
        value = overall + 0.5, # Add 0.5 to the value the pointer must be set to
            # This is so that the pointer is at the centre and not the edge of each coloured rectange in the linear gauge
            # The range of the linear gauge is broken into 4 equal parts: very low, low, high and very high
        delta = {'reference': limit},
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': 'Overall Risk'},
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

    level = int(overall)
    text = {0:'very low', 1:'low', 2:'high', 3:'very high'} # Assign text levels for each indicator value

    # Output the linear gauge, the text level and the placeholder text that's displayed alongside the linear gauge
    return (fig, text[level], city)

if __name__ == '__main__':
    app.run_server(debug=True)