# radar_plotter.py
"""
Generates customizable radar (spider) charts comparing football player statistics
scraped from saved FBRef player comparison HTML files.

This script parses a previously saved HTML file from FBRef's player comparison
tool, extracts specified statistics for selected players, calculates per 90-minute
values where appropriate, and plots the results on a radar chart using Matplotlib.
Plot aesthetics are configurable via command-line arguments.
"""

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager, cm
from matplotlib.patches import Polygon
from bs4 import BeautifulSoup
import math
from typing import List, Dict, Tuple, Any, Optional

# --- Constants ---
HTML_DIR_DEFAULT: str = './htmls'
PER_90_SUFFIX: str = '/90'
PERCENTAGE_CHAR: str = '%'
NA_VALUE: str = 'N/A'
DEFAULT_STATS: List[str] = [
    'npxG + xAG', 'Progressive Passes',
    'Successful Take-Ons', 'Goals/Shot',
    'Shot-Creating Actions', 'Total Carrying Distance'
]
DEFAULT_BG_COLOR: str = '#2C2C2C'
DEFAULT_TEXT_COLOR: str = 'white'
DEFAULT_CIRCLE_COLOR: str = 'white'
DEFAULT_FONT_FAMILY: str = 'Helvetica' # Ensure this font is available on the system
PLOT_MARKER: str = 'o'
MAX_VALUE_SCALE_FACTOR: float = 1.07
LEGEND_X_OFFSET: float = 0.5
LEGEND_Y_OFFSET: float = -0.3
TITLE_LINE_LENGTH: int = 50


# --- Core Functions ---

def load_html_file(dir_path: str, file_name_base: str) -> str:
    """
    Loads HTML content from a file within the specified directory.

    Args:
        dir_path: The directory containing the HTML files.
        file_name_base: The base name of the HTML file (without .html extension).

    Returns:
        The HTML content as a string.

    Raises:
        FileNotFoundError: If the HTML file cannot be found.
        IOError: If there's an error reading the file.
    """
    file_path = os.path.join(dir_path, f"{file_name_base}.html")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        print(f"Successfully loaded HTML file: {file_path}")
        return html_content
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File '{file_path}' not found. Please check the path and filename.")
    except IOError as e:
        raise IOError(f"Error reading file '{file_path}': {e}")

def extract_players_and_spans(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts player names and their corresponding season spans from the main table.

    Finds the first occurrence of each player in the table and their associated
    'span' data, stopping when player names start repeating.

    Args:
        soup: A BeautifulSoup object representing the parsed HTML.

    Returns:
        A dictionary mapping player names (str) to their season spans (str).
    """
    players_with_span: Dict[str, str] = {}
    # Find player rows based on the 'csk' attribute which typically holds the name
    player_rows = soup.find_all('th', {'data-stat': 'player', 'csk': True})

    if not player_rows:
        print("Warning: No player rows found with 'csk' attribute. Check HTML structure.")
        return {}

    for row in player_rows:
        player_name = row.get('csk')
        if not player_name:
            continue # Skip if 'csk' attribute is missing

        # Find the adjacent 'span' cell in the same row
        span_cell = row.find_next_sibling('td', {'data-stat': 'span'})
        if span_cell:
            span = span_cell.text.strip()
        else:
            span = "N/A" # Default if span cell not found

        # Add if player not seen before, break if player repeats (signals end of first block)
        if player_name not in players_with_span:
            players_with_span[player_name] = span
        else:
            break # Stop when we see a player for the second time

    if not players_with_span:
        print("Warning: Could not extract any player names and spans.")

    return players_with_span

def get_data_stat(soup: BeautifulSoup, aria_label: str) -> str:
    """
    Finds the 'data-stat' attribute corresponding to a given 'aria-label' in table headers.

    Args:
        soup: A BeautifulSoup object representing the parsed HTML.
        aria_label: The 'aria-label' value to search for in <th> tags.

    Returns:
        The corresponding 'data-stat' attribute value as a string.

    Raises:
        ValueError: If the aria-label is not found in any table header.
    """
    header = soup.find('th', {'aria-label': aria_label})
    if header and 'data-stat' in header.attrs:
        return header['data-stat']
    else:
        raise ValueError(f"Error: Aria-label '{aria_label}' not found or missing 'data-stat' attribute in table headers.")

def extract_stat(soup: BeautifulSoup, data_stat: str, selected_players: List[str]) -> Dict[str, str]:
    """
    Extracts a specific statistic ('data-stat') for a list of selected players.

    Finds the first row matching each player and extracts the stat value from the
    cell corresponding to the given data_stat.

    Args:
        soup: A BeautifulSoup object representing the parsed HTML.
        data_stat: The 'data-stat' attribute identifying the statistic column.
        selected_players: A list of player names (matching 'csk' attributes).

    Returns:
        A dictionary mapping player names (str) to their stat values (str).
        Returns NA_VALUE if a stat is not found for a player.
    """
    player_stats: Dict[str, str] = {}

    for player in selected_players:
        stat_value = NA_VALUE # Default

        # Find the first header cell matching the player's 'csk' name
        player_header = soup.find('th', {'csk': player})

        if player_header:
            # Find the parent row <tr>
            player_row = player_header.find_parent('tr')
            if player_row:
                # Find the specific stat cell within that row
                stat_cell = player_row.find('td', {'data-stat': data_stat})
                if stat_cell:
                    stat_value = stat_cell.text.strip()
                    if not stat_value: # Handle empty cells
                        stat_value = NA_VALUE
            else:
                 print(f"Warning: Could not find parent row for player '{player}'.")
        else:
            print(f"Warning: Could not find header cell for player '{player}' with csk attribute.")

        player_stats[player] = stat_value

    return player_stats

def adjust_stats_by_nineties(
    all_player_stats: Dict[str, Dict[str, str]],
    nineties_played: Dict[str, str]
) -> Dict[str, Dict[str, Any]]:
    """
    Adjusts raw statistics to per 90-minute values where appropriate.

    Stats ending in '%' or containing '/' are not adjusted. Others are divided
    by the '90s Played' value for each player.

    Args:
        all_player_stats: Dict where keys are stat names (aria-labels) and
                          values are dicts mapping player names to raw stat strings.
        nineties_played: Dict mapping player names to their '90s Played' stat string.

    Returns:
        A dictionary with adjusted stats. Keys might be original stat names or
        have PER_90_SUFFIX appended. Values are dicts mapping player names to
        adjusted values (float or original string/NA_VALUE).
    """
    adjusted_stats: Dict[str, Dict[str, Any]] = {}

    for stat_name, players_stats in all_player_stats.items():
        # Determine if the stat should be adjusted (not a percentage or already per X)
        is_adjustable = PERCENTAGE_CHAR not in stat_name and '/' not in stat_name
        output_stat_name = stat_name + PER_90_SUFFIX if is_adjustable else stat_name
        adjusted_stats[output_stat_name] = {}

        for player, raw_value in players_stats.items():
            nineties_str = nineties_played.get(player, NA_VALUE)

            if is_adjustable:
                try:
                    # Attempt conversion and calculation
                    if raw_value != NA_VALUE and nineties_str != NA_VALUE:
                        raw_float = float(raw_value)
                        nineties_float = float(nineties_str)
                        if nineties_float > 0: # Avoid division by zero
                            adjusted_value = raw_float / nineties_float
                            adjusted_stats[output_stat_name][player] = round(adjusted_value, 2)
                        else:
                             adjusted_stats[output_stat_name][player] = 0.0 # Or NA_VALUE, depends on preference
                    else:
                        adjusted_stats[output_stat_name][player] = NA_VALUE
                except (ValueError, TypeError):
                    # Handle cases where conversion fails
                    print(f"Warning: Could not convert stat '{stat_name}' ({raw_value}) or 90s ({nineties_str}) to float for player '{player}'. Setting to N/A.")
                    adjusted_stats[output_stat_name][player] = NA_VALUE
            else:
                # Keep non-adjustable stats as they are (or try converting percentages)
                if raw_value == NA_VALUE:
                    adjusted_stats[output_stat_name][player] = NA_VALUE
                elif PERCENTAGE_CHAR in stat_name:
                     try: # Attempt to convert percentage string to float
                         adjusted_stats[output_stat_name][player] = round(float(raw_value.replace(PERCENTAGE_CHAR, '')), 2)
                     except (ValueError, TypeError):
                         adjusted_stats[output_stat_name][player] = NA_VALUE # Keep as string/NA if conversion fails
                else:
                     try: # Attempt conversion for other non-adjusted stats (like Goals/Shot)
                         adjusted_stats[output_stat_name][player] = round(float(raw_value), 2)
                     except (ValueError, TypeError):
                          adjusted_stats[output_stat_name][player] = raw_value # Keep as string if conversion fails


    return adjusted_stats

def add_line_breaks(text: str, line_length: int = TITLE_LINE_LENGTH) -> str:
    """
    Adds line breaks to a string to ensure lines don't exceed a max length.

    Attempts to break at the last ' vs. ' or space before the line length limit.

    Args:
        text: The input string.
        line_length: The maximum desired line length.

    Returns:
        The string with newline characters inserted.
    """
    lines: List[str] = []
    current_text = text.strip()

    while len(current_text) > line_length:
        break_point = -1
        # Try breaking at ' vs. ' first
        vs_index = current_text.rfind(' vs. ', 0, line_length)
        if vs_index != -1:
             # Break *after* ' vs. '
             break_point = vs_index + len(' vs. ') -1 # index of last char of ' vs. '
        else:
            # Try breaking at the last space
            space_index = current_text.rfind(' ', 0, line_length)
            if space_index != -1:
                break_point = space_index # index of the space
            else:
                # Force break if no suitable point found
                break_point = line_length -1 # index before cutoff

        lines.append(current_text[:break_point + 1].strip())
        current_text = current_text[break_point + 1:].strip()

    lines.append(current_text) # Add the remaining part
    return '\n'.join(lines)

def plot_radar_chart(
    plot_data: Dict[str, Dict[str, float]],
    selected_players: List[str],
    all_players_spans: Dict[str, str],
    categories: List[str],
    title_prefix: Optional[str] = None,
    polygonal: bool = True,
    bg_color: str = DEFAULT_BG_COLOR,
    text_color: str = DEFAULT_TEXT_COLOR,
    circle_color: str = DEFAULT_CIRCLE_COLOR,
    font_family: str = DEFAULT_FONT_FAMILY,
    save_path: Optional[str] = None
) -> None:
    """
    Generates and displays or saves a radar chart comparing player statistics.

    Args:
        plot_data: Dict where keys are category names (for axes) and values are
                   dicts mapping player names to their final numeric stat values.
                   Should only contain stats ready for plotting (already adjusted).
                   Assumes NA_VALUE has been handled or converted appropriately.
        selected_players: List of player names included in the chart.
        all_players_spans: Dict mapping all player names to their season spans (for legend).
        categories: List of category names (strings) corresponding to the keys in plot_data,
                    determining the order of axes on the radar chart.
        title_prefix: Optional string to prepend to the chart title.
        polygonal: If True, use the polygonal fill style; otherwise, use standard fill.
        bg_color: Background color of the plot.
        text_color: Color for text elements (title, labels, legend).
        circle_color: Color for the radar grid lines and spokes.
        font_family: Font family to use for text.
        save_path: If provided, saves the plot to this file path (e.g., 'chart.png').
                   If None, displays the plot interactively.
    """
    num_vars = len(categories)
    if num_vars < 3:
        print("Error: Need at least 3 statistics to plot a radar chart.")
        return

    # --- Data Preparation ---
    # Replace any remaining NA_VALUE or non-numeric with 0 for plotting
    # Also find max values *after* handling NA
    stat_max_values: Dict[str, float] = {}
    numeric_plot_data: Dict[str, Dict[str, float]] = {}

    for category in categories:
        numeric_plot_data[category] = {}
        max_val_for_cat = 0.0
        for player in selected_players:
            value = plot_data.get(category, {}).get(player, 0.0)
            try:
                num_value = float(value) if value != NA_VALUE else 0.0
            except (ValueError, TypeError):
                num_value = 0.0 # Default to 0 if conversion fails unexpectedly
            numeric_plot_data[category][player] = num_value
            # Ensure max is only compared with valid numbers, handle negative stats if necessary
            if isinstance(num_value, (int, float)):
                 max_val_for_cat = max(max_val_for_cat, num_value)

        # Apply scaling factor. Handle case where max is 0 or negative.
        stat_max_values[category] = max(max_val_for_cat * MAX_VALUE_SCALE_FACTOR, 0.01) # Avoid zero max


    # Normalize the stats for the radar plot (0 to 1 range)
    normalized_player_stats: Dict[str, List[float]] = {}
    for player in selected_players:
        normalized_stats = []
        for category in categories:
            player_val = numeric_plot_data.get(category, {}).get(player, 0.0)
            max_val = stat_max_values.get(category, 1.0) # Default max to 1 to avoid division by zero
            normalized = player_val / max_val if max_val else 0.0
            normalized_stats.append(max(0, min(normalized, 1))) # Clamp between 0 and 1
        normalized_player_stats[player] = normalized_stats


    # --- Plotting Setup ---
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] # Close the circle

    # Prepare stats lists for plotting (append first value to end)
    plot_values_closed: Dict[str, List[float]] = {}
    for player, stats in normalized_player_stats.items():
        plot_values_closed[player] = stats + stats[:1]

    # Font properties
    try:
        font_prop = font_manager.FontProperties(family=font_family, size=10)
        title_font_prop = font_manager.FontProperties(family=font_family, size=16, weight='bold')
        font_manager.findfont(font_prop) # Check if font is available
    except ValueError:
        print(f"Warning: Font '{font_family}' not found. Using default sans-serif.")
        font_prop = font_manager.FontProperties(family='sans-serif', size=10)
        title_font_prop = font_manager.FontProperties(family='sans-serif', size=16, weight='bold')


    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True)) # Slightly larger default size
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # Plot grid and labels first
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font_prop, color=text_color)

    # Set y-axis limits and remove default labels/ticks
    ax.set_ylim(0, 1)
    ax.set_yticks(np.linspace(0.2, 1.0, 5)) # Example: 5 grid circles
    ax.set_yticklabels([]) # Hide numeric labels on spokes

    # Style the grid lines
    ax.xaxis.grid(True, color=circle_color, linestyle='dashed', linewidth=0.8)
    ax.yaxis.grid(True, color=circle_color, linestyle='dashed', linewidth=0.8)
    ax.spines['polar'].set_color(circle_color)
    ax.spines['polar'].set_linewidth(1.5)

    # Rotate labels for readability
    for label, angle_rad in zip(ax.get_xticklabels(), angles[:-1]):
        angle_deg = np.degrees(angle_rad)
        if 0 < angle_deg < 180: # Top half
            label.set_horizontalalignment('center')
            label.set_verticalalignment('bottom' if angle_deg != 90 else 'center')
            label.set_rotation(angle_deg if angle_deg < 90 else angle_deg -180)
        elif 180 < angle_deg < 360: # Bottom half
             label.set_horizontalalignment('center')
             label.set_verticalalignment('top' if angle_deg != 270 else 'center')
             label.set_rotation(angle_deg-180 if angle_deg > 270 else angle_deg-180)
        else: # 0 or 180 degrees
            label.set_horizontalalignment('right' if angle_deg == 180 else 'left')
            label.set_verticalalignment('center')
            label.set_rotation(angle_deg)


    # --- Plot Player Data ---
    player_colors = cm.rainbow(np.linspace(0, 1, len(selected_players)))
    alphas = np.linspace(0.1, 0.6, num_vars) if polygonal else [0.3] * len(selected_players)
    # Ensure shuffle distance makes sense
    shuffle_distance = max(1, math.floor(num_vars / len(selected_players))) if len(selected_players) > 0 else 1

    for idx, player in enumerate(selected_players):
        data_to_plot = plot_values_closed[player]
        player_color = player_colors[idx]
        player_legend_label = f"{player}, {all_players_spans.get(player, 'N/A')}"

        if polygonal:
            # Plot individual polygon segments with varying alpha
            current_alphas = np.roll(alphas, idx * shuffle_distance)
            for i in range(num_vars):
                segment_angles = angles[i:i+2] + [0] # Angles for segment + center
                segment_values = data_to_plot[i:i+2] + [0] # Values for segment + center
                ax.fill(segment_angles, segment_values, color=player_color, alpha=current_alphas[i])
        else:
            # Standard fill for the whole area
            ax.fill(angles, data_to_plot, color=player_color, alpha=alphas[idx % len(alphas)]) # Use modulo for safety

        # Plot the outline
        ax.plot(angles, data_to_plot, color=player_color, linewidth=2,
                marker=PLOT_MARKER, markersize=6, markerfacecolor=player_color,
                label=player_legend_label)


    # --- Title and Legend ---
    title_str = f"{title_prefix}:\n" if title_prefix else ""
    players_str = add_line_breaks(" vs. ".join(selected_players), line_length=TITLE_LINE_LENGTH)
    full_title = title_str + players_str
    ax.set_title(full_title, fontproperties=title_font_prop, color=text_color, y=1.10) # Adjust y for spacing

    legend = ax.legend(loc='lower right',
                       bbox_to_anchor=(LEGEND_X_OFFSET, LEGEND_Y_OFFSET),
                       facecolor=bg_color, framealpha=0.6, prop=font_prop)
    plt.setp(legend.get_texts(), color=text_color)


    # --- Display or Save ---
    fig.tight_layout() # Adjust layout to prevent labels overlapping

    if save_path:
        try:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=bg_color, pad_inches=0.1)
            print(f"Chart saved to {save_path}")
        except Exception as e:
            print(f"Error saving chart to {save_path}: {e}")
    else:
        plt.show()

    plt.close(fig) # Close the figure to free memory

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate radar charts for FBRef player comparisons from saved HTML.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    parser.add_argument(
        "html_file_base",
        help="Base name of the HTML file (without .html extension) located in the HTML directory."
    )
    parser.add_argument(
        "-d", "--htmldir", default=HTML_DIR_DEFAULT,
        help="Directory containing the HTML files."
    )
    parser.add_argument(
        "-p", "--players", nargs='+',
        help="List of player names (case-sensitive, matching 'csk' attribute) to include. "
             "If omitted, uses all unique players found in the first table section."
    )
    parser.add_argument(
        "-s", "--stats", nargs='+', default=DEFAULT_STATS,
        help="List of stats (using the exact 'aria-label' from table headers) to plot."
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output file path for the plot image (e.g., plot.png). If omitted, displays the plot interactively."
    )
    parser.add_argument(
        "--title", default=None,
        help="Custom title prefix for the plot (e.g., 'UCL 2018+')."
    )
    parser.add_argument(
        "--polygonal", action='store_true',
        help="Use the alternative polygonal fill style instead of a solid fill."
    )
    parser.add_argument(
        "--bgcolor", default=DEFAULT_BG_COLOR,
        help="Background color (CSS name or hex code)."
    )
    parser.add_argument(
        "--textcolor", default=DEFAULT_TEXT_COLOR,
        help="Text color (CSS name or hex code)."
    )
    parser.add_argument(
        "--circlecolor", default=DEFAULT_CIRCLE_COLOR,
        help="Radar grid/spoke color (CSS name or hex code)."
    )
    parser.add_argument(
        "--font", default=DEFAULT_FONT_FAMILY,
        help="Font family name for plot text (must be installed on system)."
    )

    args = parser.parse_args()

    # --- Data Loading and Processing ---
    try:
        html_content = load_html_file(args.htmldir, args.html_file_base)
        soup = BeautifulSoup(html_content, 'html.parser')

        all_players_spans = extract_players_and_spans(soup)
        if not all_players_spans:
            print("Error: No players extracted from the HTML. Exiting.")
            exit(1)

        # Determine selected players
        if args.players:
            selected_players = []
            found_players = set(all_players_spans.keys())
            for p_arg in args.players:
                if p_arg in found_players:
                    selected_players.append(p_arg)
                else:
                    print(f"Warning: Requested player '{p_arg}' not found in the extracted players.")
            if not selected_players:
                print("Error: None of the specified players were found. Exiting.")
                exit(1)
        else:
            selected_players = list(all_players_spans.keys())

        print(f"Selected players for comparison: {', '.join(selected_players)}")
        print(f"Using stats: {', '.join(args.stats)}")

        # Extract raw stats
        raw_player_stats: Dict[str, Dict[str, str]] = {}
        stat_aria_labels_used = args.stats # Store the original aria-labels
        try:
            for stat_label in stat_aria_labels_used:
                data_stat = get_data_stat(soup, stat_label)
                raw_player_stats[stat_label] = extract_stat(soup, data_stat, selected_players)

            # Get 90s played stat
            nineties_data_stat = get_data_stat(soup, '90s Played')
            nineties_played = extract_stat(soup, nineties_data_stat, selected_players)
        except ValueError as e:
            print(f"Error: {e}")
            print("Please ensure the stat 'aria-label' names provided match the HTML source exactly.")
            exit(1)

        # Adjust stats for per 90
        adjusted_player_stats = adjust_stats_by_nineties(raw_player_stats, nineties_played)

        # Prepare final data dictionary and category list for plotting
        final_plot_data: Dict[str, Dict[str, float]] = {}
        plot_categories_final: List[str] = []
        for stat_label in stat_aria_labels_used:
             key_per90 = stat_label + PER_90_SUFFIX
             if key_per90 in adjusted_player_stats:
                 final_plot_data[key_per90] = adjusted_player_stats[key_per90]
                 plot_categories_final.append(key_per90) # Use the adjusted key as category label
             elif stat_label in adjusted_player_stats:
                 final_plot_data[stat_label] = adjusted_player_stats[stat_label]
                 plot_categories_final.append(stat_label) # Use original key
             else:
                 print(f"Warning: Stat '{stat_label}' (or its /90 version) was not found in adjusted stats and will be skipped.")

        if not final_plot_data or len(plot_categories_final) < 3:
            print("Error: Not enough valid statistics processed to generate a radar chart (minimum 3 required).")
            exit(1)

        # --- Plotting ---
        plot_radar_chart(
            plot_data=final_plot_data,
            selected_players=selected_players,
            all_players_spans=all_players_spans,
            categories=plot_categories_final,
            title_prefix=args.title,
            polygonal=args.polygonal,
            bg_color=args.bgcolor,
            text_color=args.textcolor,
            circle_color=args.circlecolor,
            font_family=args.font,
            save_path=args.output
        )

        print("Script finished.")

    except FileNotFoundError as e:
        print(e)
        exit(1)
    except IOError as e:
        print(e)
        exit(1)
    except Exception as e:
        # Catch other potential errors during processing/plotting
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        exit(1)