
# Minify geojson files

# Make sure npm minify-geojson is installed. 

# Options: 
# -k: shrink property keys
# -i: Add the key map to the GeoJSON file
# -w: keep whitelisted properties. 
# -c :Removes superfluous decimals (keep first 5)   

# -f, --filter String  Comma separted list of property filters, e.g. "WATER = YES, LAND = NO" # might be useful!


minify-geojson -ki -w "pct_nimby, med_inc_adj, turnout, owned, precname, yr_prop" -c 5 ../results/maps/results_pre1992.geojson
minify-geojson -ki -w "pct_nimby, med_inc_adj, turnout, owned, precname, yr_prop" -c 5 ../results/maps/results_pre2002.geojson
minify-geojson -ki -w "pct_nimby, med_inc_adj, turnout, owned, precname, yr_prop" -c 5 ../results/maps/results_pre2012.geojson