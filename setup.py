from flask import Flask, render_template, session, redirect, request, url_for, flash
import pandas as pd
import requests
import concurrent.futures
import os
from time import sleep

app = Flask(__name__, static_url_path='/static')

def fetch_data_with_retry(url, params, headers, retries=3, retry_delay=30):
    for _ in range(retries):
        response = requests.get(url, data=params, headers=headers)
        if response.status_code == 500:
            sleep(retry_delay)
        else:
            return response
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/picks/', methods=("POST", "GET"))
def toppicks():
    params = (
        ('per_page', '10000'),
        ('single_stat', 'true'),
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
    }

    response = fetch_data_with_retry('https://partner-api.prizepicks.com/projections', params, headers)

    if response is None:
        return render_template('error.html', error_message="Failed to fetch data after retries.")

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

    class TopPicksScraper():
        def toppicks_props_dk(self, categories=[1000, 1001, 1002, 1003, 1342, 583, 1215, 1216, 1217, 1218, 1293, 1190, 1189, 550, 1064], event=[88808, 42648, 42133, 92483]):
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



    toppicks_scraper = TopPicksScraper()
    result_df = toppicks_scraper.toppicks_props_dk()
    result_df['market'] = result_df['market'].apply(lambda x: x.replace(' ', '') if '+' in x else x)
    result_df['market'] = result_df['market'].apply(lambda x: x.replace('Reb', 'Rebs') if '+' in x else x)
    result_df['market'] = result_df['market'].apply(lambda x: x.replace('Ast', 'Asts') if '+' in x else x)
    result_df['market'] = result_df['market'].apply(lambda x: x.replace('Blk', 'Blks') if '+' in x else x)
    result_df['market'] = result_df['market'].apply(lambda x: x.replace('Stl', 'Stls') if '+' in x else x)

    final_df = pd.merge(df,result_df,left_on=['Name','Stat'],right_on=['player','market'],how='inner')
    final_df = final_df.drop(['player', 'market'], axis=1)
    final_df['Over'] = final_df['over'].astype(float)
    final_df['Under'] = final_df['under'].astype(float)
    final_df['Over %'] = final_df['Over'].apply(lambda i: abs(i)/(abs(i) + 100) * 100 if i < 0 else (100/(i + 100) * 100 if i > 0 else 0))
    final_df['Under %'] = final_df['Under'].apply(lambda i: abs(i)/(abs(i) + 100) * 100 if i < 0 else (100/(i + 100) * 100 if i > 0 else 0))
    final_df['diff'] = ((final_df['PrizePicks'] - final_df['DraftKings']) / final_df['DraftKings'])*100
    final_df['diff'] = final_df['diff'].round(2)
    final_df['Under %'] = final_df['Under %'] + final_df['diff'].apply(lambda x: x if x < 0 else 0)
    final_df['Under %'] = final_df['Under %'].apply(lambda x: min(max(x, 5), 95))
    final_df['Under %'] = final_df['Under %'].round(2)
    final_df['Over %'] = final_df['Over %'] - final_df['diff'].apply(lambda x: x)
    final_df['Over %'] = final_df['Over %'].apply(lambda x: min(max(x, 5), 95))
    final_df['Over %'] = final_df['Over %'].round(2)
    final_df.loc[final_df['Type'] != 'standard', 'Under %'] = None
    final_df = final_df[~final_df['League'].str.contains('1H')]
    final_df = final_df[~final_df['League'].str.contains('1Q')]
    final_df = final_df[~final_df['League'].str.contains('2H')]
    final_df = final_df[~final_df['League'].str.contains('2Q')]
    final_df = final_df[~final_df['League'].str.contains('3Q')]
    final_df = final_df[~final_df['League'].str.contains('4Q')]
    final_df = final_df[~final_df['League'].str.contains('1P')]
    final_df = final_df[~final_df['League'].str.contains('2P')]
    final_df = final_df[~final_df['League'].str.contains('3P')]
    final_df = final_df.sort_values(by='Over %', ascending=False)
    final_df = final_df[['League','Name','Team','Opp','Stat','Type','PrizePicks','DraftKings','Over','Under','Over %','Under %']]
    
    html_table = final_df.to_html(classes='styled-table', index=False, justify='center', border=2, na_rep='')

    return render_template('toppicks.html', tables=[html_table], titles=final_df.columns.values)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, ssl_context=('cert.pem', 'key.pem'))

