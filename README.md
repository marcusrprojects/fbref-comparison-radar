# FBRef Player Comparison Radar Chart Generator

![Language](https://img.shields.io/badge/Language-Python-blue.svg)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
![Libraries](https://img.shields.io/badge/Libraries-BeautifulSoup4%20|%20NumPy%20|%20Matplotlib-orange.svg)

## Overview

This project provides a Python script (`multi_player_radar.py`) to parse saved HTML files from [FBRef.com](https://fbref.com/)'s player comparison tool and generate customizable radar (spider) charts. It extracts specified statistics for selected players, calculates per 90-minute values where appropriate, and visualizes the comparison using `matplotlib`. The script offers command-line options for selecting players, stats, time periods, and customizing plot aesthetics.

## Features

*   Parses player statistics from user-saved FBRef Player Comparison HTML pages.
*   Compares multiple players based on user-selected statistics.
*   Automatically calculates per 90-minute stats for relevant metrics.
*   Generates informative radar charts visualizing player profiles across chosen stats.
*   Highly customizable plot aesthetics:
    *   Background, text, and grid colors.
    *   Optional polygonal fill style.
    *   Customizable font family.
*   Command-line interface for flexible usage:
    *   Specify HTML input file.
    *   Select specific players to include.
    *   Choose which statistics (`aria-label`s) to plot.
    *   Add a custom title prefix.
    *   Save the plot to a specified file (PNG format).

## Example Output

![UCL - Messi, CR7, Neymar Radar Chart](./data_viz/t3-17-24-radar-20250430_1401.png)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Create environment
    python3 -m venv venv

    # Activate (Linux/macOS)
    source venv/bin/activate

    # Activate (Windows CMD)
    # venv\Scripts\activate.bat

    # Activate (Windows PowerShell)
    # .\venv\Scripts\Activate.ps1
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Prepare HTML Data:**
    *   Navigate to the "Player Comparison" tool on [FBRef.com](https://fbref.com/).
    *   Select the players and season(s) you want to compare.
    *   Once the comparison table is displayed, save the **complete HTML page** using your browser (e.g., `File -> Save Page As... -> Webpage, Complete`).
    *   Place these saved `.html` files into a directory. The script defaults to looking in `./htmls/` (create this directory if it doesn't exist).

## Usage

Run the script (`multi_player_radar.py`) from your terminal within the activated virtual environment.

**Basic Usage (using default stats from 'my_comparison.html' in './htmls/'):**
```bash
python multi_player_radar.py my_comparison
```
(Note: Only provide the base filename, without .html)

**Specify Players, Stats, Output File, and Title:**
```bash
python multi_player_radar.py chiesa-rashford-kvara-sancho \
    --players "Chiesa Federico" "Rashford Marcus" "Kvaratskhelia Khvicha" \
    --stats "npxG + xAG" "Progressive Passes" "Successful Take-Ons" "Goals/Shot" "Shot-Creating Actions" "Total Carrying Distance" \
    --output winger_comparison.png \
    --title "Winger Comparison 2018+"
```
(Ensure player names match the csk attribute and stat names match the aria-label in the HTML source)

**Specify HTML Directory:**
```bash
python multi_player_radar.py my_comparison --htmldir path/to/my/html_files
```

**View All Options:**
```bash
python multi_player_radar.py --help
```

## Files
- `multi_player_radar.py`: The main Python script for parsing and plotting.
- `requirements.txt`: Lists the necessary Python packages.
- `README.md`: This documentation file.
- `htmls/` (Example directory): Place your saved FBRef HTML files here by default.
- `output/` or `data_viz/` (Example directory): A potential location to save generated plots (consider adding this to .gitignore).

## Dependencies
- Python 3.8+
- Beautiful Soup 4 (`beautifulsoup4`)
- NumPy (`numpy`)
- Matplotlib (`matplotlib`)
