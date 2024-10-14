import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

def createResultsDf():
    
    years = list(range(2025,2023, -1))

    all_matches = []

    standingsUrl = "https://fbref.com/en/comps/9/Premier-League-Stats"

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

            teamData = teamData[teamData["Comp"] == "Premier League"]
            teamData["Season"] = year
            teamData["Team"] = teamName
            all_matches.append(teamData)
            time.sleep(15)



    matchDf = pd.concat(all_matches)
    matchDf.columns = [c.lower() for c in matchDf.columns]
    matchDf.to_csv("matches.csv")

def main():
    createResultsDf()

if __name__ == '__main__':
    main()
