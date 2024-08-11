import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from pages import riskProfile, healthSystem, prevalence, transmission, overall
#from pages import riskProfile, healthSystem, prevalence

import pip

#define a function for installing packages
def install(package):
    if hasattr(pip, 'main'):
        pip.main(['install', package])
    else:
        pip._internal.main(['install', package])


# define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link('Risk Profile |', href='/pages/riskProfile'),
        dcc.Link(' Health System |', href='/pages/healthSystem'),
        dcc.Link(' Prevalence |', href='/pages/prevalence'),
        dcc.Link(' Transmission |', href='/pages/transmission'),
        dcc.Link(' Overall', href='/pages/overall')
    ], className="row"),
    html.Div(id='page-content', children=[])
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/pages/riskProfile':
        return riskProfile.layout
    if pathname == '/pages/healthSystem':
        return healthSystem.layout
    if pathname == '/pages/prevalence':
        return prevalence.layout
    if pathname == '/pages/transmission':
        return transmission.layout
    if pathname == '/pages/overall':
        return overall.layout
    else:
        return riskProfile.layout

if __name__ == '__main__':
    # install all the packages
    install('pandas')
    install('numpy')
    install('dash')
    install('gspread')
    install('plotly')

    # run the app
    app.run_server(debug=True)
