# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 12:02:31 2025
@author: Aditi Bose
"""

import pandas as pd
import numpy as np
import re
import os
from collections import defaultdict
import math

class EpilepsyNetworkAnalyzer:
    def __init__(self):
        # Define the order of edge types for analysis
        self.edge_type_order = ['FF', 'FN', 'NN', 'FO', 'NO', 'OO']
        
        # Storage for segmentation results
        self.segmentation_results = {
            'subject_network_segments': {},  # subject -> network -> segment -> edge_type_counts
            'threshold_used': None
        }
        
    def load_vertex_centrality_csv(self, vertex_csv_path):
        """Load vertex centrality CSV and extract node names from column headers"""
        print(f"Loading vertex CSV: {vertex_csv_path}")
        try:
            df = pd.read_csv(vertex_csv_path)
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

    def segment_edges_by_threshold(self, ranked_edge_csv_path, values_edge_csv_path, 
                                 vertex_csv_path, is_right_case, selected_networks, 
                                 threshold_value):
        """
        Extract edges within threshold and segment them into 4 parts for each network
        
        Args:
            ranked_edge_csv_path: Path to ranked edge CSV
            values_edge_csv_path: Path to values edge CSV
            vertex_csv_path: Path to vertex CSV
            is_right_case: Boolean for hemisphere classification
            selected_networks: List of network numbers to analyze
            threshold_value: Threshold rank value for edge selection
        """
        # Extract subject name
        subject_name = self.extract_subject_name(ranked_edge_csv_path)
        
        print(f"\n{'='*50}")
        print(f"PROCESSING SUBJECT: {subject_name}")
        print(f"Threshold value: {threshold_value}")
        print(f"{'='*50}")
        
        # Load data
        print("Loading data...")
        ranked_edge_df = pd.read_csv(ranked_edge_csv_path)
        values_edge_df = pd.read_csv(values_edge_csv_path)
        node_names = self.load_vertex_centrality_csv(vertex_csv_path)
        node_classifications = self.classify_nodes(node_names, is_right_case)
        
        # Get edge names from column headers
        edge_names = ranked_edge_df.columns[1:].tolist()
        print(f"Found {len(edge_names)} edge names")
        
        # Initialize storage for this subject
        self.segmentation_results['subject_network_segments'][subject_name] = {}
        
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
            
            # Filter edges within threshold and with non-zero values
            filtered_edges = [
                (rank, edge_name, edge_type, value) 
                for rank, edge_name, edge_type, value in edge_data 
                if rank <= threshold_value and value != 0
            ]
            
            print(f"  Network {network_num}: {len(filtered_edges)} edges within threshold (out of {len(edge_data)} total)")
            
            if len(filtered_edges) == 0:
                print(f"  Network {network_num}: No edges within threshold, skipping...")
                continue
            
            # Divide into 4 equal segments
            segment_results = self.divide_into_segments(filtered_edges, network_num)
            
            # Store results for this network
            self.segmentation_results['subject_network_segments'][subject_name][network_num] = segment_results
        
        print(f"\nCompleted processing subject: {subject_name}")

    
    def divide_into_segments(self, filtered_edges, network_num):
        """
        Divide filtered edges into 4 equal segments and count edge types in each segment.
        All remainder edges go to the fourth bin only.
        
        Args:
            filtered_edges: List of (rank, edge_name, edge_type, value) tuples
            network_num: Network identifier
            
        Returns:
            Dictionary with segment results
        """
        num_edges = len(filtered_edges)
        segment_size = num_edges // 4
        remainder = num_edges % 4
        
        print(f"    Dividing {num_edges} edges into 4 segments (base size: {segment_size}, remainder: {remainder})")
        
        segments = {}
        start_idx = 0
        
        for segment_num in range(1, 5):  # Segments 1, 2, 3, 4
            # Calculate segment size - only segment 4 gets the remainder
            if segment_num == 4:
                current_segment_size = segment_size + remainder
            else:
                current_segment_size = segment_size
            
            end_idx = start_idx + current_segment_size
            
            # Extract edges for this segment
            segment_edges = filtered_edges[start_idx:end_idx]
            
            # Count edge types in this segment
            edge_type_counts = {edge_type: 0 for edge_type in self.edge_type_order}
            
            for rank, edge_name, edge_type, value in segment_edges:
                edge_type_counts[edge_type] += 1
            
            # Store segment results
            segments[segment_num] = {
                'edge_count': len(segment_edges),
                'rank_range': (segment_edges[0][0], segment_edges[-1][0]) if segment_edges else (None, None),
                'edge_type_counts': edge_type_counts,
                'edges': segment_edges  # Store actual edges for reference
            }
            
            print(f"      Segment {segment_num}: {len(segment_edges)} edges, "
                  f"ranks {segments[segment_num]['rank_range'][0]:.1f}-{segments[segment_num]['rank_range'][1]:.1f}, "
                  f"types: {dict(edge_type_counts)}")
            
            start_idx = end_idx
        
        return segments

    def process_all_subjects(self, ranked_edge_csv_list, values_edge_csv_list, 
                           vertex_csv_list, is_right_case_list, selected_networks_list, 
                           threshold_value):
        """
        Process all subjects with the given threshold value
        
        Args:
            All input lists for multiple subjects
            threshold_value: Single threshold value to apply to all subjects
        """
        # Store threshold used
        self.segmentation_results['threshold_used'] = threshold_value
        
        # Validate input lists
        lists_to_check = [ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list, 
                         is_right_case_list, selected_networks_list]
        
        if not all(len(lst) == len(ranked_edge_csv_list) for lst in lists_to_check):
            raise ValueError("All input lists must have the same length!")
        
        print(f"Processing {len(ranked_edge_csv_list)} subjects with threshold: {threshold_value}")
        
        # Process each subject
        for i in range(len(ranked_edge_csv_list)):
            try:
                self.segment_edges_by_threshold(
                    ranked_edge_csv_list[i],
                    values_edge_csv_list[i],
                    vertex_csv_list[i],
                    is_right_case_list[i],
                    selected_networks_list[i],
                    threshold_value
                )
            except Exception as e:
                subject_name = self.extract_subject_name(ranked_edge_csv_list[i])
                print(f"ERROR processing {subject_name}: {e}")
                import traceback
                traceback.print_exc()

    def print_segmentation_summary(self):
        """Print summary of segmentation results"""
        print(f"\n{'='*80}")
        print(f"SEGMENTATION RESULTS SUMMARY")
        print(f"Threshold used: {self.segmentation_results['threshold_used']}")
        print(f"{'='*80}")
        
        for subject_name in self.segmentation_results['subject_network_segments']:
            print(f"\nSUBJECT: {subject_name}")
            print(f"-" * 50)
            
            subject_data = self.segmentation_results['subject_network_segments'][subject_name]
            
            for network_num in sorted(subject_data.keys()):
                network_data = subject_data[network_num]
                print(f"\n  Network {network_num}:")
                
                for segment_num in range(1, 5):
                    if segment_num in network_data:
                        segment_info = network_data[segment_num]
                        edge_counts = segment_info['edge_type_counts']
                        rank_range = segment_info['rank_range']
                        
                        print(f"    Segment {segment_num}: {segment_info['edge_count']} edges, "
                              f"ranks {rank_range[0]:.1f}-{rank_range[1]:.1f}")
                        print(f"      Edge types: {dict(edge_counts)}")

    def get_segmentation_results(self):
        """Return segmentation results for variable explorer"""
        return self.segmentation_results

    def export_results_to_csv(self, output_path):
        """Export segmentation results to CSV file"""
        results_data = []
        
        for subject_name in self.segmentation_results['subject_network_segments']:
            subject_data = self.segmentation_results['subject_network_segments'][subject_name]
            
            for network_num in subject_data:
                network_data = subject_data[network_num]
                
                for segment_num in range(1, 5):
                    if segment_num in network_data:
                        segment_info = network_data[segment_num]
                        edge_counts = segment_info['edge_type_counts']
                        rank_range = segment_info['rank_range']
                        
                        row_data = {
                            'subject': subject_name,
                            'network': network_num,
                            'segment': segment_num,
                            'total_edges': segment_info['edge_count'],
                            'rank_min': rank_range[0],
                            'rank_max': rank_range[1],
                            'FF': edge_counts['FF'],
                            'FN': edge_counts['FN'],
                            'NN': edge_counts['NN'],
                            'FO': edge_counts['FO'],
                            'NO': edge_counts['NO'],
                            'OO': edge_counts['OO']
                        }
                        results_data.append(row_data)
        
        # Create DataFrame and save to CSV
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(output_path, index=False)
        print(f"Results exported to: {output_path}")
        
        return results_df


def analyze_edge_segments_with_threshold(ranked_edge_csv_list, values_edge_csv_list, 
                                       vertex_csv_list, is_right_case_list, 
                                       selected_networks_list, threshold_value, 
                                       output_csv_path=None):
    """
    Main function to analyze edge segments with a given threshold
    
    Args:
        All the input lists for multiple subjects
        threshold_value: The centrality rank threshold to use
        output_csv_path: Optional path to save results as CSV
        
    Returns:
        EpilepsyNetworkAnalyzer instance with results
    """
    analyzer = EpilepsyNetworkAnalyzer()
    
    # Process all subjects
    analyzer.process_all_subjects(
        ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list,
        is_right_case_list, selected_networks_list, threshold_value
    )
    
    # Print summary
    analyzer.print_segmentation_summary()
    
    # Export to CSV if path provided
    if output_csv_path:
        analyzer.export_results_to_csv(output_csv_path)
    
    return analyzer


# Example usage
def main():
    ##### betweenness #####
    # edge CSV files (centrality ranks)
    ranked_edge_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness-ranked/generalised/[ranked]011a_LMT_no-ref-ch_edge-betweenness-centrality.csv"
    ]   
    # edge CSV files (actual centrality values)
    values_edge_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness/generalised/011a_LMT_no-ref-ch_edge-betweenness-centrality.csv"
    ]
    # vertex CSV files - for node classification - (centrality ranks)
    vertex_csv_list = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/vertex-betweenness-ranked/generalised/[ranked]011a_LMT_no-ref-ch_vertex-betweenness-centrality.csv"
    ]

    is_right_case_list = [  
       False    # S18 = 011a_LMT
    ]
    
    selected_networks_list = [
        [1,8,12,15,24,26,32,39,41,45,55,64]     # S18 = 011a_LMT
    ]
    
    # Set your threshold value 
    """
    threshold obtained from code: threshold-determination-from-edge-bw-[annotated]edge-centrality-distribution_12nws.py
    actual threshold is= 76.75, floor value is retained.
    """
    threshold_value = 76
    
    # Optional: specify output CSV path
    output_csv_path = "C:/Users/Aditi Bose/OneDrive - IIIT Hyderabad/IIITH-PhD/Research-works/EEG-epilepsy-UKB/Universitätsklinikum Bonn/codes-outputs-plots_v1/Codes-for-submission2025_science-advances/coarse-graining-of-top-MIEs/edge-bw.csv"
    
    # Run the analysis
    analyzer = analyze_edge_segments_with_threshold(
        ranked_edge_csv_list, values_edge_csv_list, vertex_csv_list,
        is_right_case_list, selected_networks_list, threshold_value,
        output_csv_path
    )
    
    # Access results
    results = analyzer.get_segmentation_results()
    print(f"\nResults stored in analyzer.segmentation_results")
    print(f"Access subject data: analyzer.segmentation_results['subject_network_segments']")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()