import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str,
                   color_col: Optional[str] = None, hover_data: Optional[List[str]] = None):
    if df.empty:
        logger.warning(f"Empty DataFrame provided for bar chart '{title}'.")
        return px.bar(title=title + " (No Data)")

    fig = px.bar(df, x=x_col, y=y_col, title=title, color=color_col, hover_data=hover_data,
                 template="plotly_white")
    fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(),
                      yaxis_title=y_col.replace('_', ' ').title(),
                      title_x=0.5)
    logger.info(f"Generated bar chart: {title}")
    return fig

def plot_pie_chart(df: pd.DataFrame, names_col: str, values_col: str, title: str,
                   hole: float = 0.4, hover_data: Optional[List[str]] = None):
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
    if df.empty:
        logger.warning(f"Empty DataFrame provided for line chart '{title}'.")
        return px.line(title=title + " (No Data)")

    if y_secondary_col and y_secondary_col in df.columns:
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add primary y-axis trace (total_amount)
        # Fix: Double curly braces for literal braces in f-string
        fig.add_trace(
            go.Scatter(x=df[x_col], y=df[y_col], name=y_col.replace('_', ' ').title(), mode='lines+markers',
                       hovertemplate='<b>%{x}</b><br>' + f'{y_col.replace("_", " ").title()}: %{{y}}:.2f<extra></extra>'),
            secondary_y=False,
        )

        # Add secondary y-axis trace (rolling_avg)
        # Fix: Double curly braces for literal braces in f-string
        fig.add_trace(
            go.Scatter(x=df[x_col], y=df[y_secondary_col], name=y_secondary_col.replace('_', ' ').title(), mode='lines+markers',
                       hovertemplate='<b>%{x}</b><br>' + f'{y_secondary_col.replace("_", " ").title()}: %{{y}}:.2f<extra></extra>',
                       line=dict(dash='dot')),
            secondary_y=True,
        )

        fig.update_layout(
            title_text=title,
            title_x=0.5,
            xaxis_title=x_col.replace('_', ' ').title(),
            template="plotly_white",
            hovermode="x unified"
        )
        fig.update_yaxes(title_text=y_col.replace('_', ' ').title(), secondary_y=False)
        fig.update_yaxes(title_text=y_secondary_col.replace('_', ' ').title(), secondary_y=True)

    else:
        fig = px.line(df, x=x_col, y=y_col, title=title, color=color_col, hover_data=hover_data,
                      template="plotly_white")
        fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(),
                          yaxis_title=y_col.replace('_', ' ').title(),
                          title_x=0.5)

    fig.update_xaxes(tickangle=45)

    logger.info(f"Generated line chart: {title}")
    return fig

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    import streamlit as st_temp

    data_bar = {'Category': ['Groceries', 'Utilities', 'Dining', 'Shopping'],
                'Spend': [500, 250, 150, 300]}
    df_bar = pd.DataFrame(data_bar)

    data_pie = {'Vendor': ['Walmart', 'Target', 'Amazon', 'Cafe'],
                'Sales': [400, 200, 150, 50]}
    df_pie = pd.DataFrame(data_pie)

    data_line = {'Month': pd.to_datetime(['2023-01', '2023-02', '2023-03', '2023-04', '2023-05']),
                 'Spend': [1000, 1200, 900, 1500, 1300],
                 'Rolling_Avg': [1000, 1100, 1033.33, 1200, 1166.67]}
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

    st_temp.subheader("Line Chart: Monthly Spend (No Rolling Average)")
    fig_line_no_secondary = plot_line_chart(df_line, 'Month', 'Spend', 'Monthly Spend Trend (No Rolling Avg)')
    st_temp.plotly_chart(fig_line_no_secondary, use_container_width=True)

    st_temp.subheader("Empty Data Chart Example")
    fig_empty = plot_bar_chart(pd.DataFrame(), 'X', 'Y', 'No Data Example')
    st_temp.plotly_chart(fig_empty, use_container_width=True)
