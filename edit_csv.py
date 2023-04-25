import pandas as pd

df = pd.read_csv("./pokemon_chances.csv")

df['end'] = pd.Series()

df.loc[0, 'end'] = df.loc[0, 'Chance percentage'] * 10000

for i in range(1, len(df.index)):
	df.loc[i, 'end'] = df.loc[i-1, 'end'] + df.loc[i-1, 'Chance percentage'] * 10000

# df['start'] = df['start'].shift(-1) + 10000 * df['Chance percentage']

print(df)

df.to_csv("chances_edited.csv")