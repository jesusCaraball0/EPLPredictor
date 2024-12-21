import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

# need to modify this to take in any fbref link and return the required results.

def createResultsDf(league='Premier League', extension='12'):

    years = list(range(2025,2023, -1))

    all_matches = []

    standingsUrl = f"https://fbref.com/en/comps/{extension}/"

    for year in years:
        data = requests.get(standingsUrl)
        soup = BeautifulSoup(data.text, features="html.parser")
        standingsTable = soup.select('table.stats_table')[0]
        links = [l.get("href") for l in standingsTable.find_all('a')]
        links = [l for l in links if "/squads/" in l]
        teamUrls = [f"https://fbref.com{l}" for l in links]

        previousSeason = soup.select("a.prev")[0].get("href")
        standingsUrl = f"https://fbref.com/{previousSeason}"


        for teamUrl in teamUrls:
            teamName = teamUrl.split("/")[-1].replace("-Stats","").replace("-"," ")

            data = requests.get(teamUrl)
            matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

            soup = BeautifulSoup(data.text, features="html.parser")
            links = [l.get("href") for l in soup.find_all('a')]
            links = [l for l in links if l and 'all_comps/shooting/' in l]

            data = requests.get(f"https://fbref.com{links[0]}")
            shootingStats = pd.read_html(data.text, match="Shooting")[0]
            shootingStats.columns = shootingStats.columns.droplevel()

            try:
                teamData = matches.merge(shootingStats[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
            except ValueError:
                continue

            teamData = teamData[teamData["Comp"] == league]
            teamData["Season"] = year
            teamData["Team"] = teamName
            all_matches.append(teamData)
            print(teamData.head())
            print(f"finished with {teamUrl} in {year}")
            time.sleep(15)


    print(f"finished getting data, making {league} csv")
    matchDf = pd.concat(all_matches)
    matchDf.columns = [c.lower() for c in matchDf.columns]

    league = '_'.join(league.lower().split(' '))
    matchDf.to_csv(f"matches_{league}.csv")

def main():
    # fbref standing links partial links (extensions)
    leagues = {'Premier League': '9', 'La Liga': '12', 'Serie A': '11', 'Bundesliga': '20', 'Ligue 1': '13'}

    for league, extension in leagues.items():
        createResultsDf(league, extension)

if __name__ == '__main__':
    main()
