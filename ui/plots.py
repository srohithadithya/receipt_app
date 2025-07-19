import plotly.express as px
import pandas as pd
import logging
from typing import Optional, List # Added List here

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str,
                   color_col: Optional[str] = None, hover_data: Optional[List[str]] = None):
    """
    Generates an interactive bar chart using Plotly Express.

    :param df: Pandas DataFrame containing the data.
    :param x_col: Column name for the x-axis.
    :param y_col: Column name for the y-axis.
    :param title: Title of the chart.
    :param color_col: Optional column to color bars by.
    :param hover_data: Optional list of columns to show on hover.
    :return: A Plotly figure object.
    """
    if df.empty:
        logger.warning(f"Empty DataFrame provided for bar chart '{title}'.")
        return px.bar(title=title + " (No Data)")

    fig = px.bar(df, x=x_col, y=y_col, title=title, color=color_col, hover_data=hover_data,
                 template="plotly_white") # "plotly_dark", "ggplot2", "seaborn" etc.
    fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(),
                      yaxis_title=y_col.replace('_', ' ').title(),
                      title_x=0.5) # Center title
    logger.info(f"Generated bar chart: {title}")
    return fig

def plot_pie_chart(df: pd.DataFrame, names_col: str, values_col: str, title: str,
                   hole: float = 0.4, hover_data: Optional[List[str]] = None):
    """
    Generates an interactive pie/donut chart using Plotly Express.

    :param df: Pandas DataFrame containing the data.
    :param names_col: Column name for the slice labels (categories).
    :param values_col: Column name for the slice sizes (values).
    :param title: Title of the chart.
    :param hole: Size of the hole in the donut chart (0 to 1). Set to 0 for a full pie chart.
    :param hover_data: Optional list of columns to show on hover.
    :return: A Plotly figure object.
    """
    if df.empty:
        logger.warning(f"Empty DataFrame provided for pie chart '{title}'.")
        return px.pie(title=title + " (No Data)")

    fig = px.pie(df, names=names_col, values=values_col, title=title, hole=hole, hover_data=hover_data,
                 template="plotly_white")
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_x=0.5, uniformtext_minsize=10, uniformtext_mode='hide')
    logger.info(f"Generated pie chart: {title}")
    return fig

def plot_line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str,
                    color_col: Optional[str] = None, hover_data: Optional[List[str]] = None,
                    y_secondary_col: Optional[str] = None):
    """
    Generates an interactive line chart using Plotly Express, with optional secondary Y-axis.

    :param df: Pandas DataFrame containing the data.
    :param x_col: Column name for the x-axis (usually time-related).
    :param y_col: Column name for the primary y-axis.
    :param title: Title of the chart.
    :param color_col: Optional column to color lines by (if multiple series).
    :param hover_data: Optional list of columns to show on hover.
    :param y_secondary_col: Optional column for a secondary Y-axis (e.g., rolling average).
    :return: A Plotly figure object.
    """
    if df.empty:
        logger.warning(f"Empty DataFrame provided for line chart '{title}'.")
        return px.line(title=title + " (No Data)")

    fig = px.line(df, x=x_col, y=y_col, title=title, color=color_col, hover_data=hover_data,
                  template="plotly_white")

    if y_secondary_col and y_secondary_col in df.columns:
        fig.add_trace(px.line(df, x=x_col, y=y_secondary_col).data[0], secondary_y=True)
        fig.update_layout(yaxis2=dict(title=y_secondary_col.replace('_', ' ').title(), overlaying='y', side='right'))

    fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(),
                      yaxis_title=y_col.replace('_', ' ').title(),
                      title_x=0.5)
    fig.update_xaxes(tickangle=45) # Rotate x-axis labels for readability if dates

    logger.info(f"Generated line chart: {title}")
    return fig

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    import streamlit as st_temp # Use a temp name to avoid conflict with actual st in app.py

    # Dummy data for demonstration
    data_bar = {'Category': ['Groceries', 'Utilities', 'Dining', 'Shopping'],
                'Spend': [500, 250, 150, 300]}
    df_bar = pd.DataFrame(data_bar)

    data_pie = {'Vendor': ['Walmart', 'Target', 'Amazon', 'Cafe'],
                'Sales': [400, 200, 150, 50]}
    df_pie = pd.DataFrame(data_pie)

    data_line = {'Month': pd.to_datetime(['2023-01', '2023-02', '2023-03', '2023-04', '2023-05']),
                 'Spend': [1000, 1200, 900, 1500, 1300],
                 'Rolling_Avg': [1000, 1100, 1033, 1200, 1166]}
    df_line = pd.DataFrame(data_line)


    st_temp.header("Plotly Chart Examples")

    st_temp.subheader("Bar Chart: Category Spend")
    fig_bar = plot_bar_chart(df_bar, 'Category', 'Spend', 'Spending by Category')
    st_temp.plotly_chart(fig_bar, use_container_width=True)

    st_temp.subheader("Pie Chart: Vendor Sales Distribution")
    fig_pie = plot_pie_chart(df_pie, 'Vendor', 'Sales', 'Sales Distribution by Vendor')
    st_temp.plotly_chart(fig_pie, use_container_width=True)

    st_temp.subheader("Line Chart: Monthly Spend Trend (with Rolling Average)")
    fig_line = plot_line_chart(df_line, 'Month', 'Spend', 'Monthly Spend Trend', y_secondary_col='Rolling_Avg')
    st_temp.plotly_chart(fig_line, use_container_width=True)

    st_temp.subheader("Empty Data Chart Example")
    fig_empty = plot_bar_chart(pd.DataFrame(), 'X', 'Y', 'No Data Example')
    st_temp.plotly_chart(fig_empty, use_container_width=True)