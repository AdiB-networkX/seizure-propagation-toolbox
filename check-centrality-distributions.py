# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 22:23:35 2025

@author: Aditi Bose
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import json

# Function to plot and save animations
def plot_sorted_rows_for_animation(file_path, selected_rows, plot_name, plot_title, output_folder):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Extract the header (x-axis data)
    x_data = df.columns[1:]

    # Create a figure for the animation
    fig, ax = plt.subplots(figsize=(12, 8))

    # Store data for each frame
    frame_data = []
    
    # Function to update the plot for each row in the animation
    def update_plot(frame):
        ax.clear()  # Clear the previous plot
        y_row = selected_rows[frame]  # Get the row to plot

        # Extract the y-axis data for the selected row
        y_data = df.iloc[y_row, 1:]  # Skip the first column

        # Sort by the y-axis values and rearrange the x-axis labels accordingly
        sorted_indices = y_data.argsort()[::-1] 
            # argsort(): performs ascending sorting by default
            # [::-1]: reverses the order of the indices produced by argsort(), 
            ## effectively sorting the array in descending order  
                                 
        sorted_y = y_data.iloc[sorted_indices]
        sorted_x = x_data[sorted_indices]

        # Store frame data for interactive version
        if frame == 0:  # Only store once
            for i, row in enumerate(selected_rows):
                row_y_data = df.iloc[row, 1:]
                row_sorted_indices = row_y_data.argsort()[::-1]
                row_sorted_y = row_y_data.iloc[row_sorted_indices]
                row_sorted_x = x_data[row_sorted_indices]
                
                frame_data.append({
                    'network': i,  # Use sequential numbering instead of actual row number
                    'x': row_sorted_x.tolist(),
                    'y': row_sorted_y.tolist()
                })

        # Plot the curve for the selected row
        ax.plot(sorted_x, sorted_y, marker='o', linewidth=2, markersize=6)

        # Add labels and title
        ax.set_xlabel("Vertices", fontsize=12)
        ax.set_ylabel("Centrality Values", fontsize=12)
        ax.set_title(f"{plot_title} - Network {frame}", fontsize=14, fontweight='bold')

        # Display the legend to label each curve
        ax.legend(loc='upper right')

        # Rotate x-ticks for better readability
        plt.xticks(rotation=90, ha='right')

        # Show grid
        ax.grid(True, alpha=0.3)

    # Create an animation and store it in the variable `ani`
    ani = animation.FuncAnimation(fig, update_plot, frames=len(selected_rows), repeat=True, interval=1000) #interval time (in milliseconds) between frames

    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Save as GIF
    gif_output_path = os.path.join(output_folder, f"{plot_name}.gif")
    ani.save(gif_output_path, writer="pillow", fps=1)
    
    # Create interactive HTML version
    create_interactive_html(frame_data, plot_name, plot_title, output_folder)

    # Close the plot to prevent display
    plt.close(fig)


def create_interactive_html(frame_data, plot_name, plot_title, output_folder):
    """Create an interactive HTML version with pause/play controls"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plot_title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        .btn {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .btn:hover {{
            background-color: #0056b3;
        }}
        .btn:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
        }}
        .info {{
            text-align: center;
            margin: 10px 0;
            font-size: 18px;
            font-weight: bold;
        }}
        .progress {{
            width: 100%;
            height: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            background-color: #007bff;
            transition: width 0.3s ease;
        }}
        #chartContainer {{
            position: relative;
            height: 500px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center;">{plot_title}</h1>
        
        <div class="controls">
            <button class="btn" id="playPauseBtn" onclick="togglePlayPause()">Play</button>
            <button class="btn" id="resetBtn" onclick="resetAnimation()">Reset</button>
            <button class="btn" id="prevBtn" onclick="previousFrame()">Previous</button>
            <button class="btn" id="nextBtn" onclick="nextFrame()">Next</button>
        </div>
        
        <div class="info">
            <span id="currentInfo">Network 0</span>
            <span style="margin: 0 20px;">|</span>
            <span>Frame <span id="frameCounter">1</span> of <span id="totalFrames">{len(frame_data)}</span></span>
        </div>
        
        <div class="progress">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <div id="chartContainer">
            <canvas id="myChart"></canvas>
        </div>
    </div>

    <script>
        const frameData = {json.dumps(frame_data)};
        let currentFrame = 0;
        let isPlaying = false;
        let animationInterval;
        let chart;

        // Initialize the chart
        function initChart() {{
            const ctx = document.getElementById('myChart').getContext('2d');
            chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: frameData[0].x,
                    datasets: [{{
                        label: `Network ${{frameData[0].network}}`,
                        data: frameData[0].y,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 3,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        fill: false,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: 'Centrality Values Distribution'
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    const dataIndex = context[0].dataIndex;
                                    const edgeLabel = context[0].label;
                                    return `Edge #${{dataIndex + 1}}: ${{edgeLabel}}`;
                                }},
                                label: function(context) {{
                                    const value = context.parsed.y;
                                    const networkNum = frameData[currentFrame].network;
                                    return `Network ${{networkNum}}: ${{value.toFixed(4)}}`;
                                }},
                                afterBody: function(context) {{
                                    const dataIndex = context[0].dataIndex;
                                    return `Sequential Position: ${{dataIndex + 1}} of ${{frameData[currentFrame].x.length}}`;
                                }}
                            }},
                            displayColors: true,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#007bff',
                            borderWidth: 1
                        }}
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Vertices'
                            }},
                            ticks: {{
                                maxRotation: 90,
                                minRotation: 90
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Centrality Values'
                            }}
                        }}
                    }},
                    animation: {{
                        duration: 300
                    }}
                }}
            }});
        }}

        function updateChart(frame) {{
            const data = frameData[frame];
            chart.data.labels = data.x;
            chart.data.datasets[0].data = data.y;
            chart.data.datasets[0].label = `Network ${{data.network}}`;
            chart.update('none');
            
            document.getElementById('currentInfo').textContent = `Network ${{data.network}}`;
            document.getElementById('frameCounter').textContent = frame + 1;
            
            const progress = ((frame + 1) / frameData.length) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }}

        function togglePlayPause() {{
            const btn = document.getElementById('playPauseBtn');
            if (isPlaying) {{
                clearInterval(animationInterval);
                btn.textContent = 'Play';
                isPlaying = false;
            }} else {{
                animationInterval = setInterval(() => {{
                    currentFrame = (currentFrame + 1) % frameData.length;
                    updateChart(currentFrame);
                    
                    if (currentFrame === 0) {{
                        // Animation completed one cycle
                        clearInterval(animationInterval);
                        btn.textContent = 'Play';
                        isPlaying = false;
                    }}
                }}, 1000);
                btn.textContent = 'Pause';
                isPlaying = true;
            }}
        }}

        function resetAnimation() {{
            clearInterval(animationInterval);
            currentFrame = 0;
            updateChart(currentFrame);
            document.getElementById('playPauseBtn').textContent = 'Play';
            isPlaying = false;
        }}

        function nextFrame() {{
            clearInterval(animationInterval);
            currentFrame = (currentFrame + 1) % frameData.length;
            updateChart(currentFrame);
            document.getElementById('playPauseBtn').textContent = 'Play';
            isPlaying = false;
        }}

        function previousFrame() {{
            clearInterval(animationInterval);
            currentFrame = currentFrame === 0 ? frameData.length - 1 : currentFrame - 1;
            updateChart(currentFrame);
            document.getElementById('playPauseBtn').textContent = 'Play';
            isPlaying = false;
        }}

        // Initialize everything when page loads
        window.onload = function() {{
            initChart();
            updateChart(0);
            document.getElementById('totalFrames').textContent = frameData.length;
        }};
    </script>
</body>
</html>
    """
    
    html_output_path = os.path.join(output_folder, f"{plot_name}.html")
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive HTML saved to: {html_output_path}")

# Example usage
# ## edge betweenness
# input_files = [
# "C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/edge-betweenness/generalised/011a_LMT_no-ref-ch_edge-betweenness-centrality.csv",
# ]

## vertex betweenness
input_files = [
"C:/Users/Aditi Bose/Downloads/1_Centrality Values and Ranks - window length=2.5s, no binning/vertex-betweenness/generalised/011a_LMT_no-ref-ch_vertex-betweenness-centrality.csv",
]

plot_names = [	
    '$C_v^B$ - S18',  # S18 = 011a1L
]

plot_titles = [
    "$C_v^B$ : S18",
]

# Define different selected_networks for each subject
selected_networks_list = [
    [1,8,12,15,24,26,32,39,41,45,55,64], #S18
]

output_folder = "C:/Users/Aditi Bose/OneDrive - IIIT Hyderabad/IIITH-PhD/Research-works/EEG-epilepsy-UKB/Universitätsklinikum Bonn/codes-outputs-plots_v1/Codes-for-submission2025_science-advances/centrality-distribution"


# Loop through the files, plot names, titles, and selected networks to generate animations
for file_path, plot_name, plot_title, selected_rows in zip(input_files, plot_names, plot_titles, selected_networks_list):
    plot_sorted_rows_for_animation(file_path, selected_rows, plot_name, plot_title, output_folder)