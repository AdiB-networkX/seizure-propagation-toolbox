# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 05:30:14 2025
@author: Aditi Bose
"""

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import importlib.util
import re

# Define global variables
segment_group_results = {}
all_results = []

def process_network(vertex_centrality, edge_centrality, segment_scheme):
    """Process network data to determine LIN and MIN values based on centrality metrics."""
    global segment_group_results
    segment_group_results = {}

    for segment_group in segment_scheme:
        group_results = {
            'LIN_nodes': [],
            'MIN_nodes': [],
            'LIN_ranks': [],  
            'MIN_ranks': [],
            'selected_segment': [],      
            'selected_edge': [],         
            'median_centrality_value': [] 
        }
        
        edge_centrality_group = edge_centrality[edge_centrality['Segment'].isin(segment_group)]
        
        max_values = edge_centrality_group.iloc[:, 1:].max(axis=1).values
        max_column_headers = edge_centrality_group.iloc[:, 1:].idxmax(axis=1).values
        sorted_max_values = np.sort(max_values)
        num_values = len(sorted_max_values)
        median_index = num_values // 2 - 1 if num_values % 2 == 0 else num_values // 2
        median_value = sorted_max_values[median_index]
        median_value_indices = np.where(max_values == median_value)[0]
        first_median_idx = median_value_indices[0]
        median_column = max_column_headers[first_median_idx]
        matching_segment_indices = edge_centrality_group.index[[first_median_idx]]
        
        x, y = map(int, median_column.strip('()').split(','))

        # Get the actual Segment value (window number) from the CSV
        selected_segment_id = edge_centrality_group.iloc[first_median_idx]['Segment']

        for idx in matching_segment_indices:
            vertex_row = vertex_centrality.loc[idx]
            rank_x = vertex_row.iloc[x + 1]  # Get rank for x
            rank_y = vertex_row.iloc[y + 1]  # Get rank for y
            
            if rank_x < rank_y:
                MIN, LIN = x, y
                MIN_rank = rank_x
                LIN_rank = rank_y
            else:
                LIN, MIN = x, y
                LIN_rank = rank_x
                MIN_rank = rank_y

            col_header_LIN = vertex_row.index[1:][LIN]
            col_header_MIN = vertex_row.index[1:][MIN]

            group_results['LIN_nodes'].append(col_header_LIN)
            group_results['MIN_nodes'].append(col_header_MIN)
            group_results['LIN_ranks'].append(LIN_rank)
            group_results['MIN_ranks'].append(MIN_rank)
            group_results['selected_segment'].append(selected_segment_id)   
            group_results['selected_edge'].append(median_column)            
            group_results['median_centrality_value'].append(median_value)   

        segment_group_results[str(segment_group)] = group_results

    return segment_group_results

def categorize_node(node):
    """Categorize node based on its alphabetical part."""
    alpha_part = ''.join(filter(str.isalpha, node))
    
    if alpha_part in ['TL', 'TR']:
        return 'F'
    elif alpha_part in ['TBAL', 'TBPL', 'TBAR', 'TBPR']:
        return 'N'
    elif alpha_part in ['TLL', 'TLR']:
        return 'O'
    return None

def categorize_edge(lin_node, min_node):
    """Categorize edge based on its nodes' categories."""
    lin_cat = categorize_node(lin_node)
    min_cat = categorize_node(min_node)
    
    categories = sorted([lin_cat, min_cat])  # Sort to ensure consistent ordering
    return ''.join(categories)

def plot_edge_categories(edge_category_mapping, output_file, plot_title):
    """Create plot with edge categories on y-axis."""
    edge_types = ['FF', 'FN', 'FO', 'NN', 'NO', 'OO']
    
    symbols = {
        'FF': 'o',
        'FN': 'o',
        'FO': 'o',
        'NN': 'o',
        'NO': 'o',
        'OO': 'o'
    }
    
    category_positions = {
        'FF': 0.7,
        'FN': 0.6,
        'FO': 0.5,
        'NN': 0.4,
        'NO': 0.3,
        'OO': 0.2
    }

    colors = {
        'FF': '#8C000F',    #crimson
        'FN': '#D2691E',    #chocolate
        'FO': '#FAC205',    #goldenrod
        'NN': '#008080',    #teal
        'NO': '#04D8B2',    #aquamarine
        'OO': '#808080',    #grey
    }

    fig, ax = plt.subplots(figsize=(8, 4))

    for segment, category in edge_category_mapping.items():
        x = segment
        y = category_positions[category]
        ax.plot(x, y, symbols[category], markersize=10, color=colors[category])

    x_ticks = list(edge_category_mapping.keys())
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_ticks, rotation=90)

    ax.set_yticks(list(category_positions.values()))
    ax.set_yticklabels(edge_types)
    
    for tick in ax.get_xticklabels():
        if int(tick.get_text()) < 2 or int(tick.get_text()) >= len(x_ticks) - 2:
            tick.set_color('red')
        else:
            tick.set_color('black')

    ax.set_xlabel('Windows')
    ax.set_title(plot_title)
    
    legend_patches = [
        mpatches.Patch(color=color, label=cat)
        for cat, color in colors.items()
    ]
    ax.legend(handles=legend_patches, loc='best')

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def process_single_file(vertex_file, edge_file, segment_file, output_directory=None, plot_name=None):
    """Process a single file and optionally generate plot."""
    # Load data
    vertex_centrality = pd.read_csv(vertex_file)
    edge_centrality = pd.read_csv(edge_file)
    
    # Load segment scheme
    spec = importlib.util.spec_from_file_location("segment_scheme", segment_file)
    segment_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(segment_module)
    segment_scheme = segment_module.segment_scheme
    
    # Process network
    global segment_group_results
    results = process_network(vertex_centrality, edge_centrality, segment_scheme)
    
    selected_segments = [
    int(group['selected_segment'][0]) 
    for group in results.values()
    ]
    print(f"{plot_name}: {selected_segments}")
    
    if output_directory and plot_name:
        # Create mapping of segments to edge categories
        edge_category_mapping = {}
        segment_counter = 0
        
        for segment_group_results in results.values():
            for lin_node, min_node in zip(segment_group_results['LIN_nodes'], 
                                        segment_group_results['MIN_nodes']):
                category = categorize_edge(lin_node, min_node)
                edge_category_mapping[segment_counter] = category
                segment_counter += 1
        
        # Generate plot
        os.makedirs(output_directory, exist_ok=True)
        output_file = os.path.join(output_directory, f"{plot_name}.png")
        plot_edge_categories(edge_category_mapping, output_file, plot_name)
        # print(f"Processed and saved plot for {plot_name}")
    
    return results

def main(vertex_files, edge_files, segment_files, output_directory, plot_names):
    """Process multiple files and generate plots for each."""
    global all_results
    all_results = []
    
    for vertex_file, edge_file, segment_file, plot_name in zip(
            vertex_files, edge_files, segment_files, plot_names):
        
        results = process_single_file(
            vertex_file, 
            edge_file, 
            segment_file, 
            output_directory, 
            plot_name
        )
        
        all_results.append({
            'plot_name': plot_name,
            'results': results
        })
    
    return all_results

# Example usage for processing multiple files
if __name__ == "__main__":


    vertex_files = [
"C:/Users/centrality-csvs-ranked/betweenness/vertex/[ranked]011a_LMT_no-ref-ch_vertex-betweenness.csv",
        ]
    edge_files = [
"C:/Users/centrality-csvs/betweenness/edge/011a_LMT_no-ref-ch_edge-betweenness.csv",
        ]
    
    
#####====================================================#####
##########           NETWORK BINNING SCHEMES             
#####====================================================#####
    # each file has grouping for consecutive networks e.g. [0,1,2],[3,4,5]...
    segment_files = [
"C:/Users/network-binning-scheme/011a_L1.py",
 ]


    plot_names = [
"betweenness - 011a_L1",
    ]
   
    output_directory = "C:/Users/nw-select_deg/25p-overlap/12nws"
    
    main(vertex_files, edge_files, segment_files, output_directory, plot_names)
