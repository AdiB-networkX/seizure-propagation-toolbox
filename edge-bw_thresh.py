# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 11:53:42 2025
@author: Aditi Bose
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import re
import os
from collections import defaultdict
import math

class EpilepsyNetworkAnalyzer:
    def __init__(self):
        # Define colors for each edge type
        self.edge_colors = {
            'FF': '#8C000F',  # dark red
            'FN': '#D2691E',  # Orange
            'FO': '#FAC205',  # Yellow
            'NN': '#008080',  # teal blue
            'NO': '#04D8B2',  # turquoise blue
            'OO': '#808080'   # gray
            }
        
        # Define the order of edge types for plotting
        self.edge_type_order = ['FF', 'FN', 'FO', 'NN', 'NO', 'OO']
        
        # Storage for threshold calculation results
        self.threshold_results = {
            'subject_network_thresholds': {},  # subject -> network -> threshold_rank
            'subject_avg_thresholds': {},      # subject -> avg_threshold
            'identical_edges_info': {},        # subject -> network -> identical_edges_data
            'final_threshold': None
        }
        
    def load_vertex_centrality_csv(self, vertex_csv_path):
        """Load vertex centrality CSV and extract node names from column headers"""
        print(f"Loading vertex CSV: {vertex_csv_path}")
        try:
            df = pd.read_csv(vertex_csv_path)
            print(f"Vertex CSV shape: {df.shape}")
            print(f"Vertex CSV columns: {df.columns[:10].tolist()}...")  # Show first 10 columns
            # Node names start from second column (index 1)
            node_names = df.columns[1:].tolist()
            print(f"Found {len(node_names)} node names")
            return node_names
        except Exception as e:
            print(f"Error loading vertex CSV: {e}")
            raise
    

    def classify_nodes(self, node_names, is_right_case=True):
        """Classify nodes into F, N, O categories based on left/right case."""
        def classify_node(node, is_right_case):
            """Categorize node based on its alphabetical prefix and hemisphere."""
            alpha_part = ''.join(filter(str.isalpha, str(node))).upper()
    
            if is_right_case:
                if alpha_part == 'TR':
                    return 'F'  # Focus
                elif alpha_part in ['TBAR', 'TBPR']:
                    return 'N'  # Neighborhood
                else:
                    return 'O'  # Other
            else:
                if alpha_part == 'TL':
                    return 'F'  # Focus
                elif alpha_part in ['TBAL', 'TBPL']:
                    return 'N'  # Neighborhood
                else:
                    return 'O'  # Other
    
        node_classifications = {}
        for node_name in node_names:
            node_classifications[node_name] = classify_node(node_name, is_right_case)
        
        # Debug: Print classification summary
        classification_counts = {}
        for classification in node_classifications.values():
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
        print(f"Node classification counts: {classification_counts}")
        
        return node_classifications

    
    def parse_edge_name(self, edge_name):
        """Parse edge name in format (x,y) to extract node indices"""
        try:
            # Remove parentheses and split by comma
            edge_name = edge_name.strip('()')
            x, y = map(int, edge_name.split(','))
            return x, y
        except Exception as e:
            print(f"Error parsing edge name '{edge_name}': {e}")
            raise
    
    def get_edge_type(self, x, y, node_classifications, node_names):
        """Determine edge type (FF, FN, FO, NN, NO, OO) from node indices"""
        try:
            # Check if indices are valid
            if x >= len(node_names) or y >= len(node_names):
                print(f"Warning: Edge indices ({x}, {y}) exceed node list length ({len(node_names)})")
                return 'OO'  # Default to OO for invalid indices
                
            node_x = node_names[x]
            node_y = node_names[y]
            
            type_x = node_classifications[node_x]
            type_y = node_classifications[node_y]
            
            # Create edge type string (alphabetically sorted)
            edge_type = ''.join(sorted([type_x, type_y]))
            return edge_type
        except Exception as e:
            print(f"Error getting edge type for indices ({x}, {y}): {e}")
            return 'OO'  # Default fallback
    
    def extract_subject_name(self, csv_filename):
        """Extract subject name from CSV filename by removing specific patterns"""
        # Get just the filename without path
        filename = os.path.basename(csv_filename)
        # Remove '[ranked]' prefix if present
        if filename.startswith('[ranked]'):
            filename = filename[8:]  # Remove '[ranked]'
        
        # Extract the pattern like '028b_RMT' or '029b_RMT'
        # Look for pattern: digits + letter + '_RMT' or '_LMT'
        pattern = r'(\d+[a-z]+_[RL]MT)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
        else:
            # Fallback: remove file extension
            return os.path.splitext(filename)[0]
    
    def create_stacked_network_plot_with_masking(self, ranked_edge_csv_path, values_edge_csv_path, 
                                               vertex_csv_path, is_right_case, selected_networks, 
                                               output_base_dir='stacked_plots', mask_opacity=0.7):
        """Create single stacked plot with all networks vertically arranged and white masking for zero values"""
        # Extract subject name from filename
        subject_name = self.extract_subject_name(ranked_edge_csv_path)
        
        # Create main output directory if it doesn't exist
        os.makedirs(output_base_dir, exist_ok=True)
        
        print(f"\nProcessing stacked plot with masking for {subject_name}...")
        print(f"Selected networks: {selected_networks}")
        
        # Load data with debugging
        print("Loading ranked edge CSV...")
        ranked_edge_df = pd.read_csv(ranked_edge_csv_path)
        print(f"Ranked edge CSV shape: {ranked_edge_df.shape}")
        print(f"First column (network IDs): {ranked_edge_df.iloc[:, 0].tolist()[:10]}...")
        
        print("Loading values edge CSV...")
        values_edge_df = pd.read_csv(values_edge_csv_path)
        print(f"Values edge CSV shape: {values_edge_df.shape}")
        
        print("Loading node names...")
        node_names = self.load_vertex_centrality_csv(vertex_csv_path)
        
        # Classify nodes
        print("Classifying nodes...")
        node_classifications = self.classify_nodes(node_names, is_right_case)
        
        # Get edge names from column headers
        edge_names = ranked_edge_df.columns[1:].tolist()
        print(f"Found {len(edge_names)} edge names")
        print(f"First few edge names: {edge_names[:5]}")
        
        # Process all selected networks and collect data
        all_networks_data = []
        max_edges = 0
        
        for network_num in selected_networks:
            print(f"Processing network {network_num}...")
            
            # Get the row for this network from both dataframes
            ranked_network_row = ranked_edge_df[ranked_edge_df.iloc[:, 0] == network_num]
            values_network_row = values_edge_df[values_edge_df.iloc[:, 0] == network_num]
            
            if ranked_network_row.empty:
                print(f"Warning: Network {network_num} not found in ranked CSV")
                continue
            if values_network_row.empty:
                print(f"Warning: Network {network_num} not found in values CSV")
                continue
            
            # Get centrality ranks and values for this network
            centrality_ranks = ranked_network_row.iloc[0, 1:].values
            centrality_values = values_network_row.iloc[0, 1:].values
            
            print(f"Network {network_num}: {len(centrality_ranks)} ranks, {len(centrality_values)} values")
            print(f"Sample ranks: {centrality_ranks[:5]}")
            print(f"Sample values: {centrality_values[:5]}")
            
            # Create list of (rank, edge_name, edge_type, value) tuples
            edge_data = []
            for i, (edge_name, rank, value) in enumerate(zip(edge_names, centrality_ranks, centrality_values)):
                try:
                    # Skip if rank or value is NaN
                    if pd.isna(rank) or pd.isna(value):
                        continue
                        
                    x, y = self.parse_edge_name(edge_name)
                    edge_type = self.get_edge_type(x, y, node_classifications, node_names)
                    edge_data.append((rank, edge_name, edge_type, value))
                except Exception as e:
                    print(f"Error processing edge {edge_name}: {e}")
                    continue
            
            print(f"Network {network_num}: Successfully processed {len(edge_data)} edges")
            
            # Sort edges by rank (ascending order)
            edge_data.sort(key=lambda x: x[0])
            
            all_networks_data.append({
                'network_num': network_num,
                'edge_data': edge_data
            })
            
            # Track maximum number of edges for consistent plot width
            max_edges = max(max_edges, len(edge_data))
        
        print(f"Total networks processed: {len(all_networks_data)}")
        print(f"Maximum edges across networks: {max_edges}")
        
        if len(all_networks_data) == 0:
            print("ERROR: No network data found! Check your selected_networks list and CSV files.")
            return
        
        if max_edges == 0:
            print("ERROR: No edges found in any network!")
            return
        
        # Create stacked plot with masking
        self.create_stacked_matshow_plot_with_masking(all_networks_data, max_edges, subject_name, 
                                                    output_base_dir, mask_opacity)
    
    def create_stacked_matshow_plot_with_masking(self, all_networks_data, max_edges, subject_name, 
                                               output_dir, mask_opacity):
        """Create stacked matshow plot for all networks with white masking for zero values"""
        num_networks = len(all_networks_data)
        
        print(f"Creating plot for {num_networks} networks with max {max_edges} edges")
        
        # COMPLETELY CLEAR any existing plots first
        plt.close('all')
        
        # Create figure with appropriate height
        fig_height = max(4, num_networks * 0.8)
        fig = plt.figure(figsize=(16, fig_height))
        
        # Create mapping from edge type to numeric value
        edge_type_to_num = {edge_type: i for i, edge_type in enumerate(self.edge_type_order)}
        
        # Create 2D arrays for matshow and masking
        plot_array = np.full((num_networks, max_edges), -1, dtype=int)  # -1 for empty cells
        mask_array = np.zeros((num_networks, max_edges), dtype=bool)  # False for normal cells
        
        # Collect edge type counts across all networks for legend
        overall_edge_type_counts = {edge_type: 0 for edge_type in self.edge_type_order}
        
        # Track unique edges for counting
        seen_edges = set()
        
        # Fill the arrays with edge type data and masking info
        for row_idx, network_data in enumerate(all_networks_data):
            edge_data = network_data['edge_data']
            print(f"Processing network {network_data['network_num']} (row {row_idx}) with {len(edge_data)} edges")
            
            # Find where zero values start
            zero_found = False
            for col_idx, (rank, edge_name, edge_type, value) in enumerate(edge_data):
                if col_idx < max_edges:
                    plot_array[row_idx, col_idx] = edge_type_to_num[edge_type]
                    
                    # Mark for masking if value is zero or zero already found
                    if value == 0 or zero_found:
                        mask_array[row_idx, col_idx] = True
                        zero_found = True
                    
                    # Count only unique edges (and only non-masked ones for accurate counting)
                    if edge_name not in seen_edges and not mask_array[row_idx, col_idx]:
                        overall_edge_type_counts[edge_type] += 1
                        seen_edges.add(edge_name)

        print(f"Plot array shape: {plot_array.shape}")
        print(f"Plot array sample:\n{plot_array[:3, :10]}")
        print(f"Edge type counts: {overall_edge_type_counts}")

        # Create custom colormap including white for empty cells
        colors_list = ['white'] + [self.edge_colors[edge_type] for edge_type in self.edge_type_order]
        custom_cmap = ListedColormap(colors_list)
        
        # Create the main plot
        ax = plt.gca()
        im = ax.matshow(plot_array, cmap=custom_cmap, aspect='auto', vmin=-1, vmax=5)
        
        # Add white mask for zero values
        white_mask = np.ma.masked_where(~mask_array, np.ones_like(mask_array))
        ax.matshow(white_mask, cmap='gray', alpha=mask_opacity, aspect='auto', vmin=0, vmax=1)
        
        # Set y-axis labels with network numbers
        network_labels = []
        for i, data in enumerate(all_networks_data):
            if i == 0:  # First row (index 0)
                network_labels.append('pre szr')
            elif i == 2:  # Third row (index 2)
                network_labels.append('szr')
            elif i == 10:  # Eleventh row (index 10)
                network_labels.append('post szr')
            else:
                network_labels.append('')
        
        ax.set_yticks(range(num_networks))
        ax.set_yticklabels(network_labels, fontsize=10)
        
        # Set labels
        ax.set_xlabel('edge betweenness centrality (decreases →)', fontsize=12)
        ax.set_ylabel('networks', fontsize=12)
        ax.set_title(f'Edge Centrality Distribution - {subject_name}', fontsize=14)
        
        # Create custom legend with colored rectangles
        legend_elements = []
        for edge_type in self.edge_type_order:
            if overall_edge_type_counts[edge_type] > 0:
                legend_elements.append(patches.Rectangle((0, 0), 1, 1, 
                                                       facecolor=self.edge_colors[edge_type], 
                                                       label=f"{edge_type} ({overall_edge_type_counts[edge_type]})"))
        
        if legend_elements:
            ax.legend(handles=legend_elements, title='edge class \n(total nonzero count)', 
                     bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Save plot using subject name as filename with masking suffix
        output_path = os.path.join(output_dir, f'{subject_name}_with_values.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Saved stacked plot with masking: {output_path}")
        
        # Close the figure after saving to prevent interference with next plot
        plt.close()
        
    def find_identical_values_threshold(self, edge_data, network_num, subject_name):
        """
        Find the rank threshold where identical centrality values start appearing at the end
        Args:
            edge_data: list of (rank, edge_name, edge_type, value) tuples, sorted by rank
            network_num: network identifier
            subject_name: subject identifier
        Returns:
            threshold_rank: rank after which identical values start (or None if no pattern found)
        """
        if len(edge_data) == 0:
            return None, None
            
        # Filter out zero values first
        nonzero_edges = [(rank, edge_name, edge_type, value) for rank, edge_name, edge_type, value in edge_data if value != 0]
        
        if len(nonzero_edges) <= 1:
            return None, None
            
        print(f"  Network {network_num}: {len(nonzero_edges)} non-zero edges out of {len(edge_data)} total edges")
        
        # Look for identical values at the end
        # Start from the end and work backwards to find where identical values begin
        last_value = nonzero_edges[-1][3]  # value is at index 3
        identical_count = 1
        threshold_idx = len(nonzero_edges) - 1
        
        # Count how many edges at the end have the same value as the last edge
        for i in range(len(nonzero_edges) - 2, -1, -1):
            if nonzero_edges[i][3] == last_value:
                identical_count += 1
                threshold_idx = i
            else:
                break
        
        print(f"  Network {network_num}: Found {identical_count} edges with identical value {last_value} at the end")
        
        # Only consider it a threshold if we have more than 2 identical values at the end
        # This avoids cutting off meaningful data when there are just 2 identical values
        if identical_count > 2:
            threshold_rank = nonzero_edges[threshold_idx][0]  # rank is at index 0
            print(f"  Network {network_num}: Threshold rank = {threshold_rank}")
            
            # Store detailed information about identical edges
            identical_edges_data = {
                'identical_count': identical_count,
                'identical_value': last_value,
                'threshold_rank': threshold_rank,
                'edges_info': nonzero_edges[threshold_idx:]
            }
            return threshold_rank, identical_edges_data
        else:
            print(f"  Network {network_num}: No significant identical pattern found (only {identical_count} identical values)")
            return None, None

    def calculate_threshold_for_subject(self, ranked_edge_csv_path, values_edge_csv_path, 
                                      vertex_csv_path, is_right_case, selected_networks):
        """Calculate threshold for a single subject across all networks"""
        # Extract subject name
        subject_name = self.extract_subject_name(ranked_edge_csv_path)
        print(f"\n{'='*50}")
        print(f"CALCULATING THRESHOLD FOR SUBJECT: {subject_name}")
        print(f"{'='*50}")
        
        # Load data
        ranked_edge_df = pd.read_csv(ranked_edge_csv_path)
        values_edge_df = pd.read_csv(values_edge_csv_path)
        node_names = self.load_vertex_centrality_csv(vertex_csv_path)
        node_classifications = self.classify_nodes(node_names, is_right_case)
        
        # Get edge names from column headers
        edge_names = ranked_edge_df.columns[1:].tolist()
        
        # Initialize storage for this subject
        self.threshold_results['subject_network_thresholds'][subject_name] = {}
        self.threshold_results['identical_edges_info'][subject_name] = {}
        
        network_thresholds = []
        
        # Process each selected network
        for network_num in selected_networks:
            print(f"\nProcessing network {network_num}...")
            
            # Get the row for this network from both dataframes
            ranked_network_row = ranked_edge_df[ranked_edge_df.iloc[:, 0] == network_num]
            values_network_row = values_edge_df[values_edge_df.iloc[:, 0] == network_num]
            
            if ranked_network_row.empty or values_network_row.empty:
                print(f"Warning: Network {network_num} not found in CSV files")
                continue
            
            # Get centrality ranks and values for this network
            centrality_ranks = ranked_network_row.iloc[0, 1:].values
            centrality_values = values_network_row.iloc[0, 1:].values
            
            # Create list of (rank, edge_name, edge_type, value) tuples
            edge_data = []
            for i, (edge_name, rank, value) in enumerate(zip(edge_names, centrality_ranks, centrality_values)):
                try:
                    # Skip if rank or value is NaN
                    if pd.isna(rank) or pd.isna(value):
                        continue
                        
                    x, y = self.parse_edge_name(edge_name)
                    edge_type = self.get_edge_type(x, y, node_classifications, node_names)
                    edge_data.append((rank, edge_name, edge_type, value))
                except Exception as e:
                    continue
            
            # Sort edges by rank (ascending order)
            edge_data.sort(key=lambda x: x[0])
            
            # Find threshold for this network
            threshold_result = self.find_identical_values_threshold(edge_data, network_num, subject_name)
            
            if threshold_result[0] is not None:
                threshold_rank, identical_edges_data = threshold_result
                network_thresholds.append(threshold_rank)
                self.threshold_results['subject_network_thresholds'][subject_name][network_num] = threshold_rank
                self.threshold_results['identical_edges_info'][subject_name][network_num] = identical_edges_data
            else:
                print(f"  Network {network_num}: No threshold found")
                self.threshold_results['subject_network_thresholds'][subject_name][network_num] = None
                self.threshold_results['identical_edges_info'][subject_name][network_num] = None
        
        # Calculate average threshold for this subject
        if network_thresholds:
            avg_threshold = np.mean(network_thresholds)
            floor_avg_threshold = math.floor(avg_threshold)
            self.threshold_results['subject_avg_thresholds'][subject_name] = floor_avg_threshold
            
            print(f"\nSUBJECT {subject_name} SUMMARY:")
            print(f"Valid network thresholds: {network_thresholds}")
            print(f"Average threshold: {avg_threshold:.2f}")
            print(f"Floor of average threshold: {floor_avg_threshold}")
        else:
            print(f"\nSUBJECT {subject_name}: No valid thresholds found")
            self.threshold_results['subject_avg_thresholds'][subject_name] = None
        
        return floor_avg_threshold if network_thresholds else None
    
    def calculate_final_threshold(self, ranked_edge_csv_list, values_edge_csv_list, 
                                vertex_csv_list, is_right_case_list, selected_networks_list):
        """Calculate final threshold across all subjects"""
        print(f"\n{'='*70}")
        print(f"CALCULATING FINAL THRESHOLD ACROSS ALL SUBJECTS")
        print(f"{'='*70}")
        
        subject_avg_thresholds = []
        
        # Process each subject
        for i in range(len(ranked_edge_csv_list)):
            subject_threshold = self.calculate_threshold_for_subject(
                ranked_edge_csv_list[i],
                values_edge_csv_list[i],
                vertex_csv_list[i],
                is_right_case_list[i],
                selected_networks_list[i]
            )
            
            if subject_threshold is not None:
                subject_avg_thresholds.append(subject_threshold)
        
        # Calculate final threshold
        if subject_avg_thresholds:
            final_threshold = np.mean(subject_avg_thresholds)
            self.threshold_results['final_threshold'] = final_threshold
            
            print(f"\n{'='*70}")
            print(f"FINAL THRESHOLD CALCULATION RESULTS")
            print(f"{'='*70}")
            print(f"Subject average thresholds: {subject_avg_thresholds}")
            print(f"Final threshold (average across subjects): {final_threshold:.2f}")
            print(f"{'='*70}")
            
            return final_threshold
        else:
            print(f"ERROR: No valid subject thresholds found!")
            return None
    
    def print_detailed_threshold_results(self):
        """Print detailed results of threshold calculation"""
        print(f"\n{'='*80}")
        print(f"DETAILED THRESHOLD CALCULATION RESULTS")
        print(f"{'='*80}")
        
        for subject_name in self.threshold_results['subject_network_thresholds']:
            print(f"\nSUBJECT: {subject_name}")
            print(f"-" * 40)
            
            network_thresholds = self.threshold_results['subject_network_thresholds'][subject_name]
            identical_info = self.threshold_results['identical_edges_info'][subject_name]
            
            for network_num in sorted(network_thresholds.keys()):
                threshold = network_thresholds[network_num]
                if threshold is not None:
                    info = identical_info[network_num]
                    print(f"Network {network_num:2d}: Threshold rank = {threshold:3.0f}, "
                          f"Identical edges = {info['identical_count']:2d}, "
                          f"Identical value = {info['identical_value']:.6f}")
                else:
                    print(f"Network {network_num:2d}: No threshold found")
            
            subject_avg = self.threshold_results['subject_avg_thresholds'][subject_name]
            if subject_avg is not None:
                print(f"Subject average threshold: {subject_avg}")
            else:
                print(f"Subject average threshold: None")
        
        final_threshold = self.threshold_results['final_threshold']
        print(f"\nFINAL THRESHOLD ACROSS ALL SUBJECTS: {final_threshold:.2f}")
        
    def get_results_for_variable_explorer(self):
        """Return all results in a format suitable for variable explorer"""
        return {
            'threshold_results': self.threshold_results,
            'subject_network_thresholds': self.threshold_results['subject_network_thresholds'],
            'subject_avg_thresholds': self.threshold_results['subject_avg_thresholds'],
            'identical_edges_info': self.threshold_results['identical_edges_info'],
            'final_threshold': self.threshold_results['final_threshold']
        }


# Function to create stacked plots with masking for multiple CSV files
def create_stacked_plots_with_masking_for_multiple_csvs(ranked_edge_csv_list, values_edge_csv_list, 
                                                      vertex_csv_list, is_right_case_list, 
                                                      selected_networks_list, output_base_dir='stacked_plots',
                                                      mask_opacity=0.7):
    
    analyzer = EpilepsyNetworkAnalyzer()
    
    # Validate input lists
    lists_to_check = [ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list, 
                     is_right_case_list, selected_networks_list]
    
    if not all(len(lst) == len(ranked_edge_csv_list) for lst in lists_to_check):
        raise ValueError("All input lists must have the same length!")
    
    print(f"Processing {len(ranked_edge_csv_list)} CSV files...")
    
    # Process all CSV files
    for i in range(len(ranked_edge_csv_list)):
        print(f"\n{'='*60}")
        print(f"Processing CSV file {i+1}/{len(ranked_edge_csv_list)}...")
        print(f"Ranked CSV: {os.path.basename(ranked_edge_csv_list[i])}")
        print(f"Values CSV: {os.path.basename(values_edge_csv_list[i])}")
        print(f"Vertex CSV: {os.path.basename(vertex_csv_list[i])}")
        print(f"Is right case: {is_right_case_list[i]}")
        print(f"Selected networks: {selected_networks_list[i]}")
        
        try:
            analyzer.create_stacked_network_plot_with_masking(
                ranked_edge_csv_list[i],
                values_edge_csv_list[i],
                vertex_csv_list[i],
                is_right_case_list[i],
                selected_networks_list[i],
                output_base_dir,
                mask_opacity
            )
        except Exception as e:
            subject_name = analyzer.extract_subject_name(ranked_edge_csv_list[i])
            print(f"ERROR processing {subject_name}: {e}")
            import traceback
            traceback.print_exc()


# Function to create stacked plot with masking for single CSV file
def create_stacked_plot_with_masking_single_csv(ranked_edge_csv_path, values_edge_csv_path, 
                                              vertex_csv_path, is_right_case, selected_networks, 
                                              output_base_dir='stacked_plots', mask_opacity=0.7):
    analyzer = EpilepsyNetworkAnalyzer()
    
    print(f"Processing single CSV file...")
    print(f"Ranked CSV: {os.path.basename(ranked_edge_csv_path)}")
    print(f"Values CSV: {os.path.basename(values_edge_csv_path)}")
    print(f"Vertex CSV: {os.path.basename(vertex_csv_path)}")
    print(f"Is right case: {is_right_case}")
    print(f"Selected networks: {selected_networks}")
    
    try:
        analyzer.create_stacked_network_plot_with_masking(
            ranked_edge_csv_path, values_edge_csv_path, vertex_csv_path, 
            is_right_case, selected_networks, output_base_dir, mask_opacity
        )
    except Exception as e:
        subject_name = analyzer.extract_subject_name(ranked_edge_csv_path)
        print(f"ERROR processing {subject_name}: {e}")
        import traceback
        traceback.print_exc()


def calculate_threshold_only(ranked_edge_csv_list, values_edge_csv_list, 
                           vertex_csv_list, is_right_case_list, selected_networks_list):
    """Function to calculate threshold without creating plots"""
    analyzer = EpilepsyNetworkAnalyzer()
    
    # Validate input lists
    lists_to_check = [ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list, 
                     is_right_case_list, selected_networks_list]
    
    if not all(len(lst) == len(ranked_edge_csv_list) for lst in lists_to_check):
        raise ValueError("All input lists must have the same length!")
    
    print(f"Calculating threshold for {len(ranked_edge_csv_list)} subjects...")
    
    # Calculate final threshold
    final_threshold = analyzer.calculate_final_threshold(
        ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list,
        is_right_case_list, selected_networks_list
    )
    
    # Print detailed results
    analyzer.print_detailed_threshold_results()
    
    return analyzer, final_threshold

# Example usage - Create stacked plots with masking for multiple CSV files
def main():
    # Check if files exist first
    def check_file_exists(filepath):
        if not os.path.exists(filepath):
            print(f"WARNING: File does not exist: {filepath}")
            return False
        return True
    
    ##### betweenness #####
    # edge CSV files (centrality ranks)
    ranked_edge_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness-ranked/generalised/[ranked]011a_LMT_no-ref-ch_edge-betweenness-centrality.csv",
   ]   
    # edge CSV files (actual centrality values)
    values_edge_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness/generalised/011a_LMT_no-ref-ch_edge-betweenness-centrality.csv",
    ]
    # vertex CSV files - for node classification - (centrality ranks)
    vertex_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/vertex-betweenness-ranked/generalised/[ranked]011a_LMT_no-ref-ch_vertex-betweenness-centrality.csv",
    ]

    is_right_case_list = [
       False     # S18 = 011a_LMT 
    ]
    
    selected_networks_list = [
        [1,8,12,15,24,26,32,39,41,45,55,64],    # S18 = 011a_LMT 
    ]
    
    # Check if all files exist
    print("Checking file paths...")
    all_files = ranked_edge_csv_list + values_edge_csv_list + vertex_csv_list
    missing_files = [f for f in all_files if not check_file_exists(f)]
    
    if missing_files:
        print(f"ERROR: {len(missing_files)} files are missing!")
        return
        
    print("All files found!")
    
    # CALCULATE THRESHOLD ONLY
    print("\n" + "="*80)
    print("CALCULATING THRESHOLD FOR BETWEENNESS CENTRALITY")
    print("="*80)
    
    analyzer, final_threshold = calculate_threshold_only(
        ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list,
        is_right_case_list, selected_networks_list
    )
    
    # Store results in variable explorer
    results_dict = analyzer.get_results_for_variable_explorer()
    globals().update(results_dict)
    
    # Access stored results
    print(f"\nSTORED RESULTS:")
    print(f"Final threshold: {analyzer.threshold_results['final_threshold']}")
    print(f"Subject average thresholds: {analyzer.threshold_results['subject_avg_thresholds']}")
    print(f"All network thresholds stored in: analyzer.threshold_results['subject_network_thresholds']")
    print(f"Identical edges info stored in: analyzer.threshold_results['identical_edges_info']")
    
    # Optionally create plots as well
    # Uncomment the lines below if you also want to create the plots
    # Specify your main output directory
    main_output_dir = "C:/Users/Aditi Bose/OneDrive - IIIT Hyderabad/IIITH-PhD/Research-works/EEG-epilepsy-UKB/Universitätsklinikum Bonn/codes-outputs-plots_v1/Codes-for-submission2025_science-advances/edge-cent-threshold"
    
    # Create stacked plots with masking for all subjects
    create_stacked_plots_with_masking_for_multiple_csvs(
        ranked_edge_csv_list,
        values_edge_csv_list,
        vertex_csv_list, 
        is_right_case_list,
        selected_networks_list,
        output_base_dir=main_output_dir,
        mask_opacity=0.7
    )

if __name__ == "__main__":
    main()

