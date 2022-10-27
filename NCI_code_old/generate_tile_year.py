import csv

with open('mangrove_damage_tile_year', 'r') as f:
    for row in csv.reader(f, delimiter=' ', skipinitialspace=True):
        print(row)
        with open('_'.join([row[0], row[1], 'damage']), 'w') as fout:
            for e in row[2:]:
                fout.write(' '.join([e.split(',')[0], e.split(',')[1], row[1], row[0]]) + '\n')
