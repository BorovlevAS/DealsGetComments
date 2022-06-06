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

                deals.update({line[0]: {'id': line[0], 'external_id': line[1], 'comments': dict()}})

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

    deals_with_files = {}

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
        req = requests.post(f'{B24_URI}/batch', json=batch)

        if req.status_code != 200:
            print('Error accessing to B24!')
            continue

        resp_json = req.json()
        res_errors = resp_json['result']['result_error']
        res_comments = resp_json['result']['result']

        if len(res_errors) > 0:
            for key, val in res_errors.items():
                print(key, ':', val['error_description'])

        if len(res_comments) > 0:
            for deal_id, comments in res_comments.items():
                deal = deals[deal_id]
                for comment_line in comments:
                    deal['comments'].update({comment_line['ID']: comment_line})
                    if 'FILES' in comment_line.keys():
                        for file in comment_line['FILES'].keys():
                            deals_with_files.update({file: {'deal_id': deal_id, 'comment_id': comment_line['ID']}})

    return [deals, deals_with_files]


def get_files(deals, deals_with_files):

    templ_start = '{"halt":0,"cmd": {'
    templ_end = '}}'

    i = 0
    packages = []
    req_str = ""

    for file_id in deals_with_files.keys():

        req_str += f'"{file_id}":"disk.file.get?id={file_id}",'
        if ((i + 1) % 50 == 0) or (i == len(deals_with_files) - 1):
            json_res = json.loads(templ_start + req_str[0:-1] + templ_end)
            packages.append(json_res)
            req_str = ""
        i += 1

    for batch in packages:
        req = requests.post(f'{B24_URI}/batch', json=batch)

        if req.status_code != 200:
            print('Error accessing to B24!')
            continue

        resp_json = req.json()
        res_errors = resp_json['result']['result_error']
        res_files = resp_json['result']['result']

        if len(res_errors) > 0:
            for key, val in res_errors.items():
                print(key, ':', val['error_description'])

        if len(res_files) > 0:
            for file_id, resp in res_files.items():
                deal_comment = deals_with_files[file_id]
                deal = deals[deal_comment['deal_id']]
                comment = deal['comments'][deal_comment['comment_id']]
                file_in_deals = comment['FILES'][file_id]
                file_in_deals['urlDownload'] = resp['DOWNLOAD_URL']

    return deals


def save_result(deals):

    with open(RESULT_FILE, 'w', encoding=CHARSET) as json_file:
        json.dump(deals, json_file, ensure_ascii=False, indent=4, sort_keys=True)


def main():

    deals = get_deals()

    if len(deals) == 0:
        print('Error while loading deals!')
        return

    deals, deals_with_files = get_comments(deals)

    if len(deals_with_files) > 0:
        deals = get_files(deals, deals_with_files)

    save_result(deals)


main()
