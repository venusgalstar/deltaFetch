#!/usr/bin/python3
import argparse
import hashlib
import os
import sys
import tempfile
import difflib 
import mysql.connector
from datetime import datetime

import requests
from lxml import html

from adapters import SendAdapterFactory
from model import WatchResult

try:

    mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "!QAZxsw2",
    database = "deltaFetch"
    )

    cursorObject = mydb.cursor()

    print("Connected to Database") 
except:
    print("Error occured while connecting database, please check it") 
    sys.exit(0)

# print(mydb)

def get_nodes(exp, page, ignore):
    """ Returns lxml nodes corresponding to the XPath expression """
    tree = html.fromstring(page)
    for i in ignore:
        for j in tree.xpath(i):
            j.drop_tree()
    return tree.xpath(exp)


def filter_document(nodes) -> str:
    """ Returns the text content of the specified nodes """
    text = ""
    for element in nodes:
        text = text + element.text_content()
    return text


def get_tmp_file(url: str) -> str:
    tmp_dir = tempfile.gettempdir()
    print(tmp_dir)
    m = hashlib.md5()
    m.update(url.encode('utf-8'))
    return os.path.join(tmp_dir, f'{m.hexdigest()[:6]}_cache.txt')


def diff_chars(a: str, b: str) -> int:
    d = difflib.unified_diff(a, b)
    return sum([i >= 2 and len(l) > 0 and l[0] in ['+', '-'] for i, l in enumerate(d)])

def get_previous_content(jobid:int, url:str, keyword:str) -> str:

    print(jobid)
    print(url)
    print(keyword)

    cursorObject.execute('''
            select content from task
            where id = %s and url = %s and keyword = %s;
        ''',(jobid, url, keyword,))

    myresult = cursorObject.fetchall()

    if len(myresult) == 0:
        cursorObject.execute('''
            insert into task (id, url, keyword, content)
            where id = %s and url = %s and keyword = %s;
        ''',(jobid, url, keyword,))

        return '<html></html>'
    else:
        return myresult[0]   
    
def compare_nodes(nodeList1, nodeList2):
    diffList = []
    for node in nodeList2:
        flag = 0
        for nodePrev in nodeList1:
            if node.text_content() == nodePrev.text_content():
                flag = 1
            break

        if flag ==0:
            diffList.push(node)
    return diffList

def insert_diff(node_diff, keyword, xpath, jobid):
    diff_text = ""
    search_result = 0
    keywordList = keyword.split()
    date_time = datetime.now()

    for node in node_diff:
        search_result_node = 1

        diff_text += xpath + node.text_content()

        if search_result != 0:
            continue

        for keyword in keywordList:
            if node.text_content().find(keyword) == -1:
                search_result_node = 0
            break
        if search_result_node == 1:
            search_result = 1
    
    cursorObject.execute('''
            insert into updated (jobid, diff, timestamp, result)
            values (%s, %s, %s, %s)
        ''',(jobid, diff_text, date_time.strftime("%m/%d/%Y %H:%M:%S"),search_result))
        
        
        




def main(args, remaining_args):

    print(args)

    urlList = args.url.split()

    for url in urlList:
        # Read length of old web page version
        nodePrev = get_nodes(args.xpath, get_previous_content(args.jobid, url, args.keyword), args.ignore)
        
        # Read length of current web page version
        # 301 and 302 redirections are resolved automatically
        r = requests.get(url, headers = { 'user-agent': args.user_agent })
        if 200 <= r.status_code <= 299 :
            nodeCurrent = get_nodes(args.xpath, r.text, args.ignore)
        else:
            print('Could not fetch %s.' % url)

        nodeDiff = compare_nodes(nodePrev, nodeCurrent)

        insert_diff(nodeDiff, args.keyword, args.xpath, args.jobid)

        update_content(r.text)

        
        # tmp_location = get_tmp_file(url)

        # doc1, doc2 = '', ''

        # try:
        #     adapter = SendAdapterFactory.get(args.adapter, remaining_args)
        # except AttributeError:
        #     sys.exit(1)

        # # Read length of old web page version
        # try:
        #     with open(tmp_location, 'r', encoding='utf8', newline='') as f:
        #         doc1 = filter_document(get_nodes(args.xpath, f.read(), args.ignore))
        # except:
        #     pass

        # if args.user_agent.lower() == 'firefox':
        #     args.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0' # Firefox 84 on Windows 10

        # # Read length of current web page version
        # # 301 and 302 redirections are resolved automatically
        # r = requests.get(args.url, headers = { 'user-agent': args.user_agent })
        # if 200 <= r.status_code <= 299 :
        #     doc2 = filter_document(get_nodes(args.xpath, r.text, args.ignore))
        # else:
        #     print('Could not fetch %s.' % args.url)

        # # Write new version to file
        # try:
        #     with open(tmp_location, 'w', encoding='utf-8', newline='') as f:
        #         f.write(r.text)
        # except Exception as e:
        #     print('Could not open file %s: %s' % (tmp_location, e))

        # diff = diff_chars(doc1, doc2)
        # if diff > args.tolerance:
        #     ok = adapter.send(WatchResult(args.url, diff))
        #     if not ok:
        #         sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'help':
        adapter_class = SendAdapterFactory.get_class(sys.argv[2])
        if adapter_class is None:
            sys.exit(1)
        else:
            adapter_class.adapter.get_parser().print_help()
            sys.exit(0)

    parser = argparse.ArgumentParser(prog='Website Watcher')
    parser.add_argument('-u', '--url', required=True, type=str, help='URL to watch')
    parser.add_argument('-j', '--jobid', required=True, type=str, help='Registered Job ID')
    # parser.add_argument('-c', '--cron', required=True, type=str, help='Cron Parameters')
    parser.add_argument('-k', '--keyword', default='', type=str, help='Key word list')
    parser.add_argument('-t', '--tolerance', default=0, type=int, help='Number of characters which have to differ between cached- and new content to trigger a notification')
    parser.add_argument('-x', '--xpath', default='//h4', type=str, help="XPath expression designating the elements to watch")
    parser.add_argument('-i', '--ignore', default='', type=str, nargs='+', help="One or multiple XPath expressions designating the elements to ignore")
    parser.add_argument('-ua', '--user-agent', default='muety/website-watcher', type=str, help='User agent header to include in requests (available shortcuts: "firefox")')
    parser.add_argument('--adapter', default='stdout', type=str, help='Send method to use. See "adapters" for all available')

    args, remaining_args = parser.parse_known_args()

    main(*parser.parse_known_args())

