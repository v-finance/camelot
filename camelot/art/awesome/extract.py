import json

# open original metadata file
with open('icons.json') as f:
    data = json.load(f)

# create dict mapping icon name to unicode
name_to_unicode = {}
for name in data:
    name_to_unicode[name] = data[name]['unicode']

# write dict to new json file
with open('name_to_code.json', 'w') as f:
    json.dump(name_to_unicode, f)
