# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 14:53:14 2025
Modified to:
1. Use colormap for edge colors
2. Make each bar height equal to cell height
3. Create two plots: fixed order and descending order by count
4. Fixed y-axis ticks positioning and added proper x-axis ticks
@author: Aditi Bose
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import matplotlib.cm as cm
from collections import defaultdict
import os

class EpilepsyHeatmapGenerator:
    def __init__(self):
        # Define edge types
        self.edge_types = ['FF', 'FN', 'FO', 'NN', 'NO', 'OO']
        
        # Use a colormap for edge colors
        colormap = cm.get_cmap('plasma')  # You can change this to any colormap
        self.edge_colors = {}
        for i, edge_type in enumerate(self.edge_types):
            self.edge_colors[edge_type] = colormap(i / len(self.edge_types))[:3]  # RGB only
        
        # Background color (white)
        self.bg_color = [1.0, 1.0, 1.0]
        
        # Network labels
        self.network_labels = (
            ['Pre-1', 'Pre-2'] + 
            [f'Sz-{i}' for i in range(1, 9)] + 
            ['Post-1', 'Post-2']
        )
        
        self.segment_labels = ['1', '2', '3', '4']
        
    def load_csv_data(self, csv_path):
        """Load CSV data and return DataFrame"""
        try:
            df = pd.read_csv(csv_path)
            print(f"Loaded CSV with shape: {df.shape}")
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            raise
    
    def extract_subject_data(self, df, subject_index):
        """Extract data for a specific subject"""
        start_row = subject_index * 48
        end_row = start_row + 48
        
        subject_data = df.iloc[start_row:end_row].copy()
        subject_data = subject_data.reset_index(drop=True)
        
        return subject_data
    
    def get_nonzero_edges(self, row_data):
        """Get all non-zero edges with their counts"""
        nonzero_edges = {}
        for edge_type in self.edge_types:
            count = row_data[edge_type]
            if count > 0:
                nonzero_edges[edge_type] = count
        return nonzero_edges
    
    def create_segment_image_fixed_order(self, nonzero_edges, segment_width=50, cell_height=50):
        """
        Create image array for a single segment with fixed edge order
        Each bar has height equal to cell height
        """
        segment_img = np.full((cell_height, segment_width, 3), self.bg_color, dtype=np.float32)
        
        if not nonzero_edges:
            return segment_img
        
        # Calculate total width needed and bar widths
        total_count = sum(nonzero_edges.values())
        if total_count == 0:
            return segment_img
        
        # Create bars in fixed order (FF, FN, FO, NN, NO, OO)
        x_start = 0
        for edge_type in self.edge_types:
            if edge_type in nonzero_edges:
                count = nonzero_edges[edge_type]
                # Bar width proportional to count
                bar_width = int((count / total_count) * segment_width)
                
                if bar_width > 0:
                    x_end = min(x_start + bar_width, segment_width)
                    edge_color = self.edge_colors[edge_type]
                    
                    # Fill entire height of cell
                    segment_img[:, x_start:x_end] = edge_color
                    
                    x_start = x_end
        
        return segment_img
    
    def create_segment_image_descending_order(self, nonzero_edges, segment_width=50, cell_height=50):
        """
        Create image array for a single segment with edges sorted by count (descending)
        Each bar has height equal to cell height
        """
        segment_img = np.full((cell_height, segment_width, 3), self.bg_color, dtype=np.float32)
        
        if not nonzero_edges:
            return segment_img
        
        # Sort edges by count in descending order
        sorted_edges = sorted(nonzero_edges.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate total count
        total_count = sum(nonzero_edges.values())
        if total_count == 0:
            return segment_img
        
        # Create bars in descending order of count
        x_start = 0
        for edge_type, count in sorted_edges:
            # Bar width proportional to count
            bar_width = int((count / total_count) * segment_width)
            
            if bar_width > 0:
                x_end = min(x_start + bar_width, segment_width)
                edge_color = self.edge_colors[edge_type]
                
                # Fill entire height of cell
                segment_img[:, x_start:x_end] = edge_color
                
                x_start = x_end
        
        return segment_img
    
    def create_subject_heatmap(self, df, subject_index, subject_name=None, 
                             plot_name=None, save_path_fixed=None, save_path_descending=None, 
                             show_plot=True):
        """Create both heatmaps for a specific subject"""
        
        # Extract subject data
        subject_data = self.extract_subject_data(df, subject_index)
        
        if subject_name is None:
            subject_name = f"Subject {subject_index + 1}"
        
        if plot_name is None:
            plot_name = subject_name
        
        # Parameters for image creation
        segment_width = 100  # Width of each segment in pixels
        cell_height = 50     # Height of each cell (same for all bars)
        
        # Create full image arrays for both plots
        total_width = 4 * segment_width  # 4 segments
        total_height = 12 * cell_height  # 12 networks
        
        full_image_fixed = np.full((total_height, total_width, 3), self.bg_color, dtype=np.float32)
        full_image_descending = np.full((total_height, total_width, 3), self.bg_color, dtype=np.float32)
        
        # Store edge information for annotations
        edge_info = {}
        
        # Process each network and segment
        for network_idx in range(12):
            network_start_row = network_idx * 4
            
            for segment_idx in range(4):
                row_idx = network_start_row + segment_idx
                row_data = subject_data.iloc[row_idx]
                
                # Get non-zero edges
                nonzero_edges = self.get_nonzero_edges(row_data)
                edge_info[(network_idx, segment_idx)] = nonzero_edges
                
                # Create segment images for both ordering methods
                segment_img_fixed = self.create_segment_image_fixed_order(
                    nonzero_edges, segment_width, cell_height)
                segment_img_descending = self.create_segment_image_descending_order(
                    nonzero_edges, segment_width, cell_height)
                
                # Place segments in full images
                img_row_start = network_idx * cell_height
                img_row_end = img_row_start + cell_height
                img_col_start = segment_idx * segment_width
                img_col_end = img_col_start + segment_width
                
                full_image_fixed[img_row_start:img_row_end, img_col_start:img_col_end] = segment_img_fixed
                full_image_descending[img_row_start:img_row_end, img_col_start:img_col_end] = segment_img_descending
        
        # Create plots
        self._create_plot(full_image_fixed, edge_info, plot_name, "Fixed Order (FF→FN→FO→NN→NO→OO)", 
                         segment_width, cell_height, save_path_fixed, show_plot)
        
        self._create_plot(full_image_descending, edge_info, plot_name, "Descending Order by Count", 
                         segment_width, cell_height, save_path_descending, show_plot)
        
        return edge_info
    
    def _create_plot(self, full_image, edge_info, plot_name, order_type, 
                    segment_width, cell_height, save_path, show_plot):
        """Helper method to create individual plots"""
        
        fig, ax = plt.subplots(figsize=(16, 20))
        
        # # Display the image
        # im = ax.imshow(full_image, aspect='auto', interpolation='none')
        
        im = ax.imshow(full_image, aspect='auto', interpolation='none',
               extent=(0, full_image.shape[1], full_image.shape[0], 0))
        ax.set_xlim(0, full_image.shape[1])
        ax.set_ylim(full_image.shape[0], 0)
        ax.margins(0)

        
        # X-axis ticks and labels (segments)
        segment_centers = [i * segment_width + segment_width/2 for i in range(4)]
        ax.set_xticks(segment_centers)
        ax.set_xticklabels(self.segment_labels, fontsize=14)
        
        # Y-axis ticks and labels - Fixed positioning
        # Row 0 (1st row) center: 0 * cell_height + cell_height/2 = 25
        # Row 2 (3rd row) center: 2 * cell_height + cell_height/2 = 125  
        # Row 10 (11th row) center: 10 * cell_height + cell_height/2 = 525
        y_tick_positions = [
            0 * cell_height + cell_height/2,   # Middle of 1st row (row 0)
            2 * cell_height + cell_height/2,   # Middle of 3rd row (row 2)
            10 * cell_height + cell_height/2   # Middle of 11th row (row 10)
        ]
        y_tick_labels = ['pre-sz', 'szr', 'post-sz']
        
        ax.set_yticks(y_tick_positions)
        ax.set_yticklabels(y_tick_labels, fontsize=16)
        
        # Set labels
        ax.set_xlabel('network layers', fontsize=20)
        ax.set_ylabel('networks', fontsize=20)
        
        # Add grid lines to separate segments and networks
        # Vertical lines (between segments)
        for i in range(1, 4):
            ax.axvline(x=i * segment_width - 0.5, color='black', linewidth=2)
        
        # Horizontal lines (between networks)
        for i in range(1, 12):
            ax.axhline(y=i * cell_height - 0.5, color='black', linewidth=1)
        
        # Add phase separators (thicker lines)
        ax.axhline(y=2 * cell_height - 0.5, color='red', linewidth=4, alpha=0.8)  # After pre-seizure
        ax.axhline(y=10 * cell_height - 0.5, color='red', linewidth=4, alpha=0.8)  # After seizure
        
        # Add text annotations showing counts
        for network_idx in range(12):
            for segment_idx in range(4):
                nonzero_edges = edge_info[(network_idx, segment_idx)]
                
                if nonzero_edges:
                    # Position for text
                    text_x = segment_idx * segment_width + segment_width/2
                    text_y = network_idx * cell_height + cell_height/2
                    
                    # Create annotation text
                    edge_texts = []
                    if order_type == "Fixed Order (FF→FN→FO→NN→NO→OO)":
                        # Show in fixed order
                        for edge_type in self.edge_types:
                            if edge_type in nonzero_edges:
                                edge_texts.append(f"{edge_type}:{nonzero_edges[edge_type]}")
                    else:
                        # Show in descending order
                        sorted_edges = sorted(nonzero_edges.items(), key=lambda x: x[1], reverse=True)
                        for edge_type, count in sorted_edges:
                            edge_texts.append(f"{edge_type}:{count}")
                    
                    annotation = "\n".join(edge_texts)
                    
                    # Add text with semi-transparent background
                    ax.text(text_x, text_y, annotation, ha='center', va='center',
                            fontsize=8, fontweight='bold', color='black',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # Create legend for edge types
        legend_patches = []
        for edge_type in self.edge_types:
            color = self.edge_colors[edge_type]
            patch = mpatches.Patch(color=color, label=f'{edge_type} edges')
            legend_patches.append(patch)
        
        # # Add note about bar width
        # legend_patches.append(mpatches.Patch(color='gray', label='Bar width ∝ Count'))
        
        # Place legend
        ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
        
        # Remove axis ticks for cleaner look
        ax.tick_params(length=0)
        
        plt.tight_layout()
        
        # Save plot if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved plot to: {save_path}")
        
        # Show plot if requested
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def process_all_subjects(self, csv_path, plot_names=None, output_dir=None, show_plots=False):
        """Process all subjects in the CSV file"""
        
        # Load data
        df = self.load_csv_data(csv_path)
        
        # Calculate number of subjects
        num_subjects = len(df) // 48
        print(f"Processing {num_subjects} subjects...")
        
        # Validate plot_names list if provided
        if plot_names is not None:
            if len(plot_names) != num_subjects:
                raise ValueError(f"plot_names list length ({len(plot_names)}) must match number of subjects ({num_subjects})")
            print(f"Using custom plot names: {plot_names}")
        
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            # Create subdirectories for different ordering methods
            fixed_dir = os.path.join(output_dir, "fixed_order")
            descending_dir = os.path.join(output_dir, "descending_order")
            os.makedirs(fixed_dir, exist_ok=True)
            os.makedirs(descending_dir, exist_ok=True)
        
        # Process each subject
        all_results = {}
        
        for subject_idx in range(num_subjects):
            subject_name = f"Subject_{subject_idx + 1:02d}"
            
            # Get plot name
            if plot_names is not None:
                plot_name = plot_names[subject_idx]
                print(f"Processing {subject_name} with plot name: {plot_name}")
            else:
                plot_name = subject_name
                print(f"Processing {subject_name}...")
            
            # Set save paths if output directory provided
            save_path_fixed = None
            save_path_descending = None
            if output_dir:
                filename = plot_name.replace(' ', '_').replace('/', '_') if plot_names else subject_name
                save_path_fixed = os.path.join(fixed_dir, f"{filename}_fixed_order.png")
                save_path_descending = os.path.join(descending_dir, f"{filename}_descending_order.png")
            
            # Create heatmaps
            results = self.create_subject_heatmap(
                df, subject_idx, subject_name, plot_name, 
                save_path_fixed, save_path_descending, show_plots
            )
            
            all_results[subject_name] = results
        
        return all_results


def main():
    """Example usage of the modified EpilepsyHeatmapGenerator"""
    
    # Initialize the generator
    generator = EpilepsyHeatmapGenerator()
    
    # Specify your CSV file path
    csv_path = "C:/Users/coarse-graining-of-top-MIEs/edge-bw.csv"
    
    # Specify output directory for saving plots
    output_dir = "C:/Users/coarse-graining-of-top-MIEs"
    
    # Define custom plot names for each subject
    plot_names = [
        '011a1L'
    ]
    
    try:
        # Process all subjects
        results = generator.process_all_subjects(
            csv_path=csv_path,
            plot_names=plot_names,
            output_dir=output_dir,
            show_plots=False  # Set to True if you want to display plots
        )
        
        print("Processing completed successfully!")
        print("Two sets of plots created:")
        print("1. Fixed order plots: edges arranged as FF→FN→FO→NN→NO→OO")
        print("2. Descending order plots: edges arranged by count (highest to lowest)")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
