import requests
from bs4 import BeautifulSoup
import sqlite3
import dateparser

from pprint import pprint

DATABASE_NAME = 'data.sqlite'
conn = sqlite3.connect(DATABASE_NAME)
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS data')
c.execute(
    '''
    CREATE TABLE data (
        name text,
        department text,
        faculty text,
        since_date text,
        until_date text,
        description text,
        location text,
        role_description text
    )
    '''
)
conn.commit()


def split_and_strip(line, delimiter=':'):
    try:
        parts = line.split(delimiter)
        return parts[1].strip()
    except IndexError:
        return ''

base_url = 'https://www.uzh.ch/prof/ssl-dir/interessenbindungen/client/web'

# generate URLs from A-Z
alphabet = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
for letter in alphabet:
    url = "%s/%s" % (base_url, letter)
    print url

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    prof_divs = soup.select('main.l-content div#list > div.row > div')

    for prof_div in prof_divs:
        name = prof_div.find('h5').get_text()
        
        info_div = prof_div.find('div').find('div')
        
        info_text = info_div.find('p').get_text()
        faculty = ''
        department = '' 
        for line in info_text.splitlines():
            if line.startswith(u'Fakult\xe4tszugeh\xf6rigkeit'):
                faculty = split_and_strip(line)
            if line.startswith(u'Institutszugeh\xf6rigkeit'):
                department = split_and_strip(line)

        table = info_div.find('table')
        if not table:
            continue
        role_trs = table.find('tbody').find_all('tr')
        for role_tr in role_trs:
            role = []
            tds = role_tr.find_all('td')
            date_str = tds[0].get_text()

            since_date = ''
            until_date = ''
            if date_str and date_str.startswith("seit"):
                since_obj = dateparser.parse(date_str[len("seit "):], languages=['de'], settings={'PREFER_DAY_OF_MONTH': 'first'})
                since_date = since_obj.isoformat()
            elif date_str and len(date_str.split(' - ')) == 2:
                since_str, until_str = date_str.split(' - ')
                since_obj = dateparser.parse(since_str, languages=['de'], settings={'PREFER_DAY_OF_MONTH': 'first'})
                until_obj = dateparser.parse(until_str, languages=['de'], settings={'PREFER_DAY_OF_MONTH': 'last'})
                since_date = since_obj.isoformat()
                until_date = until_obj.isoformat()

            description = tds[1].get_text()
            location = tds[2].get_text()
            role_description = tds[3].get_text()
            
            c.execute(
                '''
                INSERT INTO data (
                    name,
                    department,
                    faculty,
                    since_date,
                    until_date,
                    description,
                    location,
                    role_description
                )
                VALUES
                (?,?,?,?,?,?,?,?)
                ''',
                [name,
                department,
                faculty,
                since_date,
                until_date,
                description,
                location,
                role_description]
            )
        conn.commit()

conn.close()
