from flask import Flask, render_template, session, redirect, request, url_for, flash
import pandas as pd
import requests
import concurrent.futures
from unidecode import unidecode
import numpy as np
import os
from tenacity import retry, stop_after_attempt, wait_fixed

app = Flask(__name__, static_url_path='/static')

@retry(stop=stop_after_attempt(5), wait=wait_fixed(30))  # Retry 5 times with a fixed delay of 30 seconds between retries
def fetch_data_with_retry(url, params, headers):
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/table/', methods=("POST", "GET"))
def toppicks():
    params = (
        ('per_page', '10000'),
        ('single_stat', 'true'),
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
    }

    response = fetch_data_with_retry('https://partner-api.prizepicks.com/projections', params, headers)

    df1 = pd.json_normalize(response.json()['included'])
    df1 = df1[df1['type'] == 'new_player']

    df2 = pd.json_normalize(response.json()['data'])

    df_m = pd.merge(df1, df2, left_on='id', right_on='relationships.new_player.data.id', how='left')

    df = df_m[['attributes.league', 'attributes.name', 'attributes.team', 'attributes.position',
               'attributes.description', 'attributes.stat_type', 'attributes.line_score',
               'attributes.odds_type']]

    df = df.rename(columns={'attributes.league':'League',
                        'attributes.name':'Name',
                        'attributes.team':'Team',
                        'attributes.position':'Pos',
                        'attributes.description':'Opp',
                        'attributes.stat_type': 'Stat',
                        'attributes.line_score':'PrizePicks',
                        'attributes.odds_type': 'Type'})

    df['PrizePicks'] = df['PrizePicks'].astype('float')

    def unidecode_column(value):
        return unidecode(value)

    df['Name'] = df['Name'].apply(unidecode_column)

# NFL

    class NFLScraper():
        def nfl_props_dk(self, categories=[1000, 1001, 1002, 1003, 1342], event=[88808]):
            data = []

            for e in event:
                for cat in categories:
                    dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}?format=json").json()
                    if 'eventGroup' in dk_api:
                        for i in dk_api['eventGroup']['offerCategories']:
                            if 'offerSubcategoryDescriptors' in i:
                                dk_markets = i['offerSubcategoryDescriptors']

                        subcategoryIds = []
                        for i in dk_markets:
                            subcategoryIds.append(i['subcategoryId'])

                        def fetch_dk_data(ids):
                            nonlocal data
                            dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}/subcategories/{ids}?format=json").json()
                            for i in dk_api['eventGroup']['offerCategories']:
                                if 'offerSubcategoryDescriptors' in i:
                                    dk_markets = i['offerSubcategoryDescriptors']

                            for i in dk_markets:
                                if 'offerSubcategory' in i:
                                    market = i['name']
                                    for j in i['offerSubcategory']['offers']:
                                        for k in j:
                                            if 'participant' in k['outcomes'][0]:
                                                player = k['outcomes'][0]['participant']
                                                over = k['outcomes'][0]['oddsAmerican']
                                                try:
                                                    under = k['outcomes'][1]['oddsAmerican']
                                                except IndexError:
                                                    continue
                                                line = k['outcomes'][1].get('line', None)  # Use get() to provide a default value if 'line' is not present
                                                data.append({'player': player, 'market': market, 'over': over, 'under': under, 'DraftKings': line})
                                            else:
                                                continue

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [executor.submit(fetch_dk_data, ids) for ids in subcategoryIds]

                            concurrent.futures.wait(futures)

            if data:
                df = pd.DataFrame(data)
                return df
            else:
                print("No data found.")

# NHL

    class NHLPicksScraper():
        def nhl_props_dk(self, categories=[1190, 1189, 550, 1064], event=[42133]):
            data = []

            for e in event:
                for cat in categories:
                    dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}?format=json").json()
                    if 'eventGroup' in dk_api:
                        for i in dk_api['eventGroup']['offerCategories']:
                            if 'offerSubcategoryDescriptors' in i:
                                dk_markets = i['offerSubcategoryDescriptors']

                        subcategoryIds = []
                        for i in dk_markets:
                            subcategoryIds.append(i['subcategoryId'])

                        def fetch_dk_data(ids):
                            nonlocal data
                            dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}/subcategories/{ids}?format=json").json()
                            for i in dk_api['eventGroup']['offerCategories']:
                                if 'offerSubcategoryDescriptors' in i:
                                    dk_markets = i['offerSubcategoryDescriptors']

                            for i in dk_markets:
                                if 'offerSubcategory' in i:
                                    market = i['name']
                                    for j in i['offerSubcategory']['offers']:
                                        for k in j:
                                            if 'participant' in k['outcomes'][0]:
                                                player = k['outcomes'][0]['participant']
                                                over = k['outcomes'][0]['oddsAmerican']
                                                try:
                                                    under = k['outcomes'][1]['oddsAmerican']
                                                except IndexError:
                                                    continue
                                                line = k['outcomes'][1].get('line', None)  # Use get() to provide a default value if 'line' is not present
                                                data.append({'player': player, 'market': market, 'over': over, 'under': under, 'DraftKings': line})
                                            else:
                                                continue

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [executor.submit(fetch_dk_data, ids) for ids in subcategoryIds]

                            concurrent.futures.wait(futures)

            if data:
                df = pd.DataFrame(data)
                return df
            else:
                print("No data found.")

# NBA, MCBB

    class BballPicksScraper():
        def bball_props_dk(self, categories=[583, 1215, 1216, 1217, 1218, 1293], event=[42648, 92483]):
            data = []

            for e in event:
                for cat in categories:
                    dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}?format=json").json()
                    if 'eventGroup' in dk_api:
                        for i in dk_api['eventGroup']['offerCategories']:
                            if 'offerSubcategoryDescriptors' in i:
                                dk_markets = i['offerSubcategoryDescriptors']

                        subcategoryIds = []
                        for i in dk_markets:
                            subcategoryIds.append(i['subcategoryId'])

                        def fetch_dk_data(ids):
                            nonlocal data
                            dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}/subcategories/{ids}?format=json").json()
                            for i in dk_api['eventGroup']['offerCategories']:
                                if 'offerSubcategoryDescriptors' in i:
                                    dk_markets = i['offerSubcategoryDescriptors']

                            for i in dk_markets:
                                if 'offerSubcategory' in i:
                                    market = i['name']
                                    for j in i['offerSubcategory']['offers']:
                                        for k in j:
                                            if 'participant' in k['outcomes'][0]:
                                                player = k['outcomes'][0]['participant']
                                                over = k['outcomes'][0]['oddsAmerican']
                                                try:
                                                    under = k['outcomes'][1]['oddsAmerican']
                                                except IndexError:
                                                    continue
                                                line = k['outcomes'][1].get('line', None)  # Use get() to provide a default value if 'line' is not present
                                                data.append({'player': player, 'market': market, 'over': over, 'under': under, 'DraftKings': line})
                                            else:
                                                continue

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [executor.submit(fetch_dk_data, ids) for ids in subcategoryIds]

                            concurrent.futures.wait(futures)

            if data:
                df = pd.DataFrame(data)
                return df
            else:
                print("No data found.")

    class SoccerPicksScraper():
        def soccer_props_dk(self, subcategories=[4690, 11783, 11004, 11005, 11006], categories=[537, 1113], event=[40253, 40031, 40481, 40032, 86680, 40817, 40030]):
            data = []

            for e in event:
                for cat in categories:
                    for sub in subcategories:
                        dk_api = requests.get(f"https://sportsbook.draftkings.com//sites/US-NJ-SB/api/v5/eventgroups/{e}/categories/{cat}/subcategories/{sub}?format=json").json()

                        if 'eventGroup' in dk_api:
                            for i in dk_api['eventGroup']['offerCategories']:
                                if 'offerSubcategoryDescriptors' in i:
                                    for subcategory in i['offerSubcategoryDescriptors']:
                                        if 'offerSubcategory' in subcategory:
                                            market = subcategory['name']

                                            for offer in subcategory['offerSubcategory']['offers']:
                                                for outcome in offer:
                                                    try:
                                                        line = outcome['label']
                                                    except KeyError:
                                                        line = 0.5

                                                    if 'outcomes' in outcome:
                                                        for participant in outcome['outcomes']:
                                                            player = participant.get('label', None)
                                                            over = participant.get('oddsAmerican', None)
                                                            under = None if player else over

                                                            data.append({'player': player, 'market': market, 'over': over, 'under': under, 'DraftKings': line})

            if data:
                df = pd.DataFrame(data)
                return df
            else:
                print("No data found.")


    # Create an instance of the scraper
    soccer_scraper = SoccerPicksScraper()

    # Run the scraper and print the result
    soccer_result_df = soccer_scraper.soccer_props_dk()

    goalscorer_rows = (soccer_result_df['market'] == 'Goalscorer') | (soccer_result_df['market'] == 'Shots On Target')
    soccer_result_df['name_count'] = soccer_result_df[goalscorer_rows].groupby('player').cumcount()
    filtered_soccer_result_df = soccer_result_df[~((goalscorer_rows) & (soccer_result_df['name_count'] <= 1))]
    filtered_soccer_result_df = filtered_soccer_result_df.drop(columns=['name_count'])
    filtered_soccer_result_df['DraftKings'] = filtered_soccer_result_df['DraftKings'].str.replace('Goalscorers','0.5')
    filtered_soccer_result_df['DraftKings'] = filtered_soccer_result_df['DraftKings'].str.replace('Player to Score or Give Assist','0.5')
    filtered_soccer_result_df['DraftKings'] = filtered_soccer_result_df['DraftKings'].str.extract('(\d+(\.\d+)?)', expand=False)[0]
    filtered_soccer_result_df['DraftKings'] = pd.to_numeric(filtered_soccer_result_df['DraftKings'], errors='coerce')

# Combining

    nfl_scraper = NFLScraper()
    nfl_result_df = nfl_scraper.nfl_props_dk()

    nhl_scraper = NHLPicksScraper()
    nhl_result_df = nhl_scraper.nhl_props_dk()

    bball_scraper = BballPicksScraper()
    bball_result_df = bball_scraper.bball_props_dk()

    result_df = pd.concat([nfl_result_df, nhl_result_df, bball_result_df, filtered_soccer_result_df])

# Editing

    # Define replacement mappings
    replacement_mapping = {
        'Reb': 'Rebs',
        'Ast': 'Asts',
        'Blk': 'Blks',
        'Stl': 'Stls',
        'Saves': 'Goalie Saves',
        'Player Shots': 'Shots',
        'Shots on Target': 'Shots On Target',
        'Player Assists': 'Assists',
        'Goalscorer': 'Goals',
        'To Score or Give Assist': 'Goal + Assist',
        'Threes': '3-PT Made',
        'Blocks': 'Blocked Shots'
    }

    # Apply replacements using a single operation
    result_df['market'] = result_df['market'].apply(lambda x: replacement_mapping.get(x, x))

    # Replace ' ' with '' if '+' exists
    result_df['market'] = result_df['market'].apply(lambda x: x.replace(' ', '') if '+' in x else x)


    # Merge and drop unnecessary columns
    final_df = pd.merge(df, result_df, left_on=['Name', 'Stat'], right_on=['player', 'market'], how='inner')
    final_df.drop(['player', 'market'], axis=1, inplace=True)

    # Adjust DraftKings values based on condition
    condition = final_df['Stat'].isin(['Shots On Target', 'Shots'])
    final_df.loc[condition, 'DraftKings'] -= 0.5

    # Convert 'over' and 'under' columns to float
    final_df['Over'] = final_df['over'].astype(float)
    final_df['Under'] = final_df['under'].astype(float)

    # Calculate 'Over %' and 'Under %'
    final_df['Over %'] = final_df['Over'].apply(lambda i: abs(i) / (abs(i) + 100) * 100 if i < 0 else (100 / (i + 100) * 100 if i > 0 else 0))
    final_df['Under %'] = final_df['Under'].apply(lambda i: abs(i) / (abs(i) + 100) * 100 if i < 0 else (100 / (i + 100) * 100 if i > 0 else 0))

    # Calculate difference and adjust 'Under %'
    final_df['diff'] = ((final_df['PrizePicks'] - final_df['DraftKings']) / final_df['DraftKings']) * 100
    final_df['diff'] = final_df['diff'].round(2)
    final_df['Under %'] += 0.1 * final_df['diff'].apply(lambda x: x if x < 0 else 0)
    final_df['Under %'] = final_df['Under %'].apply(lambda x: min(max(x, 5), 95)).round(2)

    # Adjust 'Over %' based on difference
    final_df['Over %'] -= 0.5 * final_df['diff']
    final_df['Over %'] = final_df['Over %'].apply(lambda x: min(max(x, 5), 95)).round(2)

    # Set 'Under %' to None based on condition
    final_df.loc[final_df['Type'] != 'standard', 'Under %'] = None

    # Filter out unwanted League values
    unwanted_leagues = ['1H', '1Q', '2H', '2Q', '3Q', '4Q', '1P', '2P', '3P']
    final_df = final_df[~final_df['League'].str.contains('|'.join(unwanted_leagues))]

    # Convert selected columns to numeric
    numeric_columns = ['Over', 'Under', 'Over %', 'Under %']
    final_df[numeric_columns] = final_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Filter based on Over values
    final_df = final_df[(final_df['Over'] <= 135) & (final_df['Over'] >= -270)]

    # Sort by 'Over %' in descending order
    final_df.sort_values(by='Over %', ascending=False, inplace=True)

    # Select and reorder columns
    final_df = final_df[['League', 'Name', 'Team', 'Opp', 'Stat', 'Type', 'PrizePicks', 'DraftKings', 'Over', 'Under', 'Over %', 'Under %']]

    # Adjust 'Under %' for 'SOCCER' league
    final_df['Under %'] = np.where(final_df['League'] == 'SOCCER', 100 - final_df['Over %'], final_df['Under %'])
 
    
    html_table = final_df.to_html(classes='styled-table', index=False, justify='center', border=2, na_rep='')

    return render_template('toppicks.html', tables=[html_table], titles=final_df.columns.values)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port)