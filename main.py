import csv
from settings import *


def get_deals():

    deals = dict()

    try:
        with open(SOURCE_FILE, 'r', encoding=CHARSET) as file:
            csv_reader = csv.reader(file, delimiter=';')

            firstline = True
            for line in csv_reader:

                if firstline:
                    firstline = False
                    continue

                deals.update({'id': line[0], 'external_id': line[1]})

    except csv.Error as err:
        print(f'Error reading CSV file: {err}')
        return dict()
    except UnicodeDecodeError as err:
        print(f'Error reading CSV file: {err}')
        return dict()
    except IOError as err:
        print('Error working with file ' + SOURCE_FILE)
        print(err)

    return deals


def main():

    deals = get_deals()

    if len(deals) == 0:
        print('Не удалось загрузить список сделок!')
        return

main()
