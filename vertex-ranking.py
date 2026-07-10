# -*- coding: utf-8 -*-
# This code is ranking the vertex centrality files and plotting  them too
"""
Created on Sun Dec 21 12:58:14 2025
@author: Aditi Bose
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

csv_files = [
"C:/Users/1_Centrality Values and Ranks - window length=2.5s, no binning/vertex-betweenness/011a_LMT_no-ref-ch_vertex-betweenness-centrality.csv"
]

transposed_dfs = {}
ranked_dfs = {}

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
    
    
