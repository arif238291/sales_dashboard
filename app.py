import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

# Load and clean data
df = pd.read_csv("sales_data.csv")
df['Category'] = df['Category'].astype(str).str.strip().str.title()
df['Region'] = df['Region'].astype(str).str.strip().str.title()
df['Date'] = pd.to_datetime(df['Date'])

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
app.title = "Professional Sales Dashboard"

# Layout
app.layout = dbc.Container([
    html.H1("Sales Dashboard", className="text-center text-primary my-4 fw-bold display-5"),

    # Stylish Filter Bar
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Select Category", className="fw-semibold text-primary"),
                    dcc.Dropdown(
                        id='category-filter',
                        options=[{'label': c, 'value': c} for c in sorted(df['Category'].unique())],
                        value=sorted(df['Category'].unique())[0],
                        clearable=False
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Select Region", className="fw-semibold text-primary"),
                    dcc.Dropdown(id='region-filter', clearable=False)
                ], width=4),
                dbc.Col([
                    html.Label("Select Date Range", className="fw-semibold text-primary"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=df['Date'].min(),
                        end_date=df['Date'].max(),
                        display_format='YYYY-MM-DD'
                    )
                ], width=4),
            ])
        ])
    ], className="mb-4 shadow-sm border border-light bg-light"),

    # Tabs
    dbc.Tabs(id="tabs", active_tab="dashboard", children=[
        dbc.Tab(label="Dashboard", tab_id="dashboard", labelClassName="fw-bold text-dark"),
        dbc.Tab(label="Data Table", tab_id="table", labelClassName="fw-bold text-dark"),
    ], className="mb-4 border-light bg-white rounded"),

    html.Div(id="tabs-content")
], fluid=True)

# Tab contents
def dashboard_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="total-demand", className="card-title text-success fw-bold display-6"),
                html.P("Total Demand", className="text-muted")
            ])], color="light"), width=3),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="avg-price", className="card-title text-warning fw-bold display-6"),
                html.P("Average Price", className="text-muted")
            ])], color="light"), width=3),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="most-sold-cat", className="card-title text-info fw-bold display-6"),
                html.P("Most Sold Category", className="text-muted")
            ])], color="light"), width=6),
        ], className="mb-4"),

        dcc.Graph(id='filtered-demand'),
        dcc.Graph(id='avg-price-region')
    ])

def table_tab():
    return html.Div([
        html.H5("Filtered Data Table", className="text-primary mb-3 fw-bold"),
        dash_table.DataTable(
            id='data-table',
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'backgroundColor': '#f8f9fa', 'color': '#212529'},
            style_header={
                'backgroundColor': '#e9ecef',
                'fontWeight': 'bold',
                'color': '#212529'
            }
        ),
        html.Div([
            html.Button("Download CSV", id="btn-download-table", className="btn btn-outline-primary mt-3"),
            dcc.Download(id="download-data-table")
        ])
    ], className="bg-white p-4 rounded border")

@app.callback(Output('tabs-content', 'children'), Input('tabs', 'active_tab'))
def render_tab(tab):
    if tab == "dashboard":
        return dashboard_tab()
    elif tab == "table":
        return table_tab()

@app.callback(
    Output('region-filter', 'options'),
    Output('region-filter', 'value'),
    Input('category-filter', 'value')
)
def update_region_dropdown(selected_category):
    filtered = df[df['Category'] == selected_category]
    regions = sorted(filtered['Region'].dropna().unique())
    if not regions:
        return [], None
    return [{'label': r, 'value': r} for r in regions], regions[0]

@app.callback(
    Output('filtered-demand', 'figure'),
    Output('avg-price-region', 'figure'),
    Output('total-demand', 'children'),
    Output('avg-price', 'children'),
    Output('most-sold-cat', 'children'),
    Input('category-filter', 'value'),
    Input('region-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_dashboard(category, region, start_date, end_date):
    filtered_df = df[(df['Category'] == category) &
                     (df['Region'] == region) &
                     (df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if filtered_df.empty:
        return (px.line(title="No Data"), px.bar(title="No Data"), "0", "$0", "N/A")

    daily = filtered_df.groupby('Date')['Demand'].sum().reset_index()
    fig1 = px.line(daily, x='Date', y='Demand', title=f"Demand Over Time")

    price_summary = filtered_df.groupby('Product ID')['Price'].mean().reset_index()
    fig2 = px.bar(price_summary, x='Product ID', y='Price', title=f"Average Product Price")

    total_demand = int(filtered_df['Demand'].sum())
    avg_price = round(filtered_df['Price'].mean(), 2)
    most_cat = filtered_df['Category'].value_counts().idxmax()

    return fig1, fig2, str(total_demand), f"${avg_price}", most_cat

@app.callback(
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('tabs', 'active_tab'),
    Input('category-filter', 'value'),
    Input('region-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_table(tab, category, region, start_date, end_date):
    if tab != 'table':
        return [], []
    filtered_df = df[(df['Category'] == category) &
                     (df['Region'] == region) &
                     (df['Date'] >= start_date) & (df['Date'] <= end_date)]
    return filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns]

@app.callback(
    Output("download-data-table", "data"),
    Input("btn-download-table", "n_clicks"),
    State('category-filter', 'value'),
    State('region-filter', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    prevent_initial_call=True
)
def download_table_csv(n, category, region, start_date, end_date):
    filtered_df = df[(df['Category'] == category) &
                     (df['Region'] == region) &
                     (df['Date'] >= start_date) & (df['Date'] <= end_date)]
    return dcc.send_data_frame(filtered_df.to_csv, filename="filtered_table_data.csv", index=False)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)
