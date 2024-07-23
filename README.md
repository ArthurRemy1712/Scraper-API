# POI Scraper using OSM Data

Api used to get a json of POI with a certain name in a certain area using OpenStreetMap data.

## Endpoints

### /ping 

Used to test connection to the API.

### /Scraper

Several parameters are required :

- zone_code : code of the search area following ISO 3166-2 norm ;
- poi_name : name of the POIs searched
- shop_category : OSM category of the POIs searched *(optional)*

