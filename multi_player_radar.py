#!/usr/bin/env python3

import argparse
import os
import sys
import math
from datetime import datetime

from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, font_manager

def load_html_file(path_to_file):
    try:
        with open(os.path.join('./htmls', path_to_file + '.html'), 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{path_to_file}.html' not found in ./htmls/")
    except IOError as e:
        raise IOError(f"Error reading file '{path_to_file}.html': {e}")

def extract_players_and_spans(soup):
    players_with_span = {}
    player_rows = soup.find_all('th', {'data-stat': 'player', 'csk': True})
    for row in player_rows:
        player_name = row['csk']
        span = row.find_next('td', {'data-stat': 'span'}).text.strip()
        if player_name not in players_with_span:
            players_with_span[player_name] = span
        else:
            break
    return players_with_span

def get_data_stat(soup, aria_label):
    header = soup.find('th', {'aria-label': aria_label.strip()})
    if header:
        return header['data-stat']
    raise ValueError(f"Aria-label '{aria_label}' not found.")

def extract_stat(soup, data_stat, selected_players):
    player_stats = {}
    for player in selected_players:
        stat_value = 'N/A'
        player_rows = soup.find_all('th', {'csk': player})
        for row_header in player_rows:
            row = row_header.find_parent('tr')
            cell = row.find('td', {'data-stat': data_stat})
            if cell:
                stat_value = cell.text.strip()
                break
        player_stats[player] = stat_value
    return player_stats

def adjust_stats_by_nineties(all_player_stats, nineties_played):
    adjusted_stats = {}
    for stat_name, player_values in all_player_stats.items():
        if '/' not in stat_name and '%' not in stat_name:
            adjusted_stats[stat_name + '/90'] = {}
            for player, value in player_values.items():
                try:
                    if value != 'N/A' and nineties_played.get(player, 'N/A') != 'N/A':
                        val = float(value) / float(nineties_played[player] or 1)
                        adjusted_stats[stat_name + '/90'][player] = round(val, 2)
                    else:
                        adjusted_stats[stat_name + '/90'][player] = 'N/A'
                except ValueError:
                    adjusted_stats[stat_name + '/90'][player] = 'N/A'
        else:
            adjusted_stats[stat_name] = player_values
    return adjusted_stats

def add_line_breaks(players_string, line_length=70):
    lines = []
    while len(players_string) > line_length:
        idx = players_string.rfind(' vs. ', 0, line_length)
        if idx == -1:
            idx = players_string.rfind(' ', 0, line_length)
        if idx == -1:
            idx = line_length
        lines.append(players_string[:idx + 1])
        players_string = players_string[idx + 1:]
    lines.append(players_string)
    return '\n'.join(lines)

def plot_radar_chart(adjusted_stats, selected_players, titleStart=None, polygonal=False,
                     bg='white', text_color='black', circle_color='black',
                     save_path=None, legendXOffset=.5, legendYOffset=-.3,
                     plotMarker='o', fontFamily='Helvetica'):

    stat_max = {stat: max(float(adjusted_stats[stat][p]) for p in selected_players) * 1.07
                for stat in adjusted_stats}
    categories = list(adjusted_stats.keys())
    player_stats = {
        p: [float(adjusted_stats[stat][p]) / stat_max[stat] for stat in categories]
        for p in selected_players
    }

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    for p in selected_players:
        player_stats[p] += player_stats[p][:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    colors = cm.rainbow(np.linspace(0, 1, len(selected_players)))
    alphas = np.linspace(0.1, 0.6, len(categories))
    rotate = max(1, math.floor(len(categories) / len(selected_players)))

    for i, player in enumerate(selected_players):
        if polygonal:
            for j, alpha in enumerate(alphas):
                ax.fill(
                    angles[j:j+2] + [0],
                    player_stats[player][j:j+2] + [0],
                    color=colors[i],
                    alpha=alpha
                )
        else:
            ax.fill(angles, player_stats[player], color=colors[i], alpha=0.3)

        ax.plot(angles, player_stats[player], color=colors[i], linewidth=2,
                marker=plotMarker, markersize=8, markerfacecolor=colors[i], label=player)
        alphas = np.roll(alphas, rotate)

    font_props = font_manager.FontProperties(family=fontFamily, size=12)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font_props, color=text_color)
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        angle_deg = np.degrees(angle)
        if 90 <= angle_deg < 270:
            label.set_rotation(angle_deg - 180)
            label.set_horizontalalignment('right')
        else:
            label.set_rotation(angle_deg)
            label.set_horizontalalignment('left')

    ax.spines['polar'].set_color(circle_color)
    ax.spines['polar'].set_linewidth(2.5)
    ax.xaxis.grid(True, color=circle_color, linestyle='dashed')
    ax.yaxis.grid(True, color=circle_color, linestyle='dashed')
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_yticklabels([])

    title_prefix = f"{titleStart}:\n" if titleStart else ""
    title_text = title_prefix + add_line_breaks(' vs. '.join(selected_players), 50)
    ax.set_title(title_text, fontproperties=font_manager.FontProperties(family=fontFamily, size=18, weight='bold'),
                 color=text_color, y=1.13)

    legend = ax.legend(loc='lower right', bbox_to_anchor=(legendXOffset, legendYOffset),
                       facecolor=bg, framealpha=0.5, prop=font_props)
    plt.setp(legend.get_texts(), color=text_color)
    fig.subplots_adjust(left=0.15, right=0.85)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.1)

    plt.show()

def main():
    """
    CLI for generating radar charts from FBRef HTML table snapshots.

    Example:
        python multi_player_radar.py scrk-ucl --save
        python multi_player_radar.py scrk-ucl --players "Rashford Marcus" "Chiesa Federico"
    """
    parser = argparse.ArgumentParser(description="Generate radar chart for selected football players.")
    parser.add_argument("filename", help="HTML file (no extension) in ./htmls/")
    parser.add_argument("--players", nargs="+", help="List of player names (exact match)")
    parser.add_argument("--save", action="store_true", help="Save the plot as PNG")
    parser.add_argument("--output", help="Output PNG filename")
    parser.add_argument("--output-dir", default="data_viz", help="Directory to save file")
    parser.add_argument("--title", default="UCL 2018+", help="Title prefix")
    parser.add_argument("--polygonal", action="store_true", default=False, help="Use polygonal fill styling (default: off)")
    args = parser.parse_args()

    safe_name = ''.join(c for c in args.filename if c.isalnum() or c in ('-', '_')).rstrip()
    html_content = load_html_file(safe_name)
    soup = BeautifulSoup(html_content, 'html.parser')

    player_spans = extract_players_and_spans(soup)
    all_players = list(player_spans.keys())

    if args.players:
        selected_players = [p for p in all_players if p in args.players]
        missing = [p for p in args.players if p not in all_players]
        if missing:
            print(f"Warning: Skipped players not found: {missing}")
    else:
        selected_players = all_players

    if not selected_players:
        print("No valid players selected. Exiting.")
        sys.exit(1)

    print(f"Selected players: {selected_players}")

    stats = ['npxG + xAG', 'Progressive Passes', 'Successful Take-Ons',
             'Goals/Shot', 'Shot-Creating Actions', 'Total Carrying Distance']

    all_stats = {stat: extract_stat(soup, get_data_stat(soup, stat), selected_players) for stat in stats}
    nineties = extract_stat(soup, get_data_stat(soup, '90s Played'), selected_players)
    adjusted = adjust_stats_by_nineties(all_stats, nineties)

    # Save logic
    final_save_path = None
    if args.save:
        os.makedirs(args.output_dir, exist_ok=True)
        if args.output:
            final_save_path = os.path.join(args.output_dir, args.output) if not os.path.dirname(args.output) else args.output
        else:
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{safe_name}-radar-{date_str}.png"
            final_save_path = os.path.join(args.output_dir, filename)

    plot_radar_chart(
        adjusted_stats=adjusted,
        selected_players=selected_players,
        titleStart=args.title,
        polygonal=args.polygonal,
        bg="#2C2C2C",
        text_color="white",
        circle_color="gray",
        save_path=final_save_path
    )

if __name__ == "__main__":
    main()