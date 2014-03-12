"""Script to parse bangalore ward boundaries from KML file available at 
http://openbangalore.org/.
"""
from bs4 import BeautifulSoup
import re
import web
import json
import csv

soup = BeautifulSoup(open("static/bruhath_bangalore_mahanagara_palike.kml").read(), "xml")

ward_info = dict((row[0], row) for row in csv.reader(open("wards.tsv"), delimiter="\t"))

def parse_coordinates(coordinates):
    d = coordinates.strip().replace(",0 ", ",").split(",")
    return list(web.group(d, 2))

def parse_ward(e):
    name = e.find("name").get_text()
    description = e.find("description").get_text()
    ward_no = re.match("WARD_NO = (\d+)", description).group(1)
    code = 'W{0:03d}'.format(int(ward_no))
    info = ward_info[code]

    ac = info[2]
    pc = info[3]

    path = "KA/{}/{}".format(ac.split("-")[0].strip(), code)

    return {
        "ward_no": ward_no,
        "code": code,
        "name": name,
        "description": description,
        "ward": code + " - " + name,
        "ac": ac,
        "pc": pc,
        "path": path,
        "coordinates": parse_coordinates(e.find("coordinates").get_text())
    }

elems = soup.find("Folder").find_all("Folder")
wards = [parse_ward(e) for e in elems]
print "//"
print "// Bangalore Ward Boundaries"
print "// Generated using ward maps KML file from openbangalore.org"
print "//"
print "var wards = " + json.dumps(wards, indent=True) + ";"
