import pandas as pd
from sklearn.ensemble import RandomForestClassifier # ML model that can pick up nonlinearity in data
from sklearn.metrics import accuracy_score, precision_score

#initial model (n_estimators is # individual decision trees trained, min_samples_split higher reduces likelihood of overfit but reduces accurary in 
#training data, random_states ensures same results as long as data remains the same)
# Data is in time series format, so all data in test set must come after all the data in the training set. 
rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)


#Adding rolling averages of key stats for each team (group)
def rollingAverages(group, cols, new_cols):
    group = group.sort_values("date")
    rollingStats = group[cols].rolling(3, closed='left').mean() #takes past 3 values instead of current 3 to prevent using the future to predict it
    group[new_cols] = rollingStats
    group.dropna(subset=new_cols)
    return group

# Fits RF model to training data and returns prediction DF + success metrics
def makePredictions(data, predictors):
    train = data[data["date"] < '2024-03-01']
    test = data[data["date"] > '2024-03-01']

    rf.fit(train[predictors], train["target"])

    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], predictions=preds), index=test.index)

    precision = precision_score(test["target"], preds)
    accuracy = accuracy_score(test["target"], preds)

    return combined, precision, accuracy

def cleanData():
    matches = pd.read_csv("matches.csv", index_col=0)

    #Cleaning data to be digestible by ML model (turning useful cols into numerical values)
    matches["date"] = pd.to_datetime(matches["date"])
    matches["venue_code"] = matches["venue"].astype("category").cat.codes #0 away, 1 at home
    matches["opp_code"] = matches["opponent"].astype("category").cat.codes
    matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")
    matches["day_code"] = matches["date"].dt.day_of_week #Mon = 0, Tue = 1, ... Sun = 6

    #turning success metric into numerical values
    matches["target"] = (matches["result"]=="W").astype("int")

    # Making new cols with rolling averages for key stats (past 3 matches)
    cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
    new_cols = [f"{c}_rolling" for c in cols]
    predictors = ["venue_code", "opp_code", "hour", "day_code"] + new_cols

    #Making new df incorporating rolling metrics
    matchesRolling = matches.groupby("team").apply(lambda x: rollingAverages(x, cols, new_cols))
    matchesRolling = matchesRolling.droplevel("team")
    matchesRolling.index = range(matchesRolling.shape[0])

    return matchesRolling, predictors

def main():
    # #choosing how to measure the accuracy of the model is a really important decision
    matches, predictors = cleanData()
    combined, precision, accuracy = makePredictions(matches, predictors)

    print(precision)
    print(accuracy)

    combined = combined.merge(matches[["date", "team", "opponent", "result"]], left_index=True, right_index=True)
    print(combined)


    #Can scrape more data, use more cols, use different ML models to improve accuracy

if __name__ == "__main__":
    main()