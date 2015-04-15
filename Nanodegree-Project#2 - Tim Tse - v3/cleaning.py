#Step 1: Import library and file.  Parse through the file with ElementTree to find the counts of each element.

#Import library
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
#Import file
OSMFILE = "example.osm"
tags = {}
for event, elem in ET.iterparse(OSMFILE):
    if elem.tag in tags:
        tags[elem.tag] += 1
    else:
        tags[elem.tag] = 1
        
#Step 2: From lesson 6, we defined lower, lower_colon, and problemchars.  The code below is to show the counts of each of the definition below.
        
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]') 
def key_type(element, keys):
    if element.tag == "tag":    
        if problemchars.search(element.attrib['k']):
            keys['problemchars'] += 1
        elif lower.search(element.attrib['k']):
            keys['lower'] += 1
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] += 1 
        else:
            keys['other'] += 1     
    return keys 
def process_map(OSMFILE):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}    
    for _, element in ET.iterparse(OSMFILE):
        keys = key_type(element, keys) 
    return keys
 
keys = process_map(OSMFILE)
pprint.pprint(keys)

#Step 3: Build an expression to match the token in a sting ending with a period and the expected clean street type.

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected_street_types = ["Avenue", "Boulevard", "Commons", "Court", "Drive", "Lane", "Parkway", 
                         "Place", "Road", "Square", "Street", "Trail"]
map_street_types = \
                     {
        "Ave" : "Avenue",
        "BLVD" : "Boulevard",
        "Blvd" : "Boulevard",
        "Blvd." : "Boulevard",
        "Cir" : "Circle",
        "Dr" : "Drive",
        "Ln" : "Lane",
        "Pkwy" : "Parkway",
        "Rd" : "Road",
        "Rd." : "Road",
        "St" : "Street",
        "St." : "Street"
}

#Step 4: The audit_string function will take in the dictionary of the regex and street types in step 3 to match against that string and the list of expected street types.  If there is a match and the match is not in our list, then it will add the match as a key to the dictionary and the string to the set.

def audit_string(match_set_dict, string_to_audit, regex, expected_matches):
    m = regex.search(string_to_audit)
    if m:
        match_string = m.group() 
        if match_string not in expected_matches:
            match_set_dict[match_string].add(string_to_audit)

#Step 5: The audit function will do the parsing and auditing of the street names in our database.
            
def audit(osmfile, tag_filter, regex, expected_matches = []):   
    osm_file = open(osmfile, "r")
    match_sets = defaultdict(set) 
    # iteratively parse
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        # iterate the tags within node or way
        if elem.tag == "node" or elem.tag == "way":
           for tag in elem.iter("tag"): 
                if tag_filter(tag):
                    audit_string(match_sets, tag.attrib['v'], regex, expected_matches)
    return match_sets

#Step 6: The is_street_name function will determine if the element has “addr:street” attribute.  Also, we can see a print of the audit output.

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
street_types = audit(OSMFILE, tag_filter = is_street_name, regex = street_type_re, 
                     expected_matches = expected_street_types)
pprint.pprint(dict(street_types))

#Step 7: The update function will replace the abbreviated street types.  The string to update function will take a string to update, mapping the dictionary, and a regex to search.

def update(string_to_update, mapping, regex):
    m = regex.search(string_to_update) 
    if m:
        match = m.group()      
        if match in mapping:
            string_to_update = re.sub(regex, mapping[match], string_to_update)
    return string_to_update

#Step 8: Take the keys from the map to create a string joined by “|”.  This will cause the regex to search for any of the keys to match the first it finds.

bad_streets = "|".join(map_street_types.keys()).replace('.', '')
street_type_updater_re = re.compile(r'\b(' + bad_streets + r')\b\.?', re.IGNORECASE)

#Step 9: Traverse the street_type dictionary to see the abbreviations to clean representations.

for street_type, ways in street_types.iteritems():
    if street_type in map_street_types:
        for name in ways:
            new_name = update(name, map_street_types, street_type_updater_re)
            print name, "=>", new_name
