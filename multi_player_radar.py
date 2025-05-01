#!/usr/bin/env python3

import argparse
import os
import sys
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from bs4 import BeautifulSoup, Tag
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, font_manager
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.font_manager import FontProperties

def load_html_file(path_to_file: str) -> str:
    """Loads HTML content from a file within the './htmls' directory."""
    file_path = os.path.join('./htmls', path_to_file + '.html')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{path_to_file}.html' not found in {os.path.abspath('./htmls/')}")
    except IOError as e:
        raise IOError(f"Error reading file '{path_to_file}.html': {e}")

def extract_players_and_spans(soup: BeautifulSoup) -> Dict[str, str]:
    """Extracts player names and their playing spans from the soup object."""
    players_with_span: Dict[str, str] = {}
    player_rows: List[Tag] = soup.find_all('th', {'data-stat': 'player', 'csk': True})
    for row in player_rows:
        player_name: str = row['csk']
        span_tag: Optional[Tag] = row.find_next('td', {'data-stat': 'span'})
        span: str = span_tag.text.strip() if span_tag else "N/A"
        # Assumes the first occurrence of a player name is the primary one if duplicates exist
        if player_name not in players_with_span:
            players_with_span[player_name] = span
    return players_with_span

def get_data_stat(soup: BeautifulSoup, aria_label: str) -> str:
    """Finds the 'data-stat' attribute value corresponding to an 'aria-label'."""
    header: Optional[Tag] = soup.find('th', {'aria-label': aria_label.strip()})
    if header and 'data-stat' in header.attrs:
        return header['data-stat']
    raise ValueError(f"Aria-label '{aria_label}' not found or missing 'data-stat'.")

def extract_stat(soup: BeautifulSoup, data_stat: str, selected_players: List[str]) -> Dict[str, str]:
    """Extracts a specific statistic ('data_stat') for a list of players."""
    player_stats: Dict[str, str] = {}
    for player in selected_players:
        stat_value: str = 'N/A'
        player_row_headers: List[Tag] = soup.find_all('th', {'csk': player})
        for row_header in player_row_headers:
            row: Optional[Tag] = row_header.find_parent('tr')
            if row:
                cell: Optional[Tag] = row.find('td', {'data-stat': data_stat})
                if cell and cell.text:
                    stat_value = cell.text.strip()
                    break  # Found the stat for this player
        player_stats[player] = stat_value
    return player_stats

def adjust_stats_by_nineties(all_player_stats: Dict[str, Dict[str, str]], nineties_played: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Adjusts raw stats to per-90-minute values where applicable."""
    adjusted_stats: Dict[str, Dict[str, str]] = {}
    for stat_name, player_values in all_player_stats.items():
        # Adjust if it's a countable stat (not inherently a rate or percentage)
        if '/' not in stat_name and '%' not in stat_name and '90s' not in stat_name.lower():
            adjusted_stat_name = f"{stat_name}/90"
            adjusted_stats[adjusted_stat_name] = {}
            for player, value in player_values.items():
                try:
                    player_90s_str = nineties_played.get(player, 'N/A')
                    if value != 'N/A' and player_90s_str != 'N/A' and player_90s_str:
                        player_90s = float(player_90s_str)
                        # Avoid division by zero or near-zero 90s played
                        if player_90s > 0.1:
                            val = float(value) / player_90s
                            adjusted_stats[adjusted_stat_name][player] = round(val, 2)
                        else:
                             adjusted_stats[adjusted_stat_name][player] = 0.0 # Or 'N/A' if preferred
                    else:
                        adjusted_stats[adjusted_stat_name][player] = 'N/A'
                except (ValueError, TypeError):
                    adjusted_stats[adjusted_stat_name][player] = 'N/A'
        else:
            # Keep stats that are already rates (e.g., Goals/Shot) or percentages as they are
            adjusted_stats[stat_name] = player_values
    return adjusted_stats

def add_line_breaks(text: str, line_length: int = 70) -> str:
    """Adds line breaks to a string to ensure it fits within a specified length."""
    lines: List[str] = []
    while len(text) > line_length:
        # Find the last ' vs. ' or space within the limit
        split_idx = text.rfind(' vs. ', 0, line_length)
        if split_idx == -1:
            split_idx = text.rfind(' ', 0, line_length)
        # If no space found, force break at line_length
        if split_idx == -1:
            split_idx = line_length
        # Adjust index to include the delimiter or space if found
        if text[split_idx:split_idx+5] == ' vs. ':
            lines.append(text[:split_idx + 5])
            text = text[split_idx + 5:]
        elif text[split_idx] == ' ':
             lines.append(text[:split_idx + 1])
             text = text[split_idx + 1:]
        else: # Force break case
             lines.append(text[:split_idx])
             text = text[split_idx:]
    lines.append(text)
    return '\n'.join(lines)


def plot_radar_chart(
    adjusted_stats: Dict[str, Dict[str, Any]],
    selected_players: List[str],
    titleStart: Optional[str] = None,
    polygonal: bool = False,
    bg: str = 'white',
    text_color: str = 'black',
    circle_color: str = 'black',
    save_path: Optional[str] = None,
    legendXOffset: float = 0.5,
    legendYOffset: float = -0.3,
    plotMarker: str = 'o',
    fontFamily: str = 'Helvetica'
) -> None:
    """Generates and displays/saves a radar chart comparing players."""

    categories: List[str] = list(adjusted_stats.keys())
    if not categories:
        print("No stats available to plot.")
        return

    # Calculate max values safely, handling 'N/A'
    stat_max: Dict[str, float] = {}
    for stat in categories:
        valid_vals = [float(adjusted_stats[stat][p]) for p in selected_players if adjusted_stats[stat].get(p, 'N/A') != 'N/A']
        stat_max[stat] = max(valid_vals) * 1.07 if valid_vals else 1.0 # Use 1.0 if no valid data

    # Normalize stats, handling 'N/A' by mapping to 0 for plotting
    player_stats_normalized: Dict[str, List[float]] = {}
    for p in selected_players:
         player_stats_normalized[p] = []
         for stat in categories:
            val_str = adjusted_stats[stat].get(p, 'N/A')
            try:
                val = float(val_str) if val_str != 'N/A' else 0.0
                # Avoid division by zero if max is 0
                norm_val = (val / stat_max[stat]) if stat_max[stat] != 0 else 0.0
                player_stats_normalized[p].append(norm_val)
            except (ValueError, TypeError):
                 player_stats_normalized[p].append(0.0) # Default to 0 if conversion fails

    angles: List[float] = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Close the loop

    # Add the first stat value to the end to close the radar shape
    for p in selected_players:
        player_stats_normalized[p] += player_stats_normalized[p][:1]

    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    colors = cm.viridis(np.linspace(0, 1, len(selected_players)))
    alphas = np.linspace(0.15, 0.65, len(categories))
    rotate = max(1, math.floor(len(categories) / len(selected_players)))

    for i, player in enumerate(selected_players):
        stats_to_plot = player_stats_normalized[player]
        if polygonal:
            # Fill segment by segment for polygonal effect
            for j, alpha in enumerate(alphas):
                ax.fill(
                    angles[j:j+2] + [0],      # Angles for the segment + origin
                    stats_to_plot[j:j+2] + [0], # Stats for the segment + origin
                    color=colors[i],
                    alpha=alpha
                )
        else:
            # Standard fill
            ax.fill(angles, stats_to_plot, color=colors[i], alpha=0.35)

        # Plot the line outline
        ax.plot(angles, stats_to_plot, color=colors[i], linewidth=2.5,
                marker=plotMarker, markersize=7, markerfacecolor=colors[i], label=player)
        alphas = np.roll(alphas, rotate)

    # Font properties
    try:
        font_props = FontProperties(family=fontFamily, size=11)
        title_font_props = FontProperties(family=fontFamily, size=17, weight='bold')
    except ValueError:
        print(f"Warning: Font family '{fontFamily}' not found. Using default.")
        font_props = FontProperties(size=11)
        title_font_props = FontProperties(size=16, weight='bold')


    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font_props, color=text_color)

    # Adjust label rotation and alignment for better readability
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        angle_deg = np.degrees(angle)
        if 90 < angle_deg < 270:
            label.set_rotation(angle_deg + 180)
            label.set_horizontalalignment('right')
        else:
            label.set_rotation(angle_deg)
            label.set_horizontalalignment('left')
        # Add a small radial offset to prevent overlap with the plot
        label.set_position((label.get_position()[0], label.get_position()[1] + 0.02))


    ax.spines['polar'].set_color(circle_color)
    ax.spines['polar'].set_linewidth(2)
    ax.xaxis.grid(True, color=circle_color, linestyle='--', linewidth=0.5)
    ax.yaxis.grid(True, color=circle_color, linestyle='--', linewidth=0.5)
    ax.set_ylim(0, 1.05) # Add slight padding to ylim
    ax.set_yticks(np.linspace(0.2, 1.0, 5))
    ax.set_yticklabels([])

    # Title formatting
    title_prefix = f"{titleStart}:\n" if titleStart else ""
    # Adjust line length for potentially smaller title font
    title_text = title_prefix + add_line_breaks(' vs. '.join(selected_players), 45)
    ax.set_title(title_text, fontproperties=title_font_props, color=text_color, y=1.15) # Adjust y pos

    # Legend formatting
    legend: Legend = ax.legend(loc='lower center', bbox_to_anchor=(legendXOffset, legendYOffset),
                               ncol=min(len(selected_players), 3),
                               facecolor=bg, framealpha=0.7, prop=font_props)
    plt.setp(legend.get_texts(), color=text_color)

    # Adjust subplot margins to prevent overlap
    fig.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)

    if save_path:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), pad_inches=0.5)
            print(f"Chart saved to: {save_path}")
        except Exception as e:
             print(f"Error saving file to {save_path}: {e}")

    plt.show()

def main() -> None:
    """
    Command-Line Interface for generating radar charts from FBRef HTML table snapshots.

    Parses arguments, loads data, processes stats, and generates the plot.
    """
    parser = argparse.ArgumentParser(
        description="Generate radar chart for selected football players from saved FBRef HTML.",
        formatter_class=argparse.RawTextHelpFormatter # Keep formatting in help text
        )
    parser.add_argument(
        "filename",
        help="Base name of the HTML file (without .html extension) located in the './htmls/' directory."
        )
    parser.add_argument(
        "--players",
        nargs="+",
        metavar='PLAYER_NAME',
        help="List of exact player names (case-sensitive) as they appear in the HTML (e.g., \"Rashford Marcus\").\nIf omitted, all players found in the file will be plotted."
        )
    parser.add_argument(
        "--stats",
        nargs="+",
        metavar='STAT_ARIA_LABEL',
        default=['npxG + xAG', 'Progressive Passes', 'Successful Take-Ons', 'Goals/Shot', 'Shot-Creating Actions', 'Total Carrying Distance'],
        help="List of exact stat 'aria-label' strings from the HTML table header to include in the chart.\nDefault: Basic attacking/creation stats."
        )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the plot as a PNG file."
        )
    parser.add_argument(
        "--output",
        metavar='FILENAME.png',
        help="Specify the output filename for the saved plot (relative to --output-dir or absolute).\nOverrides the default generated filename."
        )
    parser.add_argument(
        "--output-dir",
        default="data_viz",
        metavar='DIRECTORY',
        help="Directory to save the plot file (default: data_viz)."
        )
    parser.add_argument(
        "--title",
        metavar='PREFIX',
        help="Custom prefix for the chart title (e.g., 'Premier League 23/24')."
        )
    parser.add_argument(
        "--polygonal",
        action="store_true",
        default=False,
        help="Use polygonal fill styling instead of standard fill (default: off)."
        )
    parser.add_argument(
        "--theme",
        choices=['dark', 'light'],
        default='dark',
        help="Choose plot theme (dark or light, default: dark)."
        )

    args = parser.parse_args()

    # Determine theme colors
    if args.theme == 'dark':
        bg_color, text_color, circle_color = "#2C2C2C", "white", "gray"
    else:
        bg_color, text_color, circle_color = "#F5F5F5", "black", "gray"

    # Sanitize filename
    safe_name = ''.join(c for c in args.filename if c.isalnum() or c in ('-', '_')).rstrip()

    try:
        html_content = load_html_file(args.filename) # Use original arg for loading
    except (FileNotFoundError, IOError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract all players available in the file
    try:
        player_spans = extract_players_and_spans(soup)
        all_players = list(player_spans.keys())
        if not all_players:
            print("Error: No players found in the HTML file.")
            sys.exit(1)
    except Exception as e:
         print(f"Error parsing player data: {e}")
         sys.exit(1)


    # Filter players based on user input or use all
    if args.players:
        selected_players = [p for p in all_players if p in args.players]
        missing = [p for p in args.players if p not in selected_players]
        if missing:
            # Provide feedback on missing players and list available ones
            print(f"\nWarning: Skipped players not found: {', '.join(missing)}")
            print(f"Available players in '{args.filename}.html':")
            for name, span in player_spans.items():
                print(f"  - {name} ({span})")
            print("\nPlease check spelling and case sensitivity matches FBRef.")
            if not selected_players:
                 print("\nError: None of the specified players were found.")
                 sys.exit(1)
    else:
        selected_players = all_players
        if len(selected_players) > 10: # Warn if plotting too many players
             print(f"Warning: Plotting all {len(selected_players)} players found. Chart may become cluttered.")

    print(f"\nSelected players for chart: {', '.join(selected_players)}")

    # Extract selected stats
    all_stats_raw: Dict[str, Dict[str, str]] = {}
    stat_data_stat_map: Dict[str, str] = {}
    print("\nExtracting stats:")
    for stat_label in args.stats:
        try:
            data_stat = get_data_stat(soup, stat_label)
            stat_data_stat_map[stat_label] = data_stat # Store mapping for potential later use
            all_stats_raw[stat_label] = extract_stat(soup, data_stat, selected_players)
            print(f"  - Extracted '{stat_label}' (data-stat: '{data_stat}')")
        except ValueError as e:
            print(f"  - Warning: Could not find stat '{stat_label}'. Skipping. ({e})")
        except Exception as e:
            print(f"  - Warning: Error extracting stat '{stat_label}'. Skipping. ({e})")

    if not all_stats_raw:
        print("\nError: No valid stats could be extracted based on provided labels. Check --stats arguments.")
        sys.exit(1)

    # Extract 90s played for adjustment
    try:
        nineties_data_stat = get_data_stat(soup, '90s Played')
        nineties = extract_stat(soup, nineties_data_stat, selected_players)
        print(f"  - Extracted '90s Played' (data-stat: '{nineties_data_stat}') for adjustments.")
    except ValueError as e:
        print(f"\nWarning: Could not find '90s Played' stat. Cannot calculate per-90 values. ({e})")
        # Proceed without adjustment, maybe rename stats to indicate they are totals?
        adjusted_stats = all_stats_raw # Use raw totals if 90s not found
    except Exception as e:
         print(f"\nWarning: Error extracting '90s Played'. Cannot calculate per-90 values. ({e})")
         adjusted_stats = all_stats_raw
    else:
        # Adjust stats to per-90
        adjusted_stats = adjust_stats_by_nineties(all_stats_raw, nineties)
        print("\nAdjusted stats to per-90 values where applicable.")


    # Determine save path logic
    final_save_path: Optional[str] = None
    if args.save:
        # Ensure output directory exists
        try:
            os.makedirs(args.output_dir, exist_ok=True)
        except OSError as e:
             print(f"Error creating output directory '{args.output_dir}': {e}")
             # Optionally decide whether to exit or just disable saving
             args.save = False # Disable saving if dir creation fails

        if args.save: # Re-check in case it was disabled
            if args.output:
                # If output path is absolute, use it directly. Otherwise, join with output_dir.
                if os.path.isabs(args.output):
                     final_save_path = args.output
                else:
                     final_save_path = os.path.join(args.output_dir, args.output)
            else:
                # Generate default filename
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Added seconds
                # Use the sanitized base name from the input file
                filename = f"{safe_name}-radar-{date_str}.png"
                final_save_path = os.path.join(args.output_dir, filename)

    # Plot the chart
    try:
        print("\nGenerating plot...")
        plot_radar_chart(
            adjusted_stats=adjusted_stats,
            selected_players=selected_players,
            titleStart=args.title,
            polygonal=args.polygonal,
            bg=bg_color,
            text_color=text_color,
            circle_color=circle_color,
            save_path=final_save_path
        )
    except Exception as e:
        print(f"\nError during plotting: {e}")
        # Consider logging the traceback here for debugging if needed
        # import traceback
        # traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()