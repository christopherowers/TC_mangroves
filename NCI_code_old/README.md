### NCI data

folder contains some of the files that were useful to get collection 3 working

`load_plot_tables.ipynb` has code at the bottom to look at all cyclone damage to mangroves (combines all pickle files)

`generate_wind_yaml.py` has dates of cyclones

`mangrove_change_on_cyclone_all.py` not exactly sure what it does but might be important for maps of immediate and long term impact
- seems that the .nc outputs created are the story about immediate impacts and long term impacts (ones with `_all.nc`)
- there are datasets in the `/more_mangroves/` about `_damage_level*.nc`; might be the link between the outputs created and the role of `mangrove_change_on_cyclone_all.py` for the maps?

most of the data is in here
`/g/data/u46/users/ea6141/more_mangroves`

note:
cyclone_damage_tally_notsure folder means it's not sure if mangrove is there on not (i.e. only 3 or 4 obs for the year)

some of it is in here
`/g/data/r78/mangroves`


`cyclone_time = {
        'IngridLF1':  '2005-01-01T00:00:00',
        'IngridLF2':   '2005-01-01T00:00:00', 
        'IngridLF3':   '2005-01-01T00:00:00',
        'Larry':  '2006-01-01T00:00:00',
        'MonicaLF1':   '2006-01-01T00:00:00',    
        'MonicaLF2':   '2006-01-01T00:00:00',
        'George':  '2007-01-01T00:00:00',
        'Laurence':    '2009-01-01T00:00:00',
        'Yasi':    '2011-01-01T00:00:00',
        'Ita': '2014-01-01T00:00:00',
        'Lam': '2015-01-01T00:00:00',
        'Marcia':  '2015-01-01T00:00:00',
        'NathanLF1':   '2015-01-01T00:00:00',
        'NathanLF2':  '2015-01-01T00:00:00',
        'Debbie': '2017-01-01T00:00:00'
        }`