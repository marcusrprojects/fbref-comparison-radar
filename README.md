# FBRef Player Comparison Radar Chart Generator

![Language](https://img.shields.io/badge/Language-Python-blue.svg)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
![Libraries](https://img.shields.io/badge/Libraries-BeautifulSoup4%20|%20NumPy%20|%20Matplotlib-orange.svg)

## Overview

This Python CLI tool (`multi_player_radar.py`) parses saved player comparison pages from [FBRef.com](https://fbref.com/) and generates radar (spider) charts visualizing selected footballers across performance metrics. It supports per-90-minute adjustments, customizable output, and clean visualizations using `matplotlib`.

## Features

- Parses saved FBRef player comparison HTML pages.
- Compares multiple players on selected stats.
- Calculates per-90-minute values for most metrics.
- Highly customizable radar chart output:
  - Dark/light themes
  - Optional polygonal fill style
  - Adjustable font, text color, and title
- Saves plot as a PNG (optional).
- Works via CLI with flexible arguments.

## Example Output

![UCL - Messi, CR7, Neymar Radar Chart](./data_viz/t3-17-24-radar-20250430_1401.png)

## Setup and Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. (Optional) Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Save your FBRef HTML file:
    - Go to FBRef's [Player Comparison](https://fbref.com/) page.
    - Select players and comparison table.
    - Save the **complete HTML page** in `./htmls/`.

## Usage

Basic usage:
```bash
python multi_player_radar.py t3-17-24
```

With custom player list:
```bash
python multi_player_radar.py t3-17-24 \
    --players "Sancho Jadon" "Chiesa Federico"
```

With output and title:
```bash
python multi_player_radar.py t3-17-24 \
    --save --output-dir mycharts \
    --title "Top Wingers"
```

Enable polygonal fill style:
```bash
python multi_player_radar.py t3-17-24 --polygonal
```

See full options:
```bash
python multi_player_radar.py --help
```

## Files

- `multi_player_radar.py`: The radar chart generator script.
- `htmls/`: Place your FBRef HTML files here.
- `data_viz/`: Default directory for saved plots.
- `requirements.txt`: Python dependencies.
- `README.md`: Project documentation.

## Dependencies

- Python 3.8+
- Beautiful Soup 4 (`beautifulsoup4`)
- NumPy (`numpy`)
- Matplotlib (`matplotlib`)

## Disclaimer

This tool is intended for personal and educational use only. It does **not** scrape or interact with FBRef.com or its servers in any way.

Users must manually download HTML files from [FBRef](https://fbref.com/) and use them locally. Please ensure you comply with [FBRef's Terms of Use](https://www.sports-reference.com/termsofuse.html) or any applicable data policies when using this tool.
