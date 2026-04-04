# Seizure Propagation Toolbox

Python scripts for determining motif driven seizure propagation modes in human epilepsy based on edge centrality measures. Code is prepared using the followings:

A. Four centrality metrics i.e. nearest neighbor centrality, eigenvector centrality, closeness and betweenness centrality.

B. Three groups of sampled brain regions i.e. seizure onset area, nearby ipsilateral and other regions.

But can be generalized for any expanded sets of **A** and **B** for any other datasets.

## Deliverables

Pearson correlation matrices corresponding to a single seizure are provided.

## Scripts

**The summary and script details are presented in the exact chronological order of the execution pipeline.**

### Summary of the scripts included

`calc_Pearson-centrality.py` : Calculates Pearson correlation matrices from preprocessed data and then calculates pairwise(vertex & edge) centrality metrics.

`edge-ranking.py` : Assigns ranks to edges separately for each brain network.

`vertex-ranking.py` : Assigns ranks to vertices separately for each brain network.

`nw-select.py` : Binning method is used for selection.

`check-centrality-distributions.py` : Plots centrality distributions for vertices as well as edges across networks.

`edge-cent_annotated-masked.py` : Annotate centrality values and add mask on redundant elements.

`edge-bw_thresh.py` : Determines global threshold centrality using edge betweenness(due to its bottleneck feature; traceable from distribution) to cut off non-informative elements across networks for all centralities.

`count-MIEs.py` : Counts 6 types of links across 4 segments of each network and stores info as .csv for further continuation.

`plot-MIEs.py` : Plots the distribution of counts (derived from `count-MIEs.py`) as heatmap to understand existing network architecture of informative elements.

`szr-grouping_ictal-period.py` : main script to find out propagation mode.

#### `calc_Pearson-centrality.py`

Given code computes Pearson correlation metrices(PCM) from one EEG time series and centrality values for vertices and edges are computed henceforth and stored as 2 separate .csv(one for vertex and one for edge centrality per seizure). As already mentioned in **Deliverables**, modify the code to make it directly executable using PCMs or any other correlation metrices. So, remove the definitions *segment_data* and *calculate_correlation_matrix*, and modify rest of the code accordingly.

[Graph-tool](https://graph-tool.skewed.de/static/docs/stable/) is used for efficient manipulation and statistical analysis of networks. For installation, help yourself from [https://graph-tool.skewed.de/installation.html](https://graph-tool.skewed.de/installation.html). 

The following parameters have to be set:

`sampling_freq`: Currently set to 200 Hz as per our dataset.

`window_length`: We considered it to be 2.5 s.

`centrality_type`: Set it to either of the **B**, **nn**, **E**, or **C** pairwise computation of centralities.

Also, set paths for the desired output directories: `correlation_output_dirs`,`output_dir_vertex`, and `output_dir_edge`

#### `edge-ranking.py`

This code assigns ranks to the centrality values of all edges in descending order. 

Set up the following paths:

`csv_files`: Uses .csv file containing centrality values of all edges across all networks corresponding to each seizure. In given code, one file path is loaded, but adding multiple file paths is also allowed.

`output_directory`: Output directory to save all ranked .csv files for particular centrality.

#### `vertex-ranking.py`

This code assigns ranks to the centrality values of all vertices in descending order.

Set up the following paths:

`csv_files`: Uses .csv file containing centrality values of all vertices across all networks corresponding to each seizure. In given code, one file path is loaded, but adding multiple file paths is also allowed.

`output_directory`: Output directory to save all ranked .csv files for particular centrality.

#### `check-centrality-distributions.py`

This code displays the centrality distributions of both network constituents across all networks on interactive template as well as .gif.

The following parameters have to be set:

`ani`: Change the values of parameters.

`selected_networks_list`: List of networks to be included obtained as output of `nw-select.py`.

Required to set up the followings:

`input_files`: Add .csv file paths.

`plot_names`: Add desired plot names in accordance.

`plot_titles`: Add desired plot titles in accordance.

`output_folder`: Add desired directory path for saving outputs.

#### `edge-cent_annotated-masked.py`

This code helps visualize the proportion of superfluous and non-informative(zero centrality) edges in each network, which helps calculate a global threshold at next step.

Visit following definition if needed:

***classify_nodes***: Change the channel names for grouping of sampled brain regions according to available dataset.

Set up following variable:

`selected_networks_list`: List of networks to be included obtained as output of `nw-select.py`.

Required to set up the followings:

`ranked_edge_csv_list`: Add .csv file paths corresponding to a particular ranked edge centrality for all seizures.

`values_edge_csv_list`: Add .csv file paths corresponding to a particular edge centrality for all seizures.

`vertex_csv_list`: Add .csv file paths corresponding to a particular ranked vertex centrality for all seizures.

`is_right_case_list`: List that specifies whether that particular seizure onsets from right/left mesial temporal lobe.

`main_output_dir`: Add desired directory path for saving outputs.

#### `edge-bw_thresh.py`

This code determines a global threshold based on edge betweenness centrality to isolate the most central and informative structure within each time-evolving brain network. The threshold obtained from edge betweenness is then applied across functional networks defined by other edge-based centrality measures.

Visit following definition if needed:

***classify_nodes***: Change the channel names for grouping of sampled brain regions according to available dataset.

***find_identical_values_threshold***: Parameter values in this definition may be adjusted based on the visual patterns and inferences drawn from the plots generated by `edge-cent_annotated-masked.py`.

Required to set up the followings:

`ranked_edge_csv_list`: Add .csv file paths corresponding to a particular ranked edge centrality for all seizures.

`values_edge_csv_list`: Add .csv file paths corresponding to a particular edge centrality for all seizures.

`vertex_csv_list`: Add .csv file paths corresponding to a particular ranked vertex centrality for all seizures.

`is_right_case_list`: List that specifies whether that particular seizure onsets from right/left mesial temporal lobe.

`main_output_dir`: Add desired directory path for saving outputs.

#### `count-MIEs.py`

This code logs all 6 link types across every segment of each network for all seizures and stores the results in a single .csv file for each edge centrality measure.

Set up the following parameter:

`threshold_value`: Currently it's set to 76 as obtained globally from `edge-bw_thresh.py` using all seizures.

Visit following definition if needed:

***classify_nodes***: Change the channel names for grouping of sampled brain regions according to available dataset.

***divide_into_segments***: Adjust `segment_size` as per requirement.

Required to set up the followings:

`ranked_edge_csv_list`: Add .csv file paths corresponding to a particular ranked edge centrality for all seizures.

`values_edge_csv_list`: Add .csv file paths corresponding to a particular edge centrality for all seizures.

`vertex_csv_list`: Add .csv file paths corresponding to a particular ranked vertex centrality for all seizures.

`is_right_case_list`: List that specifies whether that particular seizure onsets from right/left mesial temporal lobe.

`output_csv_path`: Add desired path for saving outputs for all seizures as a single .csv file.

#### `plot-MIEs.py`

This code generates plots showing the link counts across network segments obtained from `count-MIEs.py`. Two types of plots are generated for understanding and eye-training of diverseness/similarity across data.

Required to set up the followings:

`csv_path`: Uses .csv file obtained from `count-MIEs.py`. One .csv corresponding to a specific centrality type is allowed to load.

`output_dir`: Add directory path to store plots.

`plot_names`: Add plot names for seizures respectively.

#### `szr-grouping_ictal-period.py` 

This is the main code to categorize a seizure from different graph-theoretic analysis.

As the threshold obtained in our case is 76, hence number of links in each network segment is 76/4=19. Change it in the following part in code if needed. 

```python
if hasattr(self, '_current_component') and self._current_component == 'fn':
    # FF, FN, NN (first 3 columns)
    weight = sum(conn_values[:3]) / 19
elif hasattr(self, '_current_component') and self._current_component == 'fno':
    # FO, NO (next 2 columns)
    weight = sum(conn_values[3:5]) / 19
elif hasattr(self, '_current_component') and self._current_component == 'o':
    # OO (last column)
    weight = conn_values[5] / 19
```

Required to set up the followings in definition ***analyze_propagation_patterns***:

`subjects_data`: Add lists containing motif-based encodes of functional networks for all seizures for mode identification.

`subject_ids`: Change as per total seizures available.

`results`: Change file path for csv obtained from `count-MIEs.py`

```python
# Analyze with both methods
results = classifier.analyze_subjects_ictal_only(subjects_data, subject_ids, 
            csv_path="C:/Users/Aditi Bose/OneDrive - IIIT Hyderabad/IIITH-PhD/Research-works/EEG-epilepsy-UKB/Universitätsklinikum Bonn/codes-outputs-plots_v1/Codes-for-submission2025_science-advances/coarse-graining-of-top-MIEs/edge-bw.csv")
```

`df_detailed`: Change where to save the analysis results.

```python
# Export detailed results with sequences
df_detailed = classifier.export_results_to_csv(results, 
    "C:/Users/Aditi Bose/OneDrive - IIIT Hyderabad/IIITH-PhD/Research-works/EEG-epilepsy-UKB/Universitätsklinikum Bonn/codes-outputs-plots_v1/Codes-for-submission2025_science-advances/weighted-Shannon-based-grouping/szr-grouping_detailed_ictal_bw.csv")
```

## Folders

#### PCMs

**(Deliverables)**

Correlation networks for a single seizure are provided.

#### centrality-csvs

Pairwise centrality computed by `calc_Pearson-centrality.py`, `edge-ranking.py` and `vertex-ranking.py` are stored here.

#### centrality-distribution

Plots obtained from `check-centrality-distributions.py` get stored here.

#### edge-cent-threshold

Plots obtained from `edge-cent_annotated-masked.py` is stored here.

#### coarse-graining-of-top-MIEs

Output .csv file and corresponding plots obtained from `count-MIEs.py` and `plot-MIEs.py` respectively are stored here.

#### weighted-Shannon-based-grouping


Output .csvs and plot obtained from `szr-grouping_ictal-period.py` are stored here. The plot here shows the pattern of propagation mode for a particular seizure corresponding to a specific centrality.
