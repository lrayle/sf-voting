## includes functions needed for data preparation
import pandas as pd
import numpy as np
import re
from datetime import date

def find_matching_sheets(wb, to_match, to_not_match):
	# searches for the right worksheet and return their names as a list.
	# wb:excel workbook with election results
	# to_match: phrase to match
	# to_not_match: phrase to exlude

    sheets =[]
    for s in wb.sheets():
        s_match = re.search(to_match,s.name, flags=re.IGNORECASE)
        not_match = re.search(to_not_match,s.name, flags=re.IGNORECASE)
        if s_match:
            if not not_match:
                #print(s_match.string)
                sheets.append(s_match.string)
    return(sheets)


# reads a given sheet to a dataframe

def read_vote_sheet(elect_date,prop_letter,vote_df,path):
	# elect_date: election date string
	# prop_letter: proposal letter
	# vote_df: dictionary of vote data 


    f=vote_df[elect_date]['filename']
    s=vote_df[elect_date]['props'][prop_letter]['s_name']
    params=vote_df[elect_date]['props'][prop_letter]['params']
    df=pd.read_excel(path+f,sheetname=s,index_col=params['index_col'], skiprows=params['skiprows'], parse_cols=params['parse_cols'],skip_footer=params['skip_footer'])
    return(df)


# When the spreadsheet only has a single index, we need to make it a multiindex.
def check_if_descriptive(elect_date):
	# This function checks for the format of the index.
	# elect_date: string with election year and month. e.g., '199811'

	# descriptive_labels=True
	# when index is like this:
	## PCT 1101 1101
	## PCT 1101 - Vote By Mail / Absentee Reporting

	# descriptive_labels=False
	# index looks like this: 
	## PCT 2001 8
	## PCT 2001 8

	# descriptive_labels=False Applies to dates '199603','199706','199711', '199806','199811'. So dates <='199811'
	# clues are in the 'registered' column--which we ASSUME IS THE FIRST COLUMN!!
	# d is election date string
    if int(elect_date)<=199811:
        result = False
    else:
        result=True
    return(result)


# turns single index into multiindex
def format_df_to_multiindex(df, descriptive_labels=True):
	# df: dataframe with election results
	# descriptive_labels: Boolean. Determined by function check_if_descriptive
    ballot_types=[]
    precinct=[]
    for i, val in enumerate(df.index):
        #if s contains something about mail or absentee or vbm:
        if descriptive_labels==True:
            match=re.search('mail|absent|vbm',val,flags=re.IGNORECASE)
            if match:    
                ballot_type='A'
                pct=match.string[:8]
            # if s is not a mail-in ballot
            else:
                match = re.search('pct',val, flags=re.IGNORECASE)
                if match:
                    ballot_type='V'
                    pct=match.string[:8]
            
        if descriptive_labels==False:
            if (df.iloc[i,0]==0)|np.isnan(df.iloc[i,0]):
                ballot_type='A'
            elif df.iloc[i,0]>0:
                ballot_type='V'
            match = re.search('pct',val, flags=re.IGNORECASE)
            if match:
                pct=match.string[:8]
        ballot_types.append(ballot_type)
        precinct.append(pct)
    df['type']=ballot_types
    df['precinct']=precinct
    df.set_index(['precinct','type'],inplace=True)
    return(df)

# Example use:
# desc = check_if_descriptive('199711')
# data=format_df_to_multiindex(data,descriptive_labels=desc)
# data.head()


# this checks if second level of multiindex is already "A" and "V"
def check_if_av_format(df):
	#df: dataframe with raw election results
    
    if 'A' in list(df.index.levels[1].values):
        result=True
    elif 'A' not in list(df.index.levels[1].values): 
        result=False
    return(result)

#  if index levels isn't already named with "A" and "V", this will fix it. 
def index_to_av_format(df):
	#df: dataframe with raw election results

    ballot_types=[]
    precincts=[]
    for i, val in enumerate(df.index):
        match = re.search('mail|absent|vbm',val[1], flags=re.IGNORECASE)
        if match:
            ballot_type='A'
        else:
            ballot_type='V'
        ballot_types.append(ballot_type)
        precincts.append(val[0])
    df['type']=ballot_types
    df['precinct']=precincts
    df.set_index(['precinct','type'],inplace=True)
    return(df)

# when dataframe has the format: multiindex, registered, ballots cast, yes, no, need to rename indexx
# This names the index and columns so they are consistent with other dataframes
def rename_index_and_cols(df):
	# df: dataframe with raw election results
    
    # seems to be a bug in using set_levels(). need to get around it some other way. 
    # df.index=df.index.set_levels([['precinct','type'],['A,V']],level=[0,1],inplace=False)
    # if index levels isn't already named with "A" and "V", fix it. 
    av_format=check_if_av_format(df)
    if not av_format:
        df=index_to_av_format(df)
    elif av_format:    
        df.index.names=['precinct','type']
    df.columns=['registered','voted','YES','NO']
    return(df)

# Example use:
#data=rename_index_and_cols(data)
#data.head()


# We should check if we processed the data correctly by verifying the percentages for each precinct add up to 100
# This function calculates total percentages and puts them in spreadsheet so can compare with original. 
def verify_vote_totals(vote_dict, fname):
	# vote_dict: dictionary holding all the dataframes with election results
	# fame: name of file for saving.

	dates=[]
	props=[]
	results=[]
	for d in vote_dict.keys():
	    for p in vote_dict[d]['props'].keys():
	        df=vote_dict[d]['props'][p]['data']
	        yes_pct=df.YES.sum()/(df.YES.sum()+df.NO.sum())
	        results.append(yes_pct)
	        props.append(p)
	        dates.append(d)
	results=pd.DataFrame({'election':dates,'proposal':props,'yes_pct':results})
	results.to_csv('../results/'+fname)
	return

# This will consolidate the absentee and regular votes for each proposition's data. 
# data is the vote data dictionary

# This is a wrapper function that loops through the dictionary of dataframes and applies a function to each one. 
# To be used for all this data processing. 
def process_votedata(data, process_func, use_datekey=False, use_propkey=False, **kwargs):
	# data: dictionary of dataframes that holds the election data. 
	# process_func: the names of the function to apply to each dataframe
	# use_datekey: Boolean. Specifies whether the process function needs a date key
	# use_propkey: Boolean. Specifies whether the process function needs a proposition key
	

    data_new = data # make a copy. I think this is necessary because otherwise it keeps overwriting when I don't want it to. 
    for d in data_new.keys():
        for p in data_new[d]['props'].keys():
            #print('working on ',d,p)
            df=data_new[d]['props'][p]['data']
            # do some function on df
            if use_datekey==True:
                if use_propkey==True:
                    df_new=process_func(df, date_key=d, prop_key=p, **kwargs)
                else:
                    df_new = process_func(df, date_key=d, **kwargs)
                
            elif use_datekey==False:
                if use_propkey==True:
                    df_new=process_func(df, prop_key=p, **kwargs)
                else:
                    df_new = process_func(df, **kwargs)
            
            #new dictionary copy with new dataframe
            data_new[d]['props'][p]['data'] = df_new
    return(data_new)


# This function consolidates any lines that have absentee votes on a separate line. 
# It's needed because a couple of the spreadsheets don't use multiindex, are in a different format. 
def consolidate_abs(df):
   	# df: the dataframe with election results
    
    if isinstance(df.index, pd.core.index.MultiIndex):
        
        # for each proposition's dataframe, make a new df to hold totals
        new_df = pd.DataFrame(index=df.index.levels[0], columns=['voted','YES','NO'])
        for prec in df.index.levels[0]:
            # calculate totals
            totals = df.loc[prec].sum(axis=0)  
            # FIXED: some of the dataframes have number of registered voters in both the regular and absentee
            # rows. So for those the 'registered' column will be 2x the correct amount. 
            new_df.ix[prec] = totals
        
        # recover registered column - create df with only the pct index and registered column

        df=df.sort_index()
        regist_temp = df.loc[(slice(None),['V']),:'registered']
        regist_temp.index = regist_temp.index.droplevel(1)
        
        # merge this back with the new dataframe I just created. 
        new_df = pd.merge(new_df, regist_temp, left_index=True, right_index=True)
        
    elif isinstance(df.index, pd.core.index.Index):
        # maybe do some other processing
        new_df=df

    return(new_df)



######## FUNCTIONS TO DEFINE THE NIMBY VARIABLES ########

# This function will look up the value for the nimby variable value, given the election date and proposal letter.

def lookup_nimby_value(date_key, letter, df_prop):
	# date_key: code with election date
	# letter: proposition letter
	# df_prop: the proposals dataframe

    x = df_prop[(df_prop.Date_str==date_key)&(df_prop.Letter==letter)]['Vote that equals NIMBY'].values[0]
    return(x)
    
# Function will make two variables, one that is total nimby votes and one that is percent nimby votes. 
def make_vote_variables(df,date_key,prop_key, df_prop):
	# df: dataframe with election results
	# date_key: code with election date
	# prop_key: proposition key
	# df_prop: the proposals dataframe (probably called 'proposals')

    nimby_val = lookup_nimby_value(date_key, prop_key, df_prop)
    df['tot_nimby_votes'] = df[nimby_val]

    # 'voted' is the total ballots received, but some voters may have skipped some ballot items)
    try:
        df['pct_nimby'] = df.tot_nimby_votes/(df.YES + df.NO)  # Pct nimby/ total votes for that proposal
    except(ZeroDivisionError):
        df['pct_nimby'] = np.nan

    # Make turnout variable
    df['turnout'] = df.voted/df.registered
    
    return(df)


# We need to format precinct columns so they match. Correct format is a 4-digit string. 

# what to do with precints that seems to be combined? e.g., 1104/1105? 
# split into two rows, I guess
# This will create a copy of the row values. 
# IMPORTANT: Don't rely on total vote counts. Doesn't matter anyway, it's the percentage that matters. 

# This function splits precincts into two rows
def split_prec_rows(df):
	# df: dataframe with election results
    for idx in df.index:
        # look for rows with precincts that need to be split
        if re.search('\d{4}/\d{4}',idx):
            a,b = idx.split('/')
            row_values = df.loc[idx]
            df.loc[a] = row_values
            df.loc[b] = row_values
            
            # delete original row
            df = df.drop(idx, axis=0)
    return(df)


# what to do with precincts marked "mail"? I think these are ones that are not physical places. 
# I'll just strip off the mail part and if it doesn't match up with a physical prec during merge, then it'll be omitted.

# further formatting of precincts. Gets rid of ones marked "mail"
def format_precincts(df):
  	# df: dataframe with election results
   
    df.index = df.index.str.strip('MAIL').str.strip('mail').str.strip()
    # strip unneeded characters
    df.index = df.index.str.strip('PCT').str.strip('Pct').str.strip()
    # split double precint rows
    df_new = split_prec_rows(df)
    
    #print(df_new.head())
    return(df_new)
   
###### FUNCTIONS TO MERGE WITH CENSUS DATA ###### 

# load census data
def get_census_data(yr_key):
	# yr_key: the 6-digit election year-month key
    censuspath = '../results/data_by_precinct/'
    filename = 'census_by_precinct_{}.csv'.format(yr_key)
    df = pd.read_csv(censuspath+filename, dtype={'precname':str})
    return(df)

# This function matches election with appropriate year for census dataset and precinct boundaries. 
def voting2census_key(vote_key):
	# vote_key: the 6-digit election year-month key

    if int(vote_key)<=200211: # try changing the cutoff from 200203 to 200211. Yes this is better. 
        census_key = 'ce2000pre1992'
    elif (int(vote_key)>200211)&(int(vote_key)<=200400):  # try changing this from 200203 to 200211
        census_key = 'ce2000pre2002'
    elif (int(vote_key)>200400)&(int(vote_key)<201211):
        census_key = 'ce2007pre2002'
    elif int(vote_key)>=201211:
        census_key = 'ce2012pre2012'
    else: 
        print('year outside of range')
        census_key = None
    return(census_key)

# This merges voting data with census data
def merge_vote_census(vote_df, date_key):
    
    census_key = voting2census_key(date_key)
    census_df = get_census_data(census_key)
    #print(census_df.head())
    #print(vote_df.head())
    merged_df = pd.merge(vote_df, census_df, left_index=True, right_on='precname', how='inner')
    # check how it turned out. 
    print('\n for election ', date_key)
    print('length vote data: ', len(vote_df), 'length census data: ', len(census_df))
    print('length new data: ', len(merged_df))
    return(merged_df)

##### FUNCTIONS TO MAKE SOME VARIABLES NEEDED FOR THE ANALYSIS ####### 

# function to make election dummy variables
def make_election_dummies(df, date_key, prop_key): 
	# df: dataframe with election results
	# date_key: the 6-digit election year-month key
	# prop_key: the ballot proposition letter
    year = date_key[0:4]
    mo = date_key[4:6]
    if date_key in ['201211','200811','200411','200011','199611','199211']:
        pres = True
    else:
        pres = False
    if mo=='11':
        nov=True
    else:
        nov=False
    # add dummy variables
    df['yr_'+year] = True
    df['pres_elec']=pres
    df['nov_elec'] = nov
    
    # also add 'year' and year+proposal code variables
    df['year'] = year
    df['yr_prop']= date_key+prop_key
    return(df)

# Some variables are not comparable across years: med_value, med_inc, med_yr_moved, med_yr_built
# we need to fix it. 
# Function to fix fix med_yr_built and med_yr_moved
def fix_yr_built_moved(df, date_key):
	# df: dataframe with election results combined with census data
	# date_key: the 6-digit election year-month key
    year = int(date_key[0:4])
    # median housing unit age ('med_hu_age') = current year - med year built
    df['med_hu_age']=year-df.med_yr_built_wgt
    # median years lived in house ('med_yrs_lived') = current year - med year moved
    df['med_yrs_lived'] = year-df.med_yr_moved_all_wgt
    df['med_yrs_lived_owner'] = year-df.med_yr_moved_owner_wgt
    return(df)


# adjust med income and med house value for inflation. Adjust all to 2014 dollars
def adjust_inflation(df, date_key):
	# df: dataframe with election results combined with census data
	# date_key: the 6-digit election year-month key

    year = date_key[0:4]
    if int(date_key)<=200400: 
        # need 1999 -> 2014    $1 in 1999 = $1.42 in 2014
        r = 1.42
    elif (int(date_key)>200400)&(int(date_key)<201211):
        # use 2012 -> 2014
        r = 1.03
    elif int(date_key)>=201211:
        # keep in 2014 
        r = 1
    else: 
        print('year outside of range')
        r = 1
    # calculate inflation-adjusted values for income and house value.
    df['med_inc_adj'] = df.med_inc_wgt*r
    df['med_val_adj'] = df.med_value_wgt*r
    
    return(df)
    
# function puts all the dataframes together.
def combine_dataframes(data):
	# data: the dictionary of dataframes that each hold election results combined with census data
    n=0
    for d in data.keys():
        for p in data[d]['props'].keys():
            print('working on ',d,p)
            df=data[d]['props'][p]['data']
            print(len(df))
            if n==0:
                df_new = df
            elif n>=1:
                df_new = pd.concat([df,df_old],axis=0)
            df_old = df_new
            n+=1
    return(df_old)



