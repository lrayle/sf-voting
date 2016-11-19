###### SPATIAL PROCESSING FUNCTIONS ###### 

# this module contains the functions needed for processing the census geography and SF precinct data. 


from geopandas import GeoDataFrame, read_file
from geopandas.tools import overlay
import pandas as pd


# function to load precinct boundary files, given a year
def load_prec_shp(p_yr, new_crs='epsg:26910'):
	# p_yr: precinct year
	# new_crs: desired reprojected crs

    precinctpath = '../data/spatial/'
    filename = precinctpath+'Precincts_{}/Precincts_{}.shp'.format(p_yr, p_yr)
    pre_df = read_file(filename)
    
    # rename columns to standard names. ONly necessary for 2012. 
    # what was originally 'PREC_2012' becomes 'precname'
    if p_yr=='2012':
        pre_df.columns = ['AssemDist', 'BARTDist', 'CongDist', 'NeighRep', 'PREC_2010','precname', 'Shape_Area', 'Shape_Leng', 'SupDist', 'geometry']
    
    # For some reason, the 1992 shapefile has one row with a precname and no geom. After mapping it, 
    # it doesn't look like a problem to omit it. 
    n_old = len(pre_df)
    pre_df = pre_df[pre_df.geometry.notnull()]
    n_new = len(pre_df)
    print('omitted {} row(s) with missing geometry'.format(n_old-n_new))
    
    #print(pre_df.head())
    print(len(pre_df.precname.unique()))  # just checking how many precincts. Looks about right. 
    
    # reproject to a CRS with units as meters
    pre_df.plot()
    pre_df = pre_df.to_crs({'init': new_crs})  
    pre_df['area_m']=pre_df.geometry.area
    return pre_df

# function to load block group boundaries
def load_bg_shp(bg_yr, new_crs='epsg:26910'):
	# bg_yr: bg/census year 
	# new_crs: desired reprojected crs

    tigerpath = '../data/spatial/'
    if bg_yr == '2010':
        filename = 'tl_2010_06075_bg10/tl_2010_06075_bg10.shp'  # shapefile for SF block groups as defined in 2010
    elif bg_yr =='2000':
        filename = 'tl_2009_06075_bg00/tl_2009_06075_bg00.shp'
    else: 
        print('bg boundaries not available')
    bg_df = read_file(tigerpath+filename)
    
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
    print(bg_df.head())
    #bg_df.plot() # check it out
    return(bg_df)


# function to merge block group boundaries with precinct. 
# since this takes a long time, do it minimum number of times. 
def merge_precinct_bg(pre_df, bg_df, yr_name):
	# pre_df: precinct geo dataframe
	# bg_df: block group geo dataframe
	# yr_name: string with year 

    print('working on intersection for year {}'.format(yr_name))
    newdf = overlay(pre_df, bg_df, how="intersection")
    # intersection has both precinct and block group IDs. 
    newdf.head()
    # create a field with the area, will later divide by the total precinct area
    newdf['intersect_area']=newdf.geometry.area
    
    # drop the unneeded columns to clean up
    try:
        cols_to_drop = ['AssemDist', 'BARTDist', 'CongDist', 'NeighRep', 'Shape_Area', 'Shape_Leng', 'SupDist', 'BLKGRPCE10', 'COUNTYFP10', 'FUNCSTAT10', 'INTPTLAT10', 'INTPTLON10', 'MTFCC10','NAMELSAD10', 'STATEFP10']
        newdf = newdf.drop(cols_to_drop, axis=1)
    except:
        print('cols not present')
    print(newdf.columns)
    
    return(newdf)



# Function to make correctly formatted geoid string column in census dataframe
def make_geoid_field(df):
	# df: dataframe with census data
    df['geoid'] = df['state']+df['county']+df['tract']+df['block group']
    return(df)

# Load 'raw' census data that was already collected from API
def load_census_data(yr):
	# yr: string with year
    censuspath = '../results/'
    df = pd.read_csv(censuspath+'census_data_{}.csv'.format(yr), dtype={'state':str,'county':str,'tract':str,'block group':str,'geoid':str})
    # if geoid field doesn't already exist, create it. 
    if 'geoid' not in list(df.columns):
        df = make_geoid_field(df)
    return(df)

# Save processed census data that is merged with precinct
def save_census_data(df, yr):
	# df: dataframe to save
	# yr: string with year
    censuspath = '../results/data_by_precinct/'
    filename = 'census_by_precinct_{}.csv'.format(yr)
    df.to_csv(censuspath+filename, index=True)
    print('saved as '+filename)
    return()
    
    
# Since we don't actually don't want to use all variables, just ones that are consistently available across years. 
# Get variables to use as defined in the variables_codes.xlsx file
def get_vars_to_use():
    path='../data/census/'
    filename='variable_codes.xlsx'
    vars_df = pd.read_excel(path+filename)
    return(list(vars_df[vars_df['use_in_final']=='yes']['name']))

# This will calculate area-weighted values for variables
# Formula: x_pre=A_intersect1 / A_pre * x_bg1 +  A_intersect2 / A_pre * x_bg2
def calc_variables(df, var_list):
	# df: the dataframe containing census spatially merged with precincts
	
    for var in var_list: 
        df[var+'_wgt'] = df[var]*df.intersect_area/ df.area_m
    df['prop_area'] = df.intersect_area/ df.area_m  # include proportional area as a check. 
    return(df)

# aggregate back together by precinct 'precname'
def agg_vars_by_prec(df):
	# df: the dataframe containing census spatially merged with precincts
    df_grouped = df.groupby(by='precname').sum()
    # check if area totals are correct. They should be about 1. 
    print("something's wrong with these:\n", df_grouped[(df_grouped.prop_area >1.1)|(df_grouped.prop_area <.97)]['prop_area'])
    return(df_grouped)

# rename columns by taking off the '_wgt' (just remember they're the weighted variables)
def rename_wgt_cols(df, var_list):
	# df: the dataframe containing census spatially merged with precincts
	# var_list: list of variables to use
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