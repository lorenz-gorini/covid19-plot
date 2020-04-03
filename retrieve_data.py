import math
from urllib.error import HTTPError

import pandas as pd
import datetime
import matplotlib
import bokeh.plotting as bk
import bokeh
import bokeh.palettes
from bokeh.models import DatetimeTickFormatter, ColumnDataSource

import logging

main_url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master'
andamento_nazionale_str = '/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale-'
andamento_regioni_str = '/dati-regioni/dpc-covid19-ita-regioni-'

national_hover_list = ['data', 'deceduti', 'dimessi_guariti', 'nuovi_positivi',
                       'totale_casi', 'tamponi', 'terapia_intensiva', 'totale_ospedalizzati',
                       'isolamento_domiciliare']
# regions_cols = ['denominazione_regione', 'lat',	'long', 'ricoverati_con_sintomi', 'terapia_intensiva',
#                 'totale_ospedalizzati', 'isolamento_domiciliare', 'totale_positivi', 'variazione_totale_positivi',
#                 'nuovi_positivi', 'dimessi_guariti', 'deceduti', 'totale_casi', 'tamponi']
REGIONAL_HOVER_LIST = ['denominazione_regione', 'lat', 'long', 'ricoverati_con_sintomi', 'terapia_intensiva',
                'totale_ospedalizzati', 'isolamento_domiciliare', 'totale_positivi', 'variazione_totale_positivi',
                'nuovi_positivi', 'dimessi_guariti', 'deceduti', 'totale_casi', 'tamponi']
NATIONAL_COLS_SHOW_LIST = ['deceduti', 'dimessi_guariti', 'nuovi_positivi',
                       'totale_casi', 'terapia_intensiva', 'totale_ospedalizzati',
                       'isolamento_domiciliare']


def retrieve_data_from_url(middle_url, final_date=datetime.date.today()) -> pd.DataFrame:

    data_timerange = pd.date_range(start=datetime.date(2020, 2, 24), end=final_date)
    # Initialize df
    monthly_df = pd.read_csv(f"{main_url}{middle_url}{data_timerange[0].strftime('%Y%m%d')}.csv")
    # Fill up the df with new daily_df for different dates
    for day in data_timerange[1:]:
        # Retrieve data but if it is too early, no data may be available
        try:
            daily_df = pd.read_csv(f"{main_url}{middle_url}{day.strftime('%Y%m%d')}.csv")
            monthly_df = pd.concat([monthly_df, daily_df], axis=0)
        except HTTPError:
            logging.warning(f"Data from the day {day.strftime('%Y%m%d')} has not been recorded yet.")
    
    # Reformat data column to DateTime
    try:
        monthly_df['data'] = pd.to_datetime(monthly_df['data'], format='%Y-%m-%d %H:%M:%S')
    except KeyError:
        logging.warning('No data column in the DF. It could be a problem if you want to use that as x_axis')

    return monthly_df


def _complete_bokeh_plot_trivial_settings(p):
    p.left[0].formatter.use_scientific = False
    p.title.text = 'CoVid-19 in Italy'
    p.legend.location = "top_left"
    p.legend.click_policy = 'hide'
    p.xaxis.formatter = DatetimeTickFormatter(
        seconds=["%d %m %Y"],
        minutes=["%d %m %Y"],
        hours=["%d %m %Y"],
        days=["%d %B %Y"],
    )
    p.xaxis.major_label_orientation = math.pi / 4


def _get_hover_tooltips_from_list(hover_list, *args):
    hover = bokeh.models.tools.HoverTool()  # (mode='vline')

    # Create the list of tuples as hover tooltips
    tooltips_hover_list = []
    hover_features = hover_list
    hover_features.extend(args)
    for feat in hover_features:
        # The brackets are needed by bokeh for features with whitespaces
        feat_with_brackets = '{' + str(feat) + '}'
        # Append the required feat
        tooltips_hover_list.append(
            (f'{feat}', f'@{feat_with_brackets}')
        )
    # Add tooltips to plot
    hover.tooltips = tooltips_hover_list

    return hover


def bokeh_plot_2(df: pd.DataFrame, x_col_name='data'):
    """
    This is to create 'hover' tool with only x, y values
    :param df:
    :param x_col_name:
    :return:
    """
    # output to static HTML file
    bk.output_file(f"National_plot.html")

    p = bk.figure(plot_width=650, plot_height=650, x_axis_type="datetime")

    for column, color in zip(NATIONAL_COLS_SHOW_LIST, bokeh.palettes.Category20[20]):
        source = ColumnDataSource(dict(x=df[x_col_name], y=df[column]))
        p.line(x='x', y='y', line_width=4, color=color, alpha=0.5, source=source, legend_label=column)

    hover = _get_hover_tooltips_from_list(hover_list=['x', 'y'])
    p.add_tools(hover)

    _complete_bokeh_plot_trivial_settings(p)
    # show the results
    bk.show(p)


def bokeh_plot(df: pd.DataFrame, x_col_name='data'):
    """
    This is to create a plot with 'hover' tool with all the informations
    :param df:
    :param x_col_name:
    :return:
    """
    # output to static HTML file
    bk.output_file(f"National_plot.html")

    p = bk.figure(plot_width=650, plot_height=650, x_axis_type="datetime")

    for column, color in zip(NATIONAL_COLS_SHOW_LIST, bokeh.palettes.Category20[20]):
        p.line(x=x_col_name, y=column, line_width=4, color=color,  alpha=0.5, source=df, legend_label=column)

    hover = _get_hover_tooltips_from_list(hover_list=national_hover_list)
    p.add_tools(hover)

    _complete_bokeh_plot_trivial_settings(p)
    # show the results
    bk.show(p)


def plot_regions_slopes(df, groupby_column, filename, y_column, x_col_name='data'):
    df_groupby = df.groupby(groupby_column)
    groups_df = [x for _, x in df_groupby]

    # output to static HTML file
    bk.output_file(f"{filename}.html")

    p = bk.figure(plot_width=650, plot_height=650, x_axis_type="datetime")

    for group_df, group_name, color in zip(groups_df, df_groupby.groups.keys(), bokeh.palettes.Category20[20]):
        p.line(x=x_col_name, y=y_column, line_width=4, color=color,  alpha=0.5,
               source=group_df, legend_label=group_name)

    hover = _get_hover_tooltips_from_list(REGIONAL_HOVER_LIST, groupby_column, y_column)
    p.add_tools(hover)

    _complete_bokeh_plot_trivial_settings(p)
    # show the results
    bk.show(p)


# TODO: PLOT PERCENTAGE VARIATION
if __name__ == '__main__':
    monthly_regions_df = retrieve_data_from_url(middle_url=andamento_regioni_str,
                                        final_date=datetime.date.today()) # - datetime.timedelta(days=1))
    monthly_national_df = retrieve_data_from_url(middle_url=andamento_nazionale_str,
                                        final_date=datetime.date.today()) # - datetime.timedelta(days=1))
    # monthly_df = pd.read_csv('andamento_nazionale_totale.csv')

    monthly_national_df.to_csv('andamento_nazionale_totale.csv')
    monthly_regions_df.to_csv('andamento_regionale_totale.csv')
    # data_groups_by_region = [x for _, x in monthly_df.groupby('denominazione_regione')]
    plot_regions_slopes(monthly_regions_df, groupby_column='denominazione_regione',
                        filename='regions_plot', y_column='nuovi_positivi')
    bokeh_plot(monthly_national_df)
    # monthly_df['deceduti'].plot()
    print('end')
