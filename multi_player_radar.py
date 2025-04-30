from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib import cm
import argparse
import math
import sys

def load_html_file(path_to_file):
    try:
        with open('./htmls/' + path_to_file + '.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
        return html_content
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{path_to_file}.html' not found.")
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
    header = soup.find('th', {'aria-label': aria_label})
    if header:
        return header['data-stat']
    raise ValueError(f"Aria-label '{aria_label}' not found.")

def extract_stat(soup, data_stat, selected_players):
    player_stats = {}
    for player in selected_players:
        stat_value = 'N/A'
        player_rows = soup.find_all('th', {'csk': player})
        for player_row_header in player_rows:
            player_row = player_row_header.find_parent('tr')
            stat_cell = player_row.find('td', {'data-stat': data_stat})
            if stat_cell:
                stat_value = stat_cell.text.strip()
                break
        player_stats[player] = stat_value
    return player_stats

def adjust_stats_by_nineties(all_player_stats, nineties_played):
    adjusted_stats = {}
    for stat_name, players_stats in all_player_stats.items():
        per90 = '/90'
        per = '/'
        percentage = '%'
        if not (per in stat_name) and not (percentage in stat_name):
            adjusted_stats[stat_name + per90] = {}
        else:
            adjusted_stats[stat_name] = {}
        for player, value in players_stats.items():
            try:
                if not (per in stat_name) and not (percentage in stat_name):
                    if value != 'N/A' and nineties_played[player] != 'N/A':
                        adjusted_value = float(value) / float(nineties_played[player])
                        adjusted_stats[stat_name + per90][player] = round(adjusted_value, 2)
                    else:
                        adjusted_stats[stat_name + per90][player] = 'N/A'
                else:
                    adjusted_stats[stat_name][player] = value
            except ValueError:
                adjusted_stats[stat_name][player] = 'N/A'
    return adjusted_stats

def add_line_breaks(players_string, line_length=70):
    lines = []
    while len(players_string) > line_length:
        middle_index = players_string.rfind(' vs. ', 0, line_length)
        if middle_index == -1:
            middle_index = players_string.rfind(' ', 0, line_length)
        if middle_index == -1:
            middle_index = line_length
        lines.append(players_string[:middle_index + 1])
        players_string = players_string[middle_index + 1:]
    lines.append(players_string)
    return '\n'.join(lines)

def plot_radar_chart(adjusted_stats, selected_players, titleStart=None, polygonal=True, bg='white', text_color='black', circle_color='black', save=False, legendXOffset=.5, legendYOffset=-.3, plotMarker='o', fontFamily='Helvetica'):
    stat_max_values = {stat: max(float(adjusted_stats[stat][player]) for player in selected_players) * 1.07 for stat in adjusted_stats}
    categories = list(adjusted_stats.keys())
    player_stats = {}
    for player in selected_players:
        player_stats[player] = [(float(adjusted_stats[stat][player]) / stat_max_values[stat]) for stat in categories]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    for player in selected_players:
        player_stats[player] += player_stats[player][:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    colors = cm.rainbow(np.linspace(0, 1, len(selected_players)))
    alphas = np.linspace(0.1, 0.6, len(categories))
    shuffleDistance = max(1, math.floor(len(categories) / len(selected_players)))

    for idx, player in enumerate(selected_players):
        if polygonal:
            for idx2, alpha_value in enumerate(alphas):
                ax.fill(angles[idx2:idx2+2]+[0], player_stats[player][idx2:idx2+2]+[0], color=colors[idx], alpha=alpha_value)
        else:
            ax.fill(angles, player_stats[player], color=colors[idx], alpha=0.3)
        ax.plot(angles, player_stats[player], color=colors[idx], linewidth=2, marker=plotMarker, markersize=8, markerfacecolor=colors[idx], label=player)
        alphas = np.roll(alphas, shuffleDistance)

    font_properties = font_manager.FontProperties(family=fontFamily, size=12)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font_properties, color=text_color)
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        angle_deg = np.degrees(angle)
        if 90 <= angle_deg < 270:
            label.set_rotation(angle_deg - 180)
            label.set_verticalalignment('center')
            label.set_horizontalalignment('right')
        else:
            label.set_rotation(angle_deg)
            label.set_verticalalignment('center')
            label.set_horizontalalignment('left')
    ax.spines['polar'].set_color(circle_color)
    ax.spines['polar'].set_linewidth(2.5)
    ax.xaxis.grid(True, color=circle_color, linestyle='dashed')
    ax.yaxis.grid(True, color=circle_color, linestyle='dashed')
    ax.set_ylim(0, 1)
    ax.set_yticklabels([])
    ax.set_yticks([])
    titleFontProperties = font_manager.FontProperties(family=fontFamily, size=18, weight='bold')
    titleStart = (titleStart + ':\n') if titleStart else ''
    players_string = ' vs. '.join(selected_players)
    full_title = titleStart + add_line_breaks(players_string, line_length=50)
    ax.set_title(full_title, fontproperties=titleFontProperties, color=text_color, y=1.13)
    legend = ax.legend(loc='lower right', bbox_to_anchor=(legendXOffset, legendYOffset), facecolor=bg, framealpha=0.5, prop=font_properties)
    plt.setp(legend.get_texts(), color=text_color)
    fig.subplots_adjust(left=0.15, right=0.85)
    if save:
        plt.savefig(f'./data_viz/{path_to_file}.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Generate radar chart for selected football players.")
    parser.add_argument("filename", help="HTML file (without extension) located in ./htmls/")
    parser.add_argument("--players", nargs="+", help="List of player names to include (optional)")
    parser.add_argument("--save", action="store_true", help="Save chart to PNG instead of displaying only")
    args = parser.parse_args()

    global path_to_file
    path_to_file = args.filename

    html_content = load_html_file(path_to_file)
    soup = BeautifulSoup(html_content, 'html.parser')
    players_and_spans = extract_players_and_spans(soup)
    all_players = list(players_and_spans.keys())
    print(f"Found the following players and span: {players_and_spans}")

    if args.players:
        selected_players = [p for p in all_players if p in args.players]
        missing = [p for p in args.players if p not in all_players]
        if missing:
            print(f"Warning: These players were not found and skipped: {missing}")
    else:
        selected_players = all_players

    if not selected_players:
        print("No players selected. Exiting.")
        sys.exit(0)

    print(f"Selected players for comparison: {selected_players}")

    stats = ['npxG + xAG', 'Progressive Passes', 'Successful Take-Ons',
             'Goals/Shot', 'Shot-Creating Actions', 'Total Carrying Distance']

    all_player_stats = {}
    for stat in stats:
        data_stat = get_data_stat(soup, stat)
        all_player_stats[stat] = extract_stat(soup, data_stat, selected_players)

    ninetiesPlayed = extract_stat(soup, get_data_stat(soup, '90s Played'), selected_players)
    print("90s Played:", ninetiesPlayed)

    adjusted_stats = adjust_stats_by_nineties(all_player_stats, ninetiesPlayed)

    plot_radar_chart(
        adjusted_stats,
        selected_players,
        titleStart="UCL 2018+",
        circle_color='white',
        bg='#2C2C2C',
        text_color='white',
        save=args.save
    )

if __name__ == "__main__":
    main()