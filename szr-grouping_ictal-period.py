# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 14:13:48 2025
@author: Aditi Bose
"""

import numpy as np
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

class SeizurePropagationClassifier:
    def __init__(self):
        # Define all possible connectivity states
        self.states = [
            '1ax', '1ao', '1bx', '1bo', '1cx', '1co',
            '2ax', '2ao', '2bx', '2bo', '2cx', '2co',
            '3ax', '3ao', '3bx', '3bo', '3cx', '3co',
            '4ax', '4ao', '4bx', '4bo', '4cx', '4co'
        ]
        # Debug storage for variable explorer
        self.debug_entropy_calc = {}
        self.debug_connectivity_weights = {}
        self.debug_series_breakdown = {}
        
    def export_debug_data(self, filename="debug_entropy_calculations.csv"):
        """Export detailed entropy calculation steps for debugging"""
        debug_data = []
        
        for calc_id, calc_info in self.debug_entropy_calc.items():
            subject_id, component = calc_id.split('_', 1)
            
            for i, unique_val in enumerate(calc_info['unique_values']):
                debug_data.append({
                    'Subject_ID': subject_id,
                    'Component': component,
                    'Unique_Value': unique_val,
                    'Count': calc_info['counts'][i],
                    'Probability': calc_info['probabilities'][i],
                    'Weight': calc_info['weights'][i],
                    'Entropy_Component': calc_info['entropy_components'][i],
                    'Series': '|'.join(map(str, calc_info['series'])),
                    'Final_Entropy': calc_info['final_entropy']
                })
        
        df = pd.DataFrame(debug_data)
        df.to_csv(filename, index=False)
        print(f"🔍 Debug entropy data exported to: {filename}")
        return df
        
        
    def load_connectivity_data(self, csv_path):
        """Load connectivity strength data from CSV file"""
        print(f"🔍 Loading connectivity data from: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            print(f"📊 CSV loaded successfully. Shape: {df.shape}")
            print(f"📋 Column names: {list(df.columns)}")
            print(f"🔢 First few rows:\n{df.head()}")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return None
        
        connectivity_data = {}
        
        for subject_idx in range(20):
            start_row = subject_idx * 48  # by default, header is skipped. python's rule to handle csv
            subject_data = []
            
            print(f"\n🔍 Processing Subject {subject_idx + 1}")
            print(f"   Start row: {start_row}")
            
            # Get segments 3-10 (middle 8 segments)
            for segment in range(2, 10):  # segments 3-10 (0-indexed: 2-9)
                segment_start = start_row + segment * 4
                print(f"   Segment {segment + 1}: row {segment_start}")
                
                # Check if row exists
                if segment_start >= len(df):
                    print(f"   ❌ Row {segment_start} out of range (CSV has {len(df)} rows)")
                    continue
                    
                # Take first row of each segment (first of 4 network parts)
                row_data = df.iloc[segment_start]
                print(f"   Row data shape: {len(row_data)}")
                
                # Extract last 6 columns (FF,FN,NN,FO,NO,OO)
                if len(row_data) < 6:
                    print(f"   ❌ Not enough columns in row {segment_start}")
                    continue
                    
                connectivity_values = row_data.iloc[-6:].values
                print(f"   Connectivity values: {connectivity_values}")
                subject_data.append(connectivity_values)
            
            connectivity_data[f"S-{subject_idx+1:02d}"] = subject_data
            print(f"   ✅ Subject S-{subject_idx+1:02d} has {len(subject_data)} segments")
        
        return connectivity_data
    
    def calculate_weighted_shannon_entropy(self, series, connectivity_data=None, subject_id=None):
        """Calculate weighted permutation entropy of a series"""
        if not series:
            return 0
        
        # Initialize debug storage for this calculation
        calc_id = f"{subject_id}_{getattr(self, '_current_component', 'unknown')}"
        self.debug_entropy_calc[calc_id] = {}
        
        # Count occurrences of each unique value
        unique_values, counts = np.unique(series, return_counts=True)
        
        # Calculate probabilities
        probabilities = counts / len(series)
        
        # Store basic info
        self.debug_entropy_calc[calc_id]['series'] = series
        self.debug_entropy_calc[calc_id]['unique_values'] = unique_values
        self.debug_entropy_calc[calc_id]['counts'] = counts
        self.debug_entropy_calc[calc_id]['probabilities'] = probabilities
        
        # Calculate weights if connectivity data is provided
        if connectivity_data is not None and subject_id is not None:
            print(f"🔍 Calculating weights for {subject_id}, component: {getattr(self, '_current_component', 'unknown')}")
            
            if subject_id not in connectivity_data:
                print(f"❌ Subject {subject_id} not found in connectivity data")
                weights = np.ones(len(probabilities))
            else:
                subject_conn_data = connectivity_data[subject_id]
                print(f"📊 Subject has {len(subject_conn_data)} connectivity segments")
                print(f"📊 Series length: {len(series)}")
                
                if len(subject_conn_data) != len(series):
                    print(f"❌ Mismatch: connectivity segments ({len(subject_conn_data)}) != series length ({len(series)})")
                    weights = np.ones(len(probabilities))
                else:
                    weights = []
                    position_weights = []  # Store individual position weights
                    
                    for unique_val in unique_values:
                        # Find all positions of this unique value in the series
                        positions = [i for i, val in enumerate(series) if val == unique_val]
                        
                        total_weight = 0
                        val_position_weights = []
                        
                        for pos in positions:
                            if pos >= len(subject_conn_data):
                                print(f"❌ Position {pos} out of range for connectivity data")
                                continue
                                
                            conn_values = subject_conn_data[pos]  # Get connectivity values for this position
                            
                            # Map state to connectivity values based on parsed state
                            if hasattr(self, '_current_component') and self._current_component == 'fn':
                                # FF,FN,NN (first 3 columns)
                                weight = sum(conn_values[:3]) / 19
                            elif hasattr(self, '_current_component') and self._current_component == 'fno':
                                # FO,NO (next 2 columns)
                                weight = sum(conn_values[3:5]) / 19
                            elif hasattr(self, '_current_component') and self._current_component == 'o':
                                # OO (last 1 column)
                                weight = conn_values[5] / 19
                            else:
                                weight = 1.0  # Default weight if component not set
                            
                            total_weight += weight
                            val_position_weights.append({'position': pos, 'conn_values': conn_values, 'weight': weight})
                        
                        # Average weight for this unique value
                        avg_weight = total_weight / len(series)
                        weights.append(avg_weight)
                        position_weights.append({'unique_val': unique_val, 'positions': positions, 'weights': val_position_weights, 'avg_weight': avg_weight})
                    
                    weights = np.array(weights)
                    
                    # Store detailed weight calculation
                    self.debug_entropy_calc[calc_id]['connectivity_data'] = subject_conn_data
                    self.debug_entropy_calc[calc_id]['position_weights'] = position_weights
        else:
            weights = np.ones(len(probabilities))  # Default to uniform weights
        
        # Store weights
        self.debug_entropy_calc[calc_id]['weights'] = weights
        
        # Calculate weighted Shannon entropy
        entropy = -np.sum(weights * np.log(probabilities)) # np.log() function refers to the natural logarithm, i.e., log base e, where e ≈ 2.71828
        
        # Store final calculation
        self.debug_entropy_calc[calc_id]['entropy_components'] = weights * probabilities * np.log(probabilities)
        self.debug_entropy_calc[calc_id]['final_entropy'] = entropy
        
        return entropy
    
    def parse_connectivity_state(self, state):
        """Parse connectivity state into components
        This simply converts the  state into string of numbers to proceed for 
        the further calculation, but does not take the numbers into account for calculation
        """
        fn_connectivity = int(state[0])-1      # F-N connectivity (1-4) ; 1:0,2:1,3:2,4:3
        # fn_connectivity = 1 if int(state[0]) <= 3 else 2    # F-N connectivity (1-4) ; 1,2,3:1, 4:2
        fno_connectivity = state[1]          # F,N-O connectivity (a,b,c) 
        o_self_loop = state[2:]             # O self-loop (x,o) 
        
        # Convert to numeric values
        fno_numeric = {'a': 0, 'b': 1, 'c': 2}[fno_connectivity]
        o_numeric = 0 if o_self_loop == 'x' else 1  # o has stronger self-loop, [0,1]; [0,2]
        
        return {
            'fn_connectivity': fn_connectivity,
            'fno_connectivity': fno_numeric,
            'o_self_loop': o_numeric,
            'raw_state': state
        }
    
    def analyze_connectivity_dynamics(self, time_series, phase_name="", connectivity_data=None, subject_id=None):
        """Analyze how F-N, F,N-O, and O components change over time"""
        parsed_states = [self.parse_connectivity_state(state) for state in time_series]
        
        # Extract time series for each component
        fn_series = [s['fn_connectivity'] for s in parsed_states]
        fno_series = [s['fno_connectivity'] for s in parsed_states]
        o_series = [s['o_self_loop'] for s in parsed_states]
        
        # Calculate transitions and direction
        fn_transitions = sum(1 for i in range(1, len(fn_series)) 
                           if abs(fn_series[i] - fn_series[i-1]) > 0)
        fno_transitions = sum(1 for i in range(1, len(fno_series)) 
                            if abs(fno_series[i] - fno_series[i-1]) > 0)
        o_transitions = sum(1 for i in range(1, len(o_series)) 
                          if abs(o_series[i] - o_series[i-1]) > 0)
        
        # Calculate Shannon entropy for each component
        self._current_component = 'fn'
        fn_entropy = self.calculate_weighted_shannon_entropy(fn_series, connectivity_data, subject_id)
        self._current_component = 'fno'
        fno_entropy = self.calculate_weighted_shannon_entropy(fno_series, connectivity_data, subject_id)
        self._current_component = 'o'
        o_entropy = self.calculate_weighted_shannon_entropy(o_series, connectivity_data, subject_id)
        
        # Calculate transition ratios T = transitions/max_transitions
        max_transitions = len(fn_series) - 1 if len(fn_series) > 1 else 1
        fn_transition_ratio = fn_transitions / max_transitions
        fno_transition_ratio = fno_transitions / max_transitions
        o_transition_ratio = o_transitions / max_transitions
        
        # Calculate new scores: S * T
        fn_score = fn_entropy * fn_transition_ratio
        fno_score = fno_entropy * fno_transition_ratio
        o_score = o_entropy * o_transition_ratio
        
        return {
            'phase': phase_name,
            'fn_stats': {
                'transitions': fn_transitions,
                'entropy': fn_entropy,
                'transition_ratio': fn_transition_ratio,
                'score': fn_score,
                'series': fn_series
            },
            'fno_stats': {
                'transitions': fno_transitions,
                'entropy': fno_entropy,
                'transition_ratio': fno_transition_ratio,
                'score': fno_score,
                'series': fno_series
            },
            'o_stats': {
                'transitions': o_transitions,
                'entropy': o_entropy,
                'transition_ratio': o_transition_ratio,
                'score': o_score,
                'series': o_series
            },
            'total_transitions': fn_transitions + fno_transitions + o_transitions,
            'parsed_states': parsed_states
        }
        
    
    def classify_propagation_pattern(self, time_series, connectivity_data=None, subject_id=None):
        """Classify seizure based on ictal propagation patterns only"""
        if len(time_series) != 12:
            raise ValueError("Time series must have exactly 12 windows")
        
        # Extract ictal period only (windows 3-10)
        ictal = time_series[2:10]              # Windows 3-10 (8 windows)
        
        # Ictal only analysis
        ictal_dynamics = self.analyze_connectivity_dynamics(ictal, "ictal_only", connectivity_data, subject_id)
        
        # Get component statistics
        fn_stats = ictal_dynamics['fn_stats']
        fno_stats = ictal_dynamics['fno_stats']
        o_stats = ictal_dynamics['o_stats']
        
        # Component scores
        component_scores = {
            'fn': fn_stats['score'],
            'fno': fno_stats['score'],
            'o': o_stats['score']
        }
             
        return {
            'analysis_scope': "Ictal Only",
            'component_scores': component_scores,
            'dynamics': ictal_dynamics,
            'metrics': {
                'fn_dominance': component_scores['fn'],
                'fno_dominance': component_scores['fno'],
                'o_dominance': component_scores['o'],
                'total_transitions': ictal_dynamics['total_transitions'],
            }
        }    

    def analyze_subjects_ictal_only(self, subjects_data, subject_ids=None, csv_path=None):
        """Analyze subjects with ictal-only approach"""
        if subject_ids is None:
            subject_ids = [f"Subject_{i+1:02d}" for i in range(len(subjects_data))]
        
        results = {}
        
        print(f"🧠 Analyzing {len(subjects_data)} subjects with ictal-only method...")
        print("="*80)
        
        # Load connectivity data if CSV path provided
        connectivity_data = None
        if csv_path:
            connectivity_data = self.load_connectivity_data(csv_path)
        
        for i, time_series in enumerate(subjects_data):
            subject_id = subject_ids[i]
            try:
                # Analyze with ictal-only method
                ictal_result = self.classify_propagation_pattern(time_series, connectivity_data=connectivity_data, subject_id=subject_id)
                
                results[subject_id] = {
                    'ictal_only': ictal_result,
                    'raw_data': time_series
                }
                
                print(f"✅ {subject_id}:")
                print(f"   📊 Ictal Only - FN: {ictal_result['metrics']['fn_dominance']:.3f}")
                
            except Exception as e:
                print(f"❌ Error analyzing {subject_id}: {e}")
                results[subject_id] = {"error": str(e)}
        
        return results
    
    
    def export_results_to_csv(self, results, filename="szr-grouping_detailed_ictal_bw.csv"):
        """Export ictal-only results to CSV file"""
        data_for_export = []
        
        for subject_id, result in results.items():
            if 'error' in result:
                data_for_export.append({
                    'Subject_ID': subject_id,
                    'Error_Message': result['error'],
                    'Ictal_FN_Dominance': None,
                    'Ictal_FNO_Dominance': None,
                    'Ictal_O_Dominance': None,
                    'Raw_Time_Series': None,
                })
            else:
                ictal_metrics = result['ictal_only']['metrics']
                ictal_dynamics = result['ictal_only']['dynamics']
                
                # Extract sequence details
                raw_series = result['raw_data']
                ictal_fn_series = ictal_dynamics['fn_stats']['series']
                ictal_fno_series = ictal_dynamics['fno_stats']['series']
                ictal_o_series = ictal_dynamics['o_stats']['series']
                
                data_for_export.append({
                    'Subject_ID': subject_id,
                    
                    # Score metrics
                    'Ictal_FN_Dominance': ictal_metrics['fn_dominance'],
                    'Ictal_FNO_Dominance': ictal_metrics['fno_dominance'], 
                    'Ictal_O_Dominance': ictal_metrics['o_dominance'],
                    
                    # Shannon entropy values
                    'Ictal_FN_Entropy': ictal_dynamics['fn_stats']['entropy'],
                    'Ictal_FNO_Entropy': ictal_dynamics['fno_stats']['entropy'],
                    'Ictal_O_Entropy': ictal_dynamics['o_stats']['entropy'],
                    
                    # Transition ratios
                    'Ictal_FN_Transition_Ratio': ictal_dynamics['fn_stats']['transition_ratio'],
                    'Ictal_FNO_Transition_Ratio': ictal_dynamics['fno_stats']['transition_ratio'],
                    'Ictal_O_Transition_Ratio': ictal_dynamics['o_stats']['transition_ratio'],
                    
                    # Scores (entropy * transition_ratio)
                    'Ictal_FN_Score': ictal_dynamics['fn_stats']['score'],
                    'Ictal_FNO_Score': ictal_dynamics['fno_stats']['score'],
                    'Ictal_O_Score': ictal_dynamics['o_stats']['score'],
                    
                    # Essential sequences for verification
                    'Raw_Time_Series': "|".join(raw_series),
                    'Ictal_FN_Series': "|".join(map(str, ictal_fn_series)),
                    'Ictal_FNO_Series': "|".join(map(str, ictal_fno_series)),
                    'Ictal_O_Series': "|".join(map(str, ictal_o_series))
                })
        
        df = pd.DataFrame(data_for_export)
        df.to_csv(filename, index=False)
        print(f"📄 Ictal-only results exported to: {filename}")
        return df
        
        # Also add this helper function to the SeizurePropagationClassifier class
        def export_sequence_summary(self, results, filename="sequence-summary_ictal_bw.csv"):
            """Export a simplified sequence summary for quick cross-checking"""
            summary_data = []
            
            for subject_id, result in results.items():
                if 'error' not in result:
                    # Get component sequences for easy comparison
                    ictal_dynamics = result['ictal_only']['dynamics']
                    full_dynamics = result['full_event']['dynamics']
                    
                    # Calculate dominant sequences
                    ictal_fn = ictal_dynamics['fn_stats']['series']
                    ictal_fno = ictal_dynamics['fno_stats']['series'] 
                    ictal_o = ictal_dynamics['o_stats']['series']
                    
                    full_fn = full_dynamics['fn_stats']['series']
                    full_fno = full_dynamics['fno_stats']['series']
                    full_o = full_dynamics['o_stats']['series']
                    
                    # Get dominant component per window
                    ictal_dominant = [max(['fn','fno','o'], key=lambda x: [ictal_fn[i], ictal_fno[i], ictal_o[i]][['fn','fno','o'].index(x)]) for i in range(len(ictal_fn))]
                    full_dominant = [max(['fn','fno','o'], key=lambda x: [full_fn[i], full_fno[i], full_o[i]][['fn','fno','o'].index(x)]) for i in range(len(full_fn))]
                    
                    summary_data.append({
                        'Subject_ID': subject_id,
                        'Raw_Series': " | ".join(result['raw_data']),
                        'Ictal_Windows': " | ".join(result['raw_data'][2:10]),
                        'Ictal_Dominant': " -->  ".join(ictal_dominant),
                        'Full_Dominant': "-->  ".join(full_dominant),
                        'Ictal_Classification': result['ictal_only']['classification'],
                        'Full_Classification': result['full_event']['classification'],
                        'Same_Classification': result['ictal_only']['classification'] == result['full_event']['classification']
                    })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_csv(filename, index=False)
            print(f"📋 Sequence summary exported to: {filename}")
            return df_summary
    
    def create_component_plots(self, results, save_path="C:/Users/weighted-Shannon-based-grouping/"):
        """Create plots for ictal-only analysis"""
        
        # Extract data for plotting
        subjects = []
        ictal_fn_entropy, ictal_fno_entropy, ictal_o_entropy = [], [], []
        ictal_fn_ratio, ictal_fno_ratio, ictal_o_ratio = [], [], []
        ictal_fn_score, ictal_fno_score, ictal_o_score = [], [], []
        
        for subject_id, result in results.items():
            if 'error' not in result:
                subjects.append(subject_id)
                
                # Extract ictal dynamics
                ictal_dynamics = result['ictal_only']['dynamics']
                
                # Entropy values
                ictal_fn_entropy.append(ictal_dynamics['fn_stats']['entropy'])
                ictal_fno_entropy.append(ictal_dynamics['fno_stats']['entropy'])
                ictal_o_entropy.append(ictal_dynamics['o_stats']['entropy'])
                
                # Transition ratios
                ictal_fn_ratio.append(ictal_dynamics['fn_stats']['transition_ratio'])
                ictal_fno_ratio.append(ictal_dynamics['fno_stats']['transition_ratio'])
                ictal_o_ratio.append(ictal_dynamics['o_stats']['transition_ratio'])
                
                # Scores
                ictal_fn_score.append(ictal_dynamics['fn_stats']['score'])
                ictal_fno_score.append(ictal_dynamics['fno_stats']['score'])
                ictal_o_score.append(ictal_dynamics['o_stats']['score'])
        
        # Create plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        x_pos = range(len(subjects))
        
        # Plot 1: Entropy (Ictal)
        axes[0].scatter(x_pos, ictal_fn_entropy, color='red', alpha=0.7, label='FN')
        axes[0].plot(x_pos, ictal_fn_entropy, color='red', alpha=0.5)
        axes[0].scatter(x_pos, ictal_fno_entropy, color='orange', alpha=0.7, label='FNO')
        axes[0].plot(x_pos, ictal_fno_entropy, color='orange', alpha=0.5)
        axes[0].scatter(x_pos, ictal_o_entropy, color='blue', alpha=0.7, label='O')
        axes[0].plot(x_pos, ictal_o_entropy, color='blue', alpha=0.5)
        axes[0].set_title("$C_e^B$:ictal event - $\epsilon_X$")
        axes[0].set_xlabel('seizures')
        axes[0].set_ylabel(r'$\varepsilon_X$')
        axes[0].legend()
        axes[0].set_xticks(x_pos[::1])
        axes[0].set_xticklabels([subjects[i] for i in range(0, len(subjects), 1)], rotation=90)
        
        # Plot 2: Transition Ratios (Ictal)
        axes[1].scatter(x_pos, ictal_fn_ratio, color='red', alpha=0.7, label='FN')
        axes[1].plot(x_pos, ictal_fn_ratio, color='red', alpha=0.5)
        axes[1].scatter(x_pos, ictal_fno_ratio, color='orange', alpha=0.7, label='FNO')
        axes[1].plot(x_pos, ictal_fno_ratio, color='orange', alpha=0.5)
        axes[1].scatter(x_pos, ictal_o_ratio, color='blue', alpha=0.7, label='O')
        axes[1].plot(x_pos, ictal_o_ratio, color='blue', alpha=0.5)
        axes[1].set_title("ictal event - $t_X$")
        axes[1].set_xlabel('seizures')
        axes[1].set_ylabel(r'$t_X$')
        axes[1].legend()
        axes[1].set_xticks(x_pos[::1])
        axes[1].set_xticklabels([subjects[i] for i in range(0, len(subjects), 1)], rotation=90)
        
        # Plot 3: Scores (Ictal)
        axes[2].scatter(x_pos, ictal_fn_score, color='red', alpha=0.7, label='FN')
        axes[2].plot(x_pos, ictal_fn_score, color='red', alpha=0.5)
        axes[2].scatter(x_pos, ictal_fno_score, color='orange', alpha=0.7, label='FNO')
        axes[2].plot(x_pos, ictal_fno_score, color='orange', alpha=0.5)
        axes[2].scatter(x_pos, ictal_o_score, color='blue', alpha=0.7, label='O')
        axes[2].plot(x_pos, ictal_o_score, color='blue', alpha=0.5)
        axes[2].set_title('ictal event - $S_X$')
        axes[2].set_xlabel('seizures')
        axes[2].set_ylabel(r'$\epsilon_X *t_X$')
        axes[2].legend()
        axes[2].set_xticks(x_pos[::1])
        axes[2].set_xticklabels([subjects[i] for i in range(0, len(subjects), 1)], rotation=90)
        
        plt.tight_layout()
        plt.savefig(f"{save_path}ictal_component_analysis_bw.png", dpi=1000, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Ictal-only plots saved to: {save_path}ictal_component_analysis_bw.png")

# ============================================================================
# ANALYSIS EXECUTION
# ============================================================================
def analyze_propagation_patterns():
    """Analyze your data with detailed sequence export for cross-checking"""
    
     ## bw
    subjects_data = [
     ['4co', '4co', '2bo', '2co', '4co', '4co', '4co', '4bo', '4co', '4bo', '4co', '1co'], #S18
 ]

    subject_ids = [f"S-{i+1:02d}" for i in range(20)]
    
    # Initialize classifier
    classifier = SeizurePropagationClassifier()
    
    print("🚀 SEIZURE PROPAGATION PATTERN ANALYSIS")
    print("Entropy, Transition Ratio, and Score Analysis for Ictal vs Full Event")
    
    # Analyze with both methods
    results = classifier.analyze_subjects_ictal_only(subjects_data, subject_ids, 
                csv_path="C:/Users/coarse-graining-of-top-MIEs/edge-bw.csv")
     
    # Export detailed results with sequences
    df_detailed = classifier.export_results_to_csv(results, 
        "C:/Users/weighted-Shannon-based-grouping/szr-grouping_detailed_ictal_bw.csv")
     
    # Create plots
    classifier.create_component_plots(results)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("📊 Check these files:")
    print("   1. szr-grouping_detailed.csv - Full results with all sequence details")
    print("   2. sequence_summary.csv - Quick sequence overview for cross-checking")
    
    return results, classifier

# Example of how to cross-check a specific subject
def cross_check_subject(results, subject_id):
    """Cross-check sequence calculation for a specific subject"""
    if subject_id not in results or 'error' in results[subject_id]:
        print(f"❌ Subject {subject_id} not found or has error")
        return
    
    result = results[subject_id]
    raw_data = result['raw_data']
    
    print(f"\n🔍 CROSS-CHECK FOR {subject_id}")
    print("="*50)
    print(f"Raw time series: {raw_data}")
    print(f"Ictal windows (3-10): {raw_data[2:10]}")
    
    # Manual calculation for verification
    classifier = SeizurePropagationClassifier()
    
    # Parse each state manually
    print("\n📊 MANUAL SEQUENCE CALCULATION:")
    print("Window | State | F-N | F,N-O | O | Dominant")
    print("-------|-------|-----|-------|---|----------")
    
    ictal_states = raw_data[2:10]
    for i, state in enumerate(ictal_states):
        parsed = classifier.parse_connectivity_state(state)
        fn = parsed['fn_connectivity'] 
        fno = parsed['fno_connectivity']
        o = parsed['o_self_loop']
        
        # Find dominant
        scores = {'fn': fn, 'fno': fno, 'o': o}
        dominant = max(scores.keys(), key=lambda k: scores[k])
        
        print(f"  {i+3:2d}   |  {state:3s}  |  {fn}  |   {fno}   | {o} |   {dominant}")
    
    print(f"Ictal FN Score: {result['ictal_only']['metrics']['fn_dominance']:.3f}")
    print(f"Ictal Total Transitions: {result['ictal_only']['metrics']['total_transitions']}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    results, classifier = analyze_propagation_patterns()
    # Export debug data for variable explorer
    debug_df = classifier.export_debug_data("C:/Users/weighted-Shannon-based-grouping/debug_entropy_calculations_ictal_bw.csv")
    
    # Cross-check specific subjects
    cross_check_subject(results, "S-01")

    
    # To check a specific subject's FN component calculation:
    print(classifier.debug_entropy_calc['S-01_fn'])

# To see connectivity weights for a specific calculation:
    print(classifier.debug_entropy_calc['S-01_fn']['weights'])
