import pandas as pd

# Define column names 
airports_cols = [
    "Airport_ID", "Name", "City", "Country", "IATA", "ICAO",
    "Latitude", "Longitude", "Altitude", "Timezone", "DST", "Tz", "Type", "Source"
]

airlines_cols = [
     "Airline_ID", "Name", "Alias", "IATA", "ICAO", "Callsign", "Country", "Active"
]

routes_cols = [
    "Airline", "Airline_ID", "Source_airport", "Source_airport_ID",
    "Destination_airport", "Destination_airport_ID", "Codeshare",
    "Stops", "Equipment"
]

# Load data
airports = pd.read_csv("airports.dat", header=None, names=airports_cols)
airlines = pd.read_csv("airlines.dat", header=None, names=airlines_cols)
routes = pd.read_csv("routes.dat", header=None, names=routes_cols)

# Keep only active airlines
airlines = airlines[airlines["Active"] == "Y"]

# Merge routes with airport and airline info
routes_full = routes.merge(
    airlines[['Airline_ID', 'Name']], on='Airline_ID', how='left'
).merge(
    airports[['Airport_ID', 'City', 'Country', 'IATA', 'Latitude', 'Longitude']],
    left_on='Source_airport_ID', right_on='Airport_ID', how='left'
).rename(columns={
    'City': 'Source_City', 'Country': 'Source_Country',
    'Latitude': 'Source_Lat', 'Longitude': 'Source_Lng'
}).merge(
    airports[['Airport_ID', 'City', 'Country', 'IATA', 'Latitude', 'Longitude']],
    left_on='Destination_airport_ID', right_on='Airport_ID', how='left'
).rename(columns={
    'City': 'Destination_City', 'Country': 'Destination_Country',
    'Latitude': 'Dest_Lat', 'Longitude': 'Dest_Lng'
})

# Drop unnecessary columns
columns_to_keep = [
    'Name', 'Source_airport', 'Source_City', 'Source_Country', 'Source_Lat', 'Source_Lng',
    'Destination_airport', 'Destination_City', 'Destination_Country', 'Dest_Lat', 'Dest_Lng',
    'Stops'
]

routes_clean = routes_full[columns_to_keep].dropna()

# Save to CSV
routes_clean.to_csv("cleaned_routes.csv", index=False)
print("✅ Cleaned data saved to cleaned_routes.csv")
