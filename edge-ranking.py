# -*- coding: utf-8 -*-
"""
Created on Sun Jun  2 06:05:22 2024
@author: Aditi Bose
"""


import pandas as pd
import matplotlib.pyplot as plt
import os

csv_files = [
"C:/Users/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness/011a_LMT_no-ref-ch_edge-betweenness-centrality.csv"
]

transposed_dfs = {}
ranked_dfs = {}

#Just to calculate dege centralities
output_directory = "C:/Users/centrality-csvs"

for file in csv_files:    
    file_name = os.path.basename(file)
    base_name = os.path.splitext(file_name)[0]
    
    df = pd.read_csv(file, index_col=0)  # Read each CSV, use the first column as the index
    transposed_df = df.T
    ranked_df = transposed_df.rank(ascending=False, method='first') # method='first':To break tie in centrality value and 
                                                                    # assign each centrality value a unique rank
    final_transposed_df = ranked_df.T  # for plotting purpose
    
    transposed_dfs[file] = transposed_df
    ranked_dfs[file] = ranked_df
    
    output_file_path = os.path.join(output_directory, f'[ranked]{base_name}.csv')
    final_transposed_df.to_csv(output_file_path)

