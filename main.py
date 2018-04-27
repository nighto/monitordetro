import datetime
import os
import pickle
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool


DETRO = 'http://www.detro.rj.gov.br/regulares-tarifas-itinerario/include/linhas.php?parametro=%s'
LINES_PAGE = 'http://www.detro.rj.gov.br/regulares-tarifas-itinerario/'
INSTANCIAS = 40
FILEFORMAT = 'assets/%s.txt'
PARALLEL = False


def download_contents(param_id):
    return requests.get(DETRO % param_id).content


def get_line_codes():
    soup = BeautifulSoup(requests.get(LINES_PAGE).content, 'html.parser')
    return {x.attrs['value']: x.text  for x in soup.find(id='linhas').findAll('option')}


def dumpfile(key, content):
    with open(FILEFORMAT % key, '+wb') as file:
        pickle.dump(content, file)


def logchanges(text, message):
    with open('changes.txt', 'a') as changes:
        changes.write(('%s - ' + message) % (datetime.datetime.now(), text))


def process(item):
    """ Item like (key, text)"""
    key, text = item

    if not key or key == ' ':
        return

    content = download_contents(key).decode('utf-8')

    if not check_has_file(key):
        logchanges(text, 'Line Added: "%s"\n')
        dumpfile(key, content)
        return

    with open(FILEFORMAT % key, 'rb') as file:
        original = pickle.load(file)
    
    if original != content:
        logchanges(text, 'Line Changed: "%s"\n')
        dumpfile(key, content)
    
    return {
        'key': key,
        'text': text
    }


def check_has_file(key):
    return os.path.isfile(FILEFORMAT % key)


if __name__ == '__main__':
    pool = Pool(INSTANCIAS)
    lines = get_line_codes()
    lines = [(x, lines[x]) for x in lines]

    if PARALLEL:
        pool.map(process, lines)
    else:
        for line in lines:
            process(line)

