from settings import *
import csv
import json
import requests


def get_deals():

    try:
        with open(SOURCE_FILE, 'r', encoding=CHARSET) as file:

            deals = dict()
            csv_reader = csv.reader(file, delimiter=';')

            firstline = True

            for line in csv_reader:

                if firstline:
                    firstline = False
                    continue

                deals.update({line[0]: {'id': line[0], 'external_id': line[1], 'comments': list()}})

            return deals

    except csv.Error as err:
        print(f'Error reading CSV file: {err}')
        return dict()
    except UnicodeDecodeError as err:
        print(f'Error reading CSV file: {err}')
        return dict()
    except IOError as err:
        print('Error working with file ' + SOURCE_FILE)
        print(err)


def get_comments(deals):

    templ_start = '{"halt":0,"cmd": {'
    templ_end = '}}'

    i = 0
    packages = []
    req_str = ""

    for deal in deals.values():

        req_str += f'"{deal["id"]}":"crm.timeline.comment.list?filter[ENTITY_ID]={deal["id"]}&filter[ENTITY_TYPE]=deal",'
        if ((i + 1) % 50 == 0) or (i == len(deals) - 1):
            json_res = json.loads(templ_start + req_str[0:-1] + templ_end)
            packages.append(json_res)
            req_str = ""
        i += 1

    for batch in packages:
        req = requests.post(f'{B24_URI}/batch', json = batch)

        if req.status_code != 200:
            print('Error accessing to B24!')
            continue

        resp_json = req.json()
        res_errors = resp_json['result']['result_error']
        res_comments = resp_json['result']['result']

        if len(res_errors) > 0:
            for key,val in res_errors.items():
                print(key, ':', val['error_description'])

        if len(res_comments) > 0:
            for deal_id, comments in res_comments.items():
                deal = deals[deal_id]
                for comment_line in comments:
                    deal['comments'].append(comment_line)

    return deals

def save_result(deals):

    with open(RESULT_FILE, 'w') as json_file:
        json.dump(deals, json_file, ensure_ascii=False)

def main():

    deals = get_deals()

    if len(deals) == 0:
        print('Error while loading deals!')
        return

    deals = get_comments(deals)
    save_result(deals)


main()
