"""spatial_processing_functions.py 

This module contains the functions needed for processing the census geography and SF precinct data. 

"""

from geopandas import GeoDataFrame, read_file
from geopandas.tools import overlay
import pandas as pd

datapath='../data/'
""" path to original data """

resultspath = '../results/'
""" path to any results data that was already collected """


def load_prec_shp(p_yr):
    """Load precinct boundary files, given a year."""
    filename = 'spatial/Precincts_{}/Precincts_{}.shp'.format(p_yr, p_yr)
    pre_df = read_file(datapath+filename)
    
    # For some reason, the 1992 shapefile has one row with a precname and no geom. After mapping it, 
    # it doesn't look like a problem to omit it. 
    n_old = len(pre_df)
    
    pre_df = pre_df[pre_df.geometry.notnull()]
    n_new = len(pre_df)
    print('omitted {} row(s) with missing geometry'.format(n_old-n_new))
    
    print('Year {}: total {} precincts'.format(p_yr, len(pre_df.precname.unique())))  # just checking how many precincts. 
    return(pre_df)

def reproject_prec(pre_df, new_crs='epsg:26910'):
    """Reproject to a CRS with units as meters and add area column (needed for pop density variable)
    new_crs(int): desired reprojected crs
    """
    pre_df = pre_df.to_crs({'init': new_crs})  
    pre_df['area_m']=pre_df.geometry.area
    return(pre_df)


def load_bg_shp(bg_yr, new_crs='epsg:26910'):
    """Load block group boundaries
    Args: 
        bg_yr (str): bg/census year 
        new_crs (int) : desired reprojected crs
    Returns: 
        DataFrame: block group boundaries
    """

    if bg_yr == '2010':
        filename = 'spatial/tl_2010_06075_bg10/tl_2010_06075_bg10.shp'  # shapefile for SF block groups as defined in 2010
    elif bg_yr =='2000':
        filename = 'spatial/tl_2009_06075_bg00/tl_2009_06075_bg00.shp'
    else: 
        print('bg boundaries not available')
    bg_df = read_file(datapath+filename)
    
    # convert GEOID to string for merging later
    if bg_yr == '2010':
        bg_df['geoid'] = bg_df['GEOID10'].astype(str)
    elif bg_yr == '2000':
        # for this one we have to create a geoid. I'm going to define it so it's the same format as 2010. 
        bg_df['geoid'] = bg_df['STATEFP00'].astype(str)+bg_df['COUNTYFP00'].astype(str)+bg_df['TRACTCE00'].astype(str)+bg_df['BLKGRPCE00'].astype(str)
    else: 
        print('bg boundaries not available')
        
    # reproject to a CRS with units as meters
    bg_df = bg_df.to_crs({'init': new_crs}) 
    # while we're at it, add a column to calculate area in meters. 
    bg_df['area_m']=bg_df.geometry.area

    return(bg_df)



def merge_precinct_bg(pre_df, bg_df, yr_name):
    """Merge block group boundaries with precinct. (Might take a few minutes.)
    Args: 
        pre_df (geoDataFrame): precinct 
        bg_df (geoDataFrame): block groups
        yr_name (str): year
    Returns: 
        DataFrame: merged block group boundaries and precinct. 
    """

    print('working on intersection for year {}'.format(yr_name))
    newdf = overlay(pre_df, bg_df, how="intersection")
    # intersection has both precinct and block group IDs. 
    #newdf.head()
    # create a field with the area, will later divide by the total precinct area
    newdf['intersect_area']=newdf.geometry.area
    
    # drop the unneeded columns to clean up
    try:
        cols_to_drop = ['BLKGRPCE10', 'COUNTYFP10', 'FUNCSTAT10', 'INTPTLAT10', 'INTPTLON10', 'MTFCC10','NAMELSAD10', 'STATEFP10']
        newdf = newdf.drop(cols_to_drop, axis=1)
    except ValueError:
        print('cols not present')
    print(newdf.columns)
    print('New df has {} precincts'.format(len(pre_df.precname.unique())))  # just checking how many precincts. 
    
    return(newdf)

def make_geoid_field(df):
    """Make correctly formatted geoid string column in census dataframe
    Args: 
        df (DataFrame): census data
    """
    df['geoid'] = df['state']+df['county']+df['tract']+df['block group']
    return(df)

def load_census_data(yr):
    """Load 'raw' census data that was already collected from API, for given year"""
    filename = 'census_data_{}.csv'.format(yr)
    df = pd.read_csv(resultspath+filename, dtype={'state':str,'county':str,'tract':str,'block group':str,'geoid':str})
    # if geoid field doesn't already exist, create it. 
    if 'geoid' not in list(df.columns):
        df = make_geoid_field(df)
    return(df)


def save_census_data(df, yr):
    """ Save processed census data that is merged with precinct
    Args: 
        df (DataFrame): dataframe to save
        yr (str): year
    """
    filename = 'data_by_precinct/census_by_precinct_{}.csv'.format(yr)
    df.to_csv(resultspath+filename, index=True)
    print('saved as '+filename)
    return()
    
    

def get_vars_to_use():
    """Get variables to use as defined in a separate file. 
    Do this since we don't actually don't want to use all variables, just ones that are consistently available across years. 
    
    """
    filename='variable_codes.xlsx'
    vars_df = pd.read_excel(datapath+filename)
    return(list(vars_df[vars_df['use_in_final']=='yes']['name']))


def calc_variables(df, var_list):
    """Calculate area-weighted values for variables. 
    Formula: x_pre=A_intersect1 / A_pre * x_bg1 +  A_intersect2 / A_pre * x_bg2
    Args: 
        df (DataFrame): the dataframe containing census spatially merged with precincts
        var_list (list): names of variables to calculate. 
    Returns: 
        DataFrame: contains area-weighted values for variables. 
    """
    
    for var in var_list: 
        df[var+'_wgt'] = df[var]*df.intersect_area/ df.area_m
    df['prop_area'] = df.intersect_area/ df.area_m  # include proportional area as a check. 
    return(df)


def agg_vars_by_prec(df):
    """Aggregate back together by precinct 'precname' and check results."""

    df_grouped = df.groupby(by='precname').sum()
    # check if area totals are correct. They should be about 1. 
    print("Sum >1.1 or <.97:\n", df_grouped[(df_grouped.prop_area >1.1)|(df_grouped.prop_area <.97)]['prop_area'])
    return(df_grouped)
 
def rename_wgt_cols(df, var_list):
    """Rename columns by taking off the '_wgt' (just remember they're the weighted variables)
    Args: 
        df (DataFrame): the dataframe containing census spatially merged with precincts
        var_list (list): variables to use
    """
    col_list = list(df.columns)
    new_cols= []
    for s in col_list:
        if s in var_list:
            new_col = s[:-4]
        else:
            new_col = s
        new_cols.append(new_col)
    df.columns = new_cols
    return(df)

    
