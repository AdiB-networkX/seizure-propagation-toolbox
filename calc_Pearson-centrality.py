# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 13:39:21 2025
@author: Aditi Bose
"""

import numpy as np
import scipy as sp
from scipy.sparse import linalg
from graph_tool.all import *
import pandas as pd
from itertools import combinations
from scipy.stats import pearsonr
import os

# Input EEG file paths (add multiple paths here)
eeg_file_paths = [
"/content/drive/MyDrive/project: EEG epilepsy-UKB/Codes-for-submission2025_science-advances/011a_LMT_no-ref-ch.csv"
]

# Output directories for correlation metrics corresponding to input files
correlation_output_dirs = [
"/content/drive/MyDrive/project: EEG epilepsy-UKB/Codes-for-submission2025_science-advances/PCMs/011a_LMT"
]

# Output directories for centrality measures
output_dir_vertex = "/content/drive/MyDrive/project: EEG epilepsy-UKB/Codes-for-submission2025_science-advances/centrality-csvs"
output_dir_edge = "/content/drive/MyDrive/project: EEG epilepsy-UKB/Codes-for-submission2025_science-advances/centrality-csvs"

# Create output directories if they do not exist
os.makedirs(output_dir_vertex, exist_ok=True)
os.makedirs(output_dir_edge, exist_ok=True)

# Constants
sampling_freq = 200  # Hz
window_length = 2.5   # seconds
window_size = int(window_length * sampling_freq)  # Number of samples per window

# Step 1: Segmenting the data into windows
def segment_data(data, window_size):
    """
    Segments the data into windows with special handling for the first and last 5000 points.
    The middle section includes any leftover points in a separate segment.

    Parameters:
    - data (numpy.ndarray): The input data array with shape (time_points, channels).
    - window_size (int): Number of samples per window.

    Returns:
    - list: A list of segmented windows (numpy arrays).
    """
    n_timepoints = data.shape[0]

    # Handle the first 5000 data points
    first_segment = data[:5000, :]
    n_first_windows = 5000 // window_size
    first_windows = [first_segment[i * window_size:(i + 1) * window_size, :] for i in range(n_first_windows)]

    # Handle the middle section
    middle_segment = data[5000:-5000, :]
    n_middle_windows = len(middle_segment) // window_size
    middle_windows = [middle_segment[i * window_size:(i + 1) * window_size, :] for i in range(n_middle_windows)]

    # Add the leftover points in the middle section as a separate window
    leftover_start = n_middle_windows * window_size
    if leftover_start < len(middle_segment):
        middle_windows.append(middle_segment[leftover_start:, :])

    # Handle the last 5000 data points
    last_segment = data[-5000:, :]
    n_last_windows = 5000 // window_size
    last_windows = [last_segment[i * window_size:(i + 1) * window_size, :] for i in range(n_last_windows)]

    # Combine all windows
    all_windows = first_windows + middle_windows + last_windows
    return all_windows


def calculate_correlation_matrix(data):
    n_channels = data.shape[1]
    # print(f"Number of channels after excluding the first column: {n_channels}")
    corr_matrix = np.zeros((n_channels, n_channels))
    for i, j in combinations(range(n_channels), 2):
        corr = pearsonr(data[:, i], data[:, j])[0]
        """
        The pearsonr function from the scipy.stats module calculates the Pearson
        correlation coefficient (𝑟) and the p-value for testing the null hypothesis
        that there is no linear correlation between two variables.

        The [0] at the end extracts only the correlation coefficient from the tuple
        returned by pearsonr. The p-value is ignored in this case.
        """
        corr_matrix[i, j] = corr_matrix[j, i] = abs(corr)
        """
             corr_matrix[i, j] = corr_matrix[j, i] = X 

        If the centrality is path based[X = 1/abs(corr)] or strength based[X = abs(corr)],since in our work,
        proposition is : if correlation assigns higher weight to an edge, the edge
        tends to contribute in shortest path scheme.
            path based centralities: closeness, betweenness
            strength based centralities: degree, eigen vector
        """
    np.fill_diagonal(corr_matrix, 0)
    return corr_matrix

def make_graphs(adj):
    g = Graph(directed=False)
    g.add_edge_list(np.transpose(np.triu(adj).nonzero()))


    remove_parallel_edges(g)

    edge_weights = g.new_edge_property('double')
    g.edge_properties["weight"] = edge_weights


    edge_weights.a=list(filter(lambda x: x >0, np.triu(adj).flatten()))


    return g

def edgeAdjM(G, weight=None):

    eN = G.num_edges()
    # Creates an edge adjacency null matrix
    edgeMatrix = np.zeros(shape=(eN,eN))

    if weight is None:
        for v in G.vertices():
            tempOut=G.get_out_edges(v, [G.edge_index])
            comb = combinations(tempOut[:,2],2)

            for tup in comb:
                edgeMatrix[tup[0],tup[1]]=1

    else:
        for v in G.vertices():
            tempOut=G.get_out_edges(v, [G.edge_index])
            comb = combinations(tempOut[:,2],2)

            for tup in comb:
                value=(weight.a[tup[0]]+weight.a[tup[1]])/2.
                edgeMatrix[tup[0],tup[1]]=value

    edgeMatrix=edgeMatrix+edgeMatrix.T

    return edgeMatrix


def edge_eigenvector_centrality(G, edgeMatrix, weight=None):
    #start_time = time.time()
    #edgeMatrix=edgeAdjM(g, weight=weight)
    #print("--- %s seconds ---" % (time.time() - start_time))

    try:
        eigenvalue, eigenvector = linalg.eigs(edgeMatrix.T, k=1, which='LR')
        #eigenvalue, eigenvector = linalg.eigsh(edgeMatrix.T, k=1, which='LA',maxiter=1)

    except sp.sparse.linalg.ArpackNoConvergence:
        return {}

    largest = eigenvector.flatten().real
    norm = np.sign(largest.sum())*np.linalg.norm(largest)
    cent_values=map(float,largest/norm)

    #print("--- %s seconds ---" % (time.time() - start_time))

    edge_eigenvector= G.new_edge_property('double', vals=cent_values)
    G.edge_properties["eigenvector"] = edge_eigenvector

    return edge_eigenvector


def edge_closeness_centrality2(G, weights=None):
    vertex_closeness=closeness(G, weight=weights, norm=False)

    edge_closeness = G.new_edge_property("double")
    G.edge_properties["edge_closeness"] = edge_closeness

    nE=G.num_edges()

    for e in G.edges():
        s=e.source()
        t=e.target()

        cs=vertex_closeness[s]
        ct=vertex_closeness[t]

        G.ep.edge_closeness[e]=(nE-1)*cs*ct*1./(cs+ct)

    return vertex_closeness,edge_closeness


def nn_centrality(G, weight='None'): #(nearest neighbour edge centrality)

    strength=G.degree_property_map('total',weight)
    degree=G.degree_property_map('total')

    nncent = G.new_edge_property("double")
    G.edge_properties["nncent"] = nncent

    nV=G.num_vertices()

    for e in G.edges():
        s=e.source()
        t=e.target()

        ds=degree[s]
        dt=degree[t]

        ss=strength[s]
        st=strength[t]
        w=G.ep.weight[e]

        G.ep.nncent[e]=(ss+st-2*w)/(abs(ss-st)+1)*w/(2*nV-4)

    return nncent


def calc_cent(G, cent):
    if cent=='B':
        G.ep.weight.a=1./G.ep.weight.a
        v,e=betweenness(G, weight=G.ep.weight)

    elif cent=='nn':
        v=G.degree_property_map('total',weight=G.ep.weight)
        e=nn_centrality(G, weight=G.ep.weight)

    elif cent=='E':
        v=eigenvector(G, weight=G.ep.weight)[1]
        eM=edgeAdjM(G,weight=G.ep.weight)
        e=edge_eigenvector_centrality(G,eM,weight=G.ep.weight)

    elif cent=='C':
        G.ep.weight.a=1./G.ep.weight.a
        v,e=edge_closeness_centrality2(G, weights=G.ep.weight)

    # Convert property maps to dictionaries
    v_dict = {int(vertex): v[vertex] for vertex in G.vertices()}
    e_dict = {(int(edge.source()), int(edge.target())): e[edge] for edge in G.edges()}
    return v_dict, e_dict

centrality_type = 'B'


# Process each input file
for file_path, correlation_output_dir in zip(eeg_file_paths, correlation_output_dirs):
    file_name = os.path.basename(file_path)
    print(f"Before processing {file_name}: segment_data is of type {type(segment_data)}")   # DEBUGGER

    base_name = os.path.splitext(file_name)[0]

    # Create correlation output directory for the current file
    os.makedirs(correlation_output_dir, exist_ok=True)

    # Load EEG data
    data = pd.read_csv(file_path, header=0, dtype=np.float64)
    channel_names = data.columns.values[1:]
    print(channel_names)
    data = data.iloc[:,1:].values  # Convert to NumPy array.since earlier I defined header=0, numpy array doesn't contain the first row.

    print("Type of data before segmenting:", type(data))
    print("Shape of data before segmenting:", data.shape)

    # Call to store the segmented data in 'windows'
    print(type(data))   # DEBUGGER: Ensure that data is consistently used as a NumPy array and not redefined as something else.

    # DEBUGGER: Check if the segment_data function is callable
    print(f"Is segment_data callable? {callable(segment_data)}")

    windows = segment_data(data, window_size)

    vertex_centrality_results = []
    edge_centrality_results = []
    correlation_matrices = []

    # for segment_idx, combined_window in enumerate(combined_windows):
    #     segment_data = combined_window   # The current segment is the combined window
    #     segment_length = segment_data.shape[0]  # Segment length is now dynamic, based on the combined window size

    for segment_idx, current_segment in enumerate(windows):  # Use `windows` directly
        segment_length = current_segment.shape[0]  # Length of the current segment

        # Calculate the correlation matrix for the current segment
        corr_matrix = calculate_correlation_matrix(current_segment)

        # Store correlation matrix with segment index
        correlation_matrices.append({
            'segment': segment_idx,
            'matrix': corr_matrix
        })

        # Create a graph from the correlation matrix
        G=make_graphs(corr_matrix)

 ###########################  CENTRALITY CALCULATION AND STORING PART ##############################
        # Calculate centralities
        vertex_centrality, edge_centrality=calc_cent(G,centrality_type)
        # print (vertex_centrality)

        # Store vertex centrality results
        vertex_centrality_dict = {'Segment': segment_idx}
        vertex_centrality_dict.update(vertex_centrality)
        vertex_centrality_results.append(vertex_centrality_dict)

        # Store edge centrality results
        edge_centrality_dict = {'Segment': segment_idx}
        edge_centrality_dict.update(edge_centrality)
        edge_centrality_results.append(edge_centrality_dict)

    ############################ Save correlation matrices ###########################
    print(f"Saving {len(correlation_matrices)} correlation matrices for subject {base_name}")
    for idx, corr_data in enumerate(correlation_matrices):
        segment_idx = corr_data['segment']
        corr_matrix = corr_data['matrix']

        corr_df = pd.DataFrame(corr_matrix, columns=channel_names, index=channel_names)
        output_file_path = os.path.join(correlation_output_dir, f'window_{segment_idx}_correlation.csv')
        corr_df.to_csv(output_file_path)
        print(f'Saved correlation matrix for window {segment_idx} to {output_file_path}')


##################### SAVING CENTRALITY TO CSVs ###################################
    # Save centrality results
    edge_centrality_df = pd.DataFrame(edge_centrality_results)
    edge_output_path = os.path.join(output_dir_edge, f'{base_name}_edge-betweenness.csv')
    edge_centrality_df.to_csv(edge_output_path, index=False)
    print(f'Saved edge centrality results to {edge_output_path}')

    vertex_centrality_df = pd.DataFrame(vertex_centrality_results)
    vertex_centrality_df.columns = ['Segment'] + list(channel_names)
    vertex_output_path = os.path.join(output_dir_vertex, f'{base_name}_vertex-betweenness.csv')
    vertex_centrality_df.to_csv(vertex_output_path, index=False)
    print(f'Saved vertex centrality results to {vertex_output_path}')
