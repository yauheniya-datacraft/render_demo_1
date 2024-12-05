# Plotly and Dash 3: Callbacks mit mehreren Inputs, Outputs, State

# Modulimporte
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback
import plotly.express as px
#import warnings
#warnings.filterwarnings("ignore", category=DeprecationWarning)


# Daten vorbereiten
gapminder = px.data.gapminder()
gapminder = gapminder.rename(columns={'pop':'Bevölkerung','lifeExp':'Lebenserwartung'})
gapminder['Bruttoinlandsprodukt'] = gapminder['Bevölkerung']*gapminder['gdpPercap']  # BIP
 
print(gapminder.head(2))

df = gapminder[gapminder['year']==2007]

# App-Komponenten definieren
fig_map = px.choropleth(df, locations='iso_alpha', color='Bruttoinlandsprodukt',
                        title='Bruttoinlandsprodukt in 2007', template='plotly_dark')
fig_map.update_layout(title_x=0.5, width=650)
#fig_map.show()

# App erstellen
app = Dash(__name__, title='Gapminder')

# App-Layout zusammensetzen
app.layout = html.Div(children=[
    html.Div(children=[
        html.H1(children='GAPMINDER'),
        html.Br(),
        html.Hr(),
        html.H2(children="Callback-Funktion mit zwei Outputs"),
        html.P(children="Klicke auf ein Land für Statistiken und Zoom-in"),
        dcc.Graph(id='map1-input', figure=fig_map), # Weltkarte
        html.Div(id='statistik-output'), # Statistik
        dcc.Graph(id='map2-output'), # Zoom-in Karte
        html.Br(),
        html.Hr(),
        html.H2(children="Callback-Funktion mit zwei Inputs"),
        html.P(children="Wähle Kennzahlen und Land für die Zeitreihe aus"),
        dcc.Checklist(id='checkliste-input', options=['Lebenserwartung', 'Bevölkerung','Bruttoinlandsprodukt'],
                      value=['Bruttoinlandsprodukt'], inline=True),
        html.Br(),
        dcc.Dropdown(id='dropdown-input', 
                     options=[{'label':land, 'value':land} for land in gapminder['country'].unique()],
                     value='Germany', style={'width':'50%'}),
        html.Br(),
        dcc.Graph(id='zeitreihe-output'),
        html.Br(),
        html.Hr(),
        html.H2(children="Callback-Funktion mit State und zwei Outputs"),
        html.P(children="Gebe den Import-Befehl für den Gapminder-Datensatz beginneng mit `px.`"),
        dcc.Input(id='import-befehl', value='', type='text'),
        html.Button(children='Daten laden', id='submit-button', n_clicks=0),
        html.Br(),
        html.Br(),
        html.Div(id='output-message'), # Output 1
        html.Br(),
        dash_table.DataTable(id='output-table', page_size=5, style_table={'overflowX':'auto'}), # Output 2
        html.Br(),
        html.Br()
    ], style={'backgroundColor':'white',
              'width':'100%',
              'maxWidth':'800px',
              'text-align':'center',
              'padding':'20px'})
], style={'backgroundColor':'gray',
              'width':'100%',
              'min-height':'100vh',
              'display':'flex',
              'justify-content':'center',
              'padding':'0',
              'margin':'0'}
)

# Callbacks
@callback(
    Output(component_id='statistik-output', component_property='children'),
    Output(component_id='map2-output', component_property='figure'),
    Input(component_id='map1-input', component_property='clickData')
)
def zeige_statistik_zoomin(clickData):
    if clickData is None:
        country_iso ='DEU'
    else:
        country_iso = clickData['points'][0]['location']
    
    dff = df[df['iso_alpha']==country_iso]
    statistik = [
        html.P(f"Land: {dff['country'].iloc[0]}", style={'font-weight':'bold'}),
        html.P(f"ISO-3: {dff['iso_alpha'].iloc[0]}"),
        html.P(f"BIP: ${dff['Bruttoinlandsprodukt'].iloc[0]:,.0f}"),
        html.P(f"Lebenserwartung: {dff['Lebenserwartung'].iloc[0]:.0f} Jahre"),
        html.P(f"Bevölkerung: {dff['Bevölkerung'].iloc[0]:,.0f}")
    ]
    fig_country_map = px.choropleth(dff, locations='iso_alpha', template='plotly_dark')
    fig_country_map.update_geos(fitbounds='locations') # Zoom-in
    fig_country_map.data[0].showlegend=False
    #df -> Ausschnitt von Gapminder für 2007
    #ddf -> Ausschnitt von df für ein Land

    return  statistik, fig_country_map


@callback(
    Output(component_id='zeitreihe-output', component_property='figure'),
    Input(component_id='checkliste-input', component_property='value'), # children
    Input(component_id='dropdown-input', component_property='value') 
)
def erstelle_zeitreihe(kennzahl, land): # BIP + Lebenserwartung
    # df -> 2007, dff -> 1 Land in 2007, gapminder -> alle Jahre alle Länder
    dff = gapminder[gapminder['country']==land].copy()
    earliest_year = dff['year'].min() # 1952
    dff['Bevölkerung'] = dff['Bevölkerung']/dff.loc[dff['year']==earliest_year, 'Bevölkerung'].values[0]
    dff['Lebenserwartung'] = dff['Lebenserwartung']/dff.loc[dff['year']==earliest_year, 'Lebenserwartung'].values[0]
    dff['Bruttoinlandsprodukt'] = dff['Bruttoinlandsprodukt']/dff.loc[dff['year']==earliest_year, 'Bruttoinlandsprodukt'].values[0]
    fig_line = px.line(dff, x='year', y=kennzahl, template='plotly_dark',
                       labels={'variable':'Kennzahl'})
    fig_line.update_layout(xaxis_title='', yaxis_title=f"Relative Veränderung im Vergleich zum {earliest_year}")
    return fig_line


@callback(
    Output(component_id='output-message', component_property='children'), #hmtl.Div
    Output(component_id='output-table', component_property='data'), #dash_table
    Input(component_id='submit-button', component_property='n_clicks'),#dcc.Input
    State(component_id='import-befehl', component_property='value')
)

def erstelle_tabelle(n_clicks,import_befehl):
    if n_clicks==0:
        return "", []
    elif import_befehl =='px.data.gapminder()':
        data_preview = gapminder.to_dict('records')
        return "Erfolg!", data_preview
    return "Falscher Befehl, versuche es erneut!", []


# Die if __name__ == "__main__": Abfrage 
if __name__ == "__main__":
    app.run(debug=True)
