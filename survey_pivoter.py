#! /bin/env python3

import pandas as pd
import numpy as np
import os
import yaml
from collections import defaultdict
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("config_file", help="Path to config yaml file with survey-specific settings (e.g. config.yml)")
args = parser.parse_args()


config_file = args.config_file

with open(config_file, 'r') as ymlfile:
    try:
        cfg = yaml.load(ymlfile)
        year = cfg['year']
        survey_name = cfg['survey_name']
        id_col = cfg['id_column']
        
        spss = cfg['spss']
        spss = bool(spss)
        weight_col = cfg['weight_col']
        if spss == False:
            input_filename_l = cfg['input_filename_with_labels']
            input_filename_v = cfg['input_filename_with_values']
        elif spss == True:
            input_filename = cfg['input_filename']
        else:
            raise Exception(
                "Configuration variable 'spss' must be set either to True or False (boolean var, not a string) in config file. Actual value is {}".format(spss)
            )
        include_in_every_row = cfg['varables_to_include_in_every_row_of_output_file']
        dont_pivot = cfg['dont_pivot']
        exclude_from_analysis = cfg['exclude_from_analysis']
    except KeyError as e:
        raise KeyError("Expected variable {} in config file {} but it wasn't found".format(e, config_file))

if spss:
    from rpy2.robjects import pandas2ri, r

output_file = '{}_{}_pivoted.csv'.format(year, survey_name.lower().replace(' ', '_'))

def get_df(filename, val_labels):
    # This is a really weird workaround used because the pandas2ri method was changing the
    # data that came back to code N/As incorrectly when value labels were on. So now R 
    # writes csvs and pandas reads them
    tmpfile = 'tmp_spss_reader.csv'
    r_commands = """
    df = suppressWarnings(foreign::read.spss("{}", to.data.frame = TRUE, use.value.labels = {}))
    write.csv(df, file='{}', row.names=FALSE)
    """.format(filename, str(val_labels).upper(), tmpfile)
    r(r_commands)
    d = pd.read_csv(tmpfile, low_memory=False)
    os.remove(tmpfile)
    return(d)

def get_variable_labels(filename):
    w = r('as.data.frame(attributes(foreign::read.spss("{}"))["variable.labels"])[,1]'.format(filename))
    cat = pandas2ri.ri2py(w)
    return(list(cat))
    
if spss == True:
    df1 = get_df(input_filename, True)
    df2 = get_df(input_filename, False)
else:
    df1 = pd.read_csv(input_filename_l, low_memory=False)
    df2 = pd.read_csv(input_filename_v, low_memory=False)

if df1.shape != df2.shape:
    print("Shape of labels data is {} and shape of values data is {}".format(df1.shape, df2.shape))
    raise

varnames = df1.columns
if spss == True:
    varlabels = get_variable_labels(input_filename)
else:
    varlabels = varnames

varmap = dict(zip(varnames, varlabels))
df3 = df1.merge(df2, left_index=True, right_index=True, suffixes=('_l', '_v'))

new_df_cols = []

for col in varnames:
    lab = '{}_l'.format(col)
    val = '{}_v'.format(col)
    if df3[lab].equals(df3[val]):
        a = df3[lab]
        a.name = col
        new_df_cols.append(a)
    else:
        new_df_cols.append(df3[lab])
        new_df_cols.append(df3[val])

df = pd.DataFrame(new_df_cols).T
df_cols = df.columns

# If weight column specified above doesn't exist, 
# create it and set all weights to 1
if weight_col not in df_cols:
    df[weight_col] = 1

def get_count_neg_map(domain):
    l = len(domain)
    m = defaultdict(lambda: 0)
    for i in range(0, int(np.floor(l/2))):
        m[domain[i]] = 1
    for i in range(int(np.ceil(l/2)), l):
        m[domain[i]] = 0
    if l % 2 != 0:
        m[domain[int(np.floor(l/2))]] = .5
    return(m)

every_row = []
for v in include_in_every_row:
    if v not in df.columns:
        if v + '_l' in df.columns:
            every_row.append(v + '_l')
            print('Merged data file is missing column {0}, using {0}_l instead'.format(v))
        else:
            print('Merged data file is missing column {}, and no replacement was found'.format(v))
    else:
        every_row.append(v)

        
dataframes = []
for v in varnames:
    if v not in dont_pivot:
        pivoted = pd.DataFrame(columns = [
                               'survey_name', 'year', 'id', 'question_varname',
                               'question_text', 'answer_text', 'answer_value', 
                               'weight', 'count_negative'] + every_row)
        if '{}_l'.format(v) in df_cols:
            labels = df['{}_l'.format(v)]
            vals = df['{}_v'.format(v)]
        else:
            labels = pd.Series(np.nan, index=np.arange(0, len(df)))
            vals = df[v]
        pivoted['answer_value'] = vals
        pivoted['answer_text'] = labels
        # Figure out which indices to exclude from analysis
        if len(labels.dropna()) > 0:
            exclude = pd.Series(False, index=np.arange(0, len(labels)))
            exclude[(labels.notnull()) & (labels.dropna().astype(str).str.lower().isin(exclude_from_analysis))] = True
        # Now figure out domain excluding 'exclude from analysis' answers
        domain = list(pd.unique(vals[(labels.notnull()) & (~labels.isin(exclude_from_analysis))].dropna().values))
        domain.sort()
        m = get_count_neg_map(domain)
        pivoted.count_negative = 0
        if len(m) > 0:
            pivoted['count_negative'] = vals.replace(m)
        pivoted['survey_name'] = survey_name
        pivoted['year'] = year
        pivoted['id'] = df[id_col]
        pivoted['question_varname'] = v
        pivoted['question_text'] = varmap[v]
        pivoted['weight'] = df[[weight_col]]
        pivoted[every_row] = df[every_row]
        dataframes.append(pivoted)
        
final_product = pd.concat(dataframes)
final_product = final_product[final_product['answer_value'].notnull()]
final_product = final_product[final_product['answer_value'].str.strip() != '']
final_product = final_product.sort_values(['year', 'survey_name', 'question_varname', 'id'])
final_product.to_csv(output_file, index=False)
print('Reshaped output file was successfully written to {}'.format(output_file))