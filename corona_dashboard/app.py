import json
from urllib.request import urlopen
import plotly.express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np

app = dash.Dash(__name__)

hotspot_labels = {1: 'Low', 2: 'Medium', 3: 'Medium-High', 4: 'High', 5: 'Very High'}

def get_county_data() -> (pd.DataFrame, dict):
    us_counties = pd.read_csv('nyt_data/us-counties.csv', dtype={"fips": str})
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as res:
        fips_metadata = json.load(res)

    us_counties['location'] = us_counties[['county', 'state']].apply(
        lambda x: ', '.join(x), axis=1)
    us_counties['pct_change'] = us_counties.groupby('location')['cases'].pct_change(
        periods=5).replace([np.inf, -np.inf], np.nan).dropna()
    final_list = us_counties.sort_values('pct_change', ascending=False)[
        'location'].unique()

    def rank_by_buckets(row) -> int:
        if row.location in final_list[:18]:
            return 5
        if row.location in final_list[18:72]:
            return 4
        if row.location in final_list[72:216]:
            return 3
        if row.location in final_list[216:720]:
            return 2
        return 1

    us_counties['hotspot_risk'] = us_counties.apply(rank_by_buckets, axis=1)

    return us_counties, fips_metadata


US_COUNTIES, FIPS_METADATA = get_county_data()

MAP = px.choropleth_mapbox(
    US_COUNTIES, geojson=FIPS_METADATA, locations='fips', color='hotspot_risk',
    color_continuous_scale='orrd', range_color=(0, 5),
    hover_data=['location'],
    mapbox_style='carto-darkmatter', zoom=3.2, opacity=0.5,
    center={'lat': 39, 'lon': -96},
    labels={'hotspot_risk': 'hotspot risk'}
    )
MAP.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

app.layout = html.Div(
    [html.Div([
        dcc.Graph(
            id="map", figure=MAP,
            className="map"),
        dcc.Graph(id="line", className="cases")
        ])
    ])


@app.callback(Output('line', 'figure'), [Input('map', 'clickData')])
def display_county_graph(clickData: dict) -> px.line:
    if not clickData:
        clicked_county = US_COUNTIES[US_COUNTIES.fips == '51013']
    else:
        clicked_county = US_COUNTIES[US_COUNTIES.fips ==
                                     clickData['points'][0]['location']]
    county_name = clicked_county['location'].iloc[0]
    hotspot_risk = clicked_county['hotspot_risk'].iloc[0]
    fig = px.line(clicked_county, x='date', y='cases', title=f"{county_name} (Hotspot Risk: {hotspot_labels[hotspot_risk]})")
    fig.update_layout(margin=dict(l=0, r=0, t=32, b=0))
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
# def main():
#     app.title = 'Coronavirus Dashboard'
#     app.run_server(debug=True)
