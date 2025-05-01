# FBRef Player Comparison Radar Chart Generator

![Language](https://img.shields.io/badge/Language-Python-blue.svg)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
![Libraries](https://img.shields.io/badge/Libraries-BeautifulSoup4%20|%20NumPy%20|%20Matplotlib-orange.svg)

## Overview

This project provides a Python script (`multi_player_radar.py`) to generate customizable radar (spider) charts from saved HTML files from [FBRef.com](https://fbref.com/)'s player comparison tool. It extracts relevant statistics, computes per 90-minute values, and visualizes comparisons between players using `matplotlib`.

> ⚠️ **Disclaimer**: This tool is intended for personal and educational use only. It does **not** scrape FBRef.com or interact with their servers.  
> Users must manually download HTML files from [FBRef](https://fbref.com/) and use them locally. Please ensure you comply with [FBRef's Terms of Use](https://www.sports-reference.com/termsofuse.html) or any applicable data policies when using this tool.

## Features

- Parses statistics from user-saved FBRef Player Comparison HTML pages
- Compares multiple players based on specified statistics
- Computes per-90-minute values for applicable metrics
- Customizable radar charts:
  - Polygonal or smooth outlines
  - Background, text, and grid colors
  - Custom fonts and title prefix
- Command-line interface with flexible flags for customization

## Example Output

![Example Radar Chart](examples/example_chart.png)

## Setup and Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/fbref-comparison-radar.git
cd fbref-comparison-radar
```

2. **Create and activate a virtual environment (optional but recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/macOS
# .\venv\Scripts\activate  # For Windows CMD
# .\venv\Scripts\Activate.ps1  # For PowerShell
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download HTML files manually from FBRef**
- Navigate to the Player Comparison tool on FBRef
- Save the page as "Webpage, Complete"
- Place the `.html` file in the `htmls/` directory

## Usage

### Basic
```bash
python multi_player_radar.py scrk-ucl
```

### With Specific Players
```bash
python multi_player_radar.py scrk-ucl \
    --players "Chiesa Federico" "Rashford Marcus"
```

### Save Output with Custom Title
```bash
python multi_player_radar.py scrk-ucl --save \
    --title "Winger Comparison" --output-dir data_viz
```

### Customize Appearance
```bash
python multi_player_radar.py scrk-ucl --polygonal --bgcolor "#2C2C2C" \
    --textcolor "#EDEDED" --circlecolor "gray"
```

### View All Options
```bash
python multi_player_radar.py --help
```

## Repository Structure

- `multi_player_radar.py` — Main script
- `requirements.txt` — Dependencies
- `README.md` — Documentation
- `htmls/` — Place your downloaded HTML files here
- `data_viz/` — Default output directory
- `examples/` — Example image(s) for README

## Dependencies

- Python 3.8+
- BeautifulSoup4
- NumPy
- Matplotlib
