#!/usr/bin/env python
"""
Scrape profile info from DESE.

This script assumes we already have a spreadsheet exported from a district 
search (http://profiles.doe.mass.edu/search/search.aspx). Our goal is to fill
in the missing fields that aren't exported.
"""
import csv
import dataset
import requests

from BeautifulSoup import BeautifulSoup

INPUT_FILE = 'input/districts.csv'
OUTPUT_DB = 'output/districts.db'
OUTPUT_FILE = 'output/districts.csv'

def fetch(orgcode):
    """
    Build a profile URL for a district given its orgcode,
    then fetch and parse, returning a document root.
    """
    # http://profiles.doe.mass.edu/profiles/general.aspx?orgcode=04450000&orgtypecode=5
    params = {'orgcode': orgcode, 'orgtypecode': 5}
    base = 'http://profiles.doe.mass.edu/profiles/general.aspx'

    resp = requests.get(base, params=params)

    return BeautifulSoup(resp.text)


def extract(soup):
    """
    Get values we want from the soup. 
    Data is stored on table.t_clear, basically in key/value pairs.

    This is a generator that yields pairs, so usage will be:
    >>> dict(extract(soup))
    """
    # get the table
    table = soup.find('table', {'class': 't_clear'})
    
    # loop through rows
    for row in table.findAll('tr'):

        # we only care about rows with two cells
        # there's other stuff here, but we have most
        # of it from input spreadsheet
        cells = row.findAll('td')
        if len(cells) == 2:
            # just deconstruct this
            k, v = cells

            # and yield text
            yield k.text, v.text


def main():
    """
    Load input CSV. 
    Scrape each district profile page. 
    Save to OUTPUT_DB.
    """
    # get a database and a table
    db = dataset.Database('sqlite:///' + OUTPUT_DB)
    districts = db['districts']

    # read in the INPUT_FILE
    with open(INPUT_FILE) as f:
        reader = csv.DictReader(f)

        for row in reader:
            # pull the Org Code out of each row and scrape that district
            print 'Fetching %s' % row['Org Name']
            soup = fetch(row['Org Code'])

            # pull out the data we need
            # then overwrite it with row, since that's cleaner
            data = dict(extract(soup))
            data.update(row)

            districts.upsert(data, ['Org Code'])
            print 'Saved %s' % row['Org Name']


if __name__ == "__main__":
    main()
