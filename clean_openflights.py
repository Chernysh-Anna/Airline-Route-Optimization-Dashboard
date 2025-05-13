import pandas as pd
import matplotlib.pyplot as plt

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

# Fix data types for join keys
routes["Airline_ID"] = pd.to_numeric(routes["Airline_ID"], errors='coerce').astype('Int64')
airlines["Airline_ID"] = pd.to_numeric(airlines["Airline_ID"], errors='coerce').astype('Int64')
routes["Source_airport_ID"] = pd.to_numeric(routes["Source_airport_ID"], errors='coerce').astype('Int64')
routes["Destination_airport_ID"] = pd.to_numeric(routes["Destination_airport_ID"], errors='coerce').astype('Int64')
airports["Airport_ID"] = pd.to_numeric(airports["Airport_ID"], errors='coerce').astype('Int64')

# Keep only active airlines
airlines = airlines[airlines["Active"] == "Y"]

# Merge routes with airline names
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

# Drop unnecessary columns and rows with missing data
columns_to_keep = [
    'Name', 'Source_airport', 'Source_City', 'Source_Country', 'Source_Lat', 'Source_Lng',
    'Destination_airport', 'Destination_City', 'Destination_Country', 'Dest_Lat', 'Dest_Lng',
    'Stops'
]

routes_clean = routes_full[columns_to_keep].dropna()

# 1. Identify underserved airports (source but not destination)
all_sources = set(routes_clean['Source_airport'])
all_destinations = set(routes_clean['Destination_airport'])

underserved_airports = all_sources - all_destinations

print("\nUnderserved Airports (potential new destinations):")
underserved_list = []
for code in underserved_airports:
    airport_info = airports[airports['IATA'] == code]
    if not airport_info.empty:
        airport_name = airport_info.iloc[0]['Name']
        city = airport_info.iloc[0]['City']
        country = airport_info.iloc[0]['Country']
        print(f"- {code}: {airport_name} ({city}, {country})")
        underserved_list.append({
            "IATA": code,
            "Name": airport_name,
            "City": city,
            "Country": country
        })

# 2. Count incoming and outgoing flights for each airport
airport_traffic = {}

# Count outgoing flights
for code in routes_clean['Source_airport'].unique():
    outgoing = routes_clean[routes_clean['Source_airport'] == code].shape[0]
    airport_traffic[code] = {"outgoing": outgoing, "incoming": 0}

# Count incoming flights
for code in routes_clean['Destination_airport'].unique():
    incoming = routes_clean[routes_clean['Destination_airport'] == code].shape[0]
    if code in airport_traffic:
        airport_traffic[code]["incoming"] = incoming
    else:
        airport_traffic[code] = {"outgoing": 0, "incoming": incoming}

# Convert to DataFrame for easier analysis
traffic_df = pd.DataFrame.from_dict(airport_traffic, orient='index')
traffic_df['total'] = traffic_df['incoming'] + traffic_df['outgoing']
traffic_df['ratio'] = traffic_df['outgoing'] / traffic_df['incoming'].replace(0, 1)  # Avoid division by zero
traffic_df = traffic_df.sort_values('total', ascending=False)

# Add airport information
traffic_df = traffic_df.reset_index().rename(columns={'index': 'IATA'})
traffic_df = traffic_df.merge(
    airports[['IATA', 'Name', 'City', 'Country']], on='IATA', how='left'
)

# Save results to CSV files
traffic_df.to_csv("airport_traffic_analysis.csv", index=False)
pd.DataFrame(underserved_list).to_csv("underserved_airports.csv", index=False)

# Print top 20 airports by traffic
print("\nTop 20 Airports by Total Traffic (Incoming + Outgoing Flights):")
for i, row in traffic_df.head(20).iterrows():
    print(f"{row['IATA']}: {row['Name']} ({row['City']}, {row['Country']}) - In: {row['incoming']}, Out: {row['outgoing']}, Total: {row['total']}")

# Print the most imbalanced airports (high outgoing to incoming ratio)
print("\nAirports with Imbalanced Traffic (High Outgoing to Incoming Ratio):")
imbalanced = traffic_df[(traffic_df['incoming'] > 0) & (traffic_df['outgoing'] > 10) & (traffic_df['ratio'] > 2)].sort_values('ratio', ascending=False)
for i, row in imbalanced.head(15).iterrows():
    print(f"{row['IATA']}: {row['Name']} ({row['City']}, {row['Country']}) - In: {row['incoming']}, Out: {row['outgoing']}, Ratio: {row['ratio']:.2f}")

# Create visualizations of airport traffic
plt.figure(figsize=(12, 8))
top_20 = traffic_df.head(20)
plt.bar(top_20['IATA'], top_20['incoming'], label='Incoming Flights')
plt.bar(top_20['IATA'], top_20['outgoing'], bottom=top_20['incoming'], label='Outgoing Flights')
plt.title('Top 20 Airports by Total Traffic')
plt.xlabel('Airport IATA Code')
plt.ylabel('Number of Flights')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('top_20_airports.png')

# Create a heatmap of airport traffic imbalance
plt.figure(figsize=(10, 8))
imbalanced_traffic = traffic_df[(traffic_df['incoming'] > 5) & (traffic_df['outgoing'] > 5)].copy()
imbalanced_traffic['imbalance'] = abs(imbalanced_traffic['incoming'] - imbalanced_traffic['outgoing'])
imbalanced_traffic = imbalanced_traffic.sort_values('imbalance', ascending=False).head(15)

colors = ['green' if row['incoming'] > row['outgoing'] else 'red' for _, row in imbalanced_traffic.iterrows()]
plt.barh(imbalanced_traffic['IATA'], imbalanced_traffic['imbalance'], color=colors)
plt.title('Most Imbalanced Airports (Difference between Incoming and Outgoing Flights)')
plt.xlabel('Imbalance')
plt.ylabel('Airport IATA Code')
plt.tight_layout()
plt.savefig('imbalanced_airports.png')

print("\nAnalysis complete. Results saved to airport_traffic_analysis.csv and underserved_airports.csv")
print("Visualizations saved as top_20_airports.png and imbalanced_airports.png")