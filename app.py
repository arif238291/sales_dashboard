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

    # Filter bar
    dbc.Card([
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Label("Select Store ID", className="fw-semibold text-primary"),
                dcc.Dropdown(
                    id='store-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': s, 'value': s} for s in sorted(df['Store ID'].unique())],
                    value='All',
                    clearable=False
                )
            ], width=4),
            dbc.Col([
                html.Label("Select Product ID", className="fw-semibold text-primary"),
                dcc.Dropdown(
                    id='product-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': p, 'value': p} for p in sorted(df['Product ID'].unique())],
                    value='All',
                    clearable=False
                )
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

# Dashboard Tab
def dashboard_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="total-demand", className="card-title text-success fw-bold display-6"),
                html.P("Total Units Demand", className="text-muted")
            ])], color="light"), width=2),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="total-orders", className="card-title text-secondary fw-bold display-6"),
                html.P("Total Units Order", className="text-muted")
            ])], color="light"), width=2),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="total-units", className="card-title text-primary fw-bold display-6"),
                html.P("Total Units Sold ", className="text-muted")
            ])], color="light"), width=2),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="total-revenue", className="card-title text-danger fw-bold display-6"),
                html.P("Total Revenue", className="text-muted")
            ])], color="light"), width=2),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="avg-price", className="card-title text-warning fw-bold display-6"),
                html.P("Average Price per Unit", className="text-muted")
            ])], color="light"), width=2),
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(id="most-sold-cat", className="card-title text-info fw-bold display-6"),
                html.P("Most Sold Category", className="text-muted")
            ])], color="light"), width=3),
        ], className="mb-4"),

        html.Div([
            html.Label("Sales Grouped by", className="fw-semibold text-primary"),
            dcc.Dropdown(
                id='grouping-dropdown',
                options=[
                    {'label': 'Category', 'value': 'Category'},
                    {'label': 'Region', 'value': 'Region'}
                ],
                value='Category',
                clearable=False,
                className="mb-3"
            ),
            dcc.Graph(id='units-sold-line-chart'),
            dcc.Graph(id='units-sold-bar-chart')
        ])
    ])



# Table Tab
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

# Tab switch callback
@app.callback(Output('tabs-content', 'children'), Input('tabs', 'active_tab'))
def render_tab(tab):
    if tab == "dashboard":
        return dashboard_tab()
    elif tab == "table":
        return table_tab()

# Update region dropdown based on selected category
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

# KPI callback
@app.callback(
    Output('total-demand', 'children'),
    Output('avg-price', 'children'),
    Output('most-sold-cat', 'children'),
    Output('total-units', 'children'),
    Output('total-revenue', 'children'),
    Output('total-orders', 'children'),
    Input('store-filter', 'value'),
    Input('product-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_dashboard(store, product, start_date, end_date):
    filtered_df = df.copy()
    if store != 'All':
        filtered_df = filtered_df[filtered_df['Store ID'] == store]
    if product != 'All':
        filtered_df = filtered_df[filtered_df['Product ID'] == product]
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

    if filtered_df.empty:
        return "0", "$0", "N/A", "0", "$0", "0"

    total_demand = int(filtered_df['Demand'].sum())
    avg_price = round(filtered_df['Price'].mean(), 2)
    most_cat = filtered_df['Category'].value_counts().idxmax()
    total_units = int(filtered_df['Units Sold'].sum())
    total_revenue = round((filtered_df['Units Sold'] * filtered_df['Price']).sum(), 2)
    total_orders = int(filtered_df['Units Ordered'].sum())

    return str(total_demand), f"${avg_price}", most_cat, str(total_units), f"${total_revenue}", str(total_orders)


# Line chart callback
@app.callback(
    Output('units-sold-line-chart', 'figure'),
    Output('units-sold-bar-chart', 'figure'),
    Input('grouping-dropdown', 'value'),
    Input('store-filter', 'value'),
    Input('product-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_charts(group_col, store, product, start_date, end_date):
    filtered_df = df.copy()
    if store != 'All':
        filtered_df = filtered_df[filtered_df['Store ID'] == store]
    if product != 'All':
        filtered_df = filtered_df[filtered_df['Product ID'] == product]
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

    if filtered_df.empty:
        return px.line(title="No Data"), px.bar(title="No Data")

    # Line chart: Units Sold over time
    line_data = filtered_df.groupby(['Date', group_col])['Units Sold'].sum().reset_index()
    line_fig = px.line(line_data, x='Date', y='Units Sold', color=group_col,
                       title=f"Units Sold Over Time by {group_col}")
    line_fig.update_layout(legend_title=group_col, height=450)

    # Bar chart: Total Units Sold by group
    bar_data = filtered_df.groupby(group_col)['Units Sold'].sum().reset_index()
    bar_fig = px.bar(bar_data, x=group_col, y='Units Sold', color=group_col,
                     title=f"Total Units Sold by {group_col}")
    bar_fig.update_layout(xaxis_title=group_col, yaxis_title="Units Sold", height=400)

    return line_fig, bar_fig



# Table update callback
@app.callback(
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('tabs', 'active_tab'),
    Input('store-filter', 'value'),
    Input('product-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_table(tab, store, product, start_date, end_date):
    if tab != 'table':
        return [], []

    filtered_df = df.copy()
    if store != 'All':
        filtered_df = filtered_df[filtered_df['Store ID'] == store]
    if product != 'All':
        filtered_df = filtered_df[filtered_df['Product ID'] == product]
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

    return filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns]


# Download table
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

if __name__ == '__main__':
    app.run(debug=True)
