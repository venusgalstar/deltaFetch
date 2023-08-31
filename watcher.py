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

# Connecting to database
try:

    mydb = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "!QAZxsw2",
        database = "deltaFetch",
        charset = "utf8"
    )

    cursorObject = mydb.cursor()
    cursorObject.execute("SET NAMES utf8mb4; ")
    mydb.commit()

    print("Connected to Database") 
except:
    print("Error occured while connecting database, please check it") 
    sys.exit(0)

# Get html tags from webpage content with exp/xpath
def get_nodes(exp, page, ignore):
    """ Returns lxml nodes corresponding to the XPath expression """
    tree = html.fromstring(page)
    for i in ignore:
        for j in tree.xpath(i):
            j.drop_tree()
    return tree.xpath(exp)

# Get previous content from database
def get_previous_content(jobid:int, url:str, keyword:str, xpath:str) -> str:

    cursorObject.execute('''
            select content from task where jobid = %s and url = %s and keyword = %s and xpath = %s;
        ''',(jobid, url, keyword, xpath,))

    myresult = cursorObject.fetchall()

    if len(myresult) == 0:
        cursorObject.execute('''
            insert into task (jobid, url, keyword, content, xpath)
            values (%s, %s, %s, %s, %s)
        ''',(jobid, url, keyword,"<html></html>",xpath))

        mydb.commit()

        return '<html></html>'
    else:
        return myresult[0][0]
    
# Compare two node list, nodeList1 is old one.
def compare_nodes(nodeList1, nodeList2):
    diffList = []
    for node in nodeList2:
        flag = 0
        for nodePrev in nodeList1:
            if node.text_content() == nodePrev.text_content():
                flag = 1
                break

        if flag == 0:
            diffList.append(node)
    return diffList

# Insert updated content to database
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

    if diff_text != "":
        cursorObject.execute('''
                insert into updated (jobid, diff, timestamp, search)
                values (%s, %s, %s, %s);
            ''',(jobid, diff_text, date_time.strftime("%Y-%m-%d %H:%M:%S"), search_result))
        mydb.commit()

# Update webpage content on databse
def update_content(new_content, jobid, url, keyword, xpath):
    
    cursorObject.execute('''
        update task set content = %s where jobid = %s and url = %s and keyword = %s and xpath = %s;
    ''',(new_content, jobid, url, keyword, xpath))

    mydb.commit()
    
def main(args, remaining_args):

    print(args)

    # First, register crontabe if it has cron parameters
    if args.cron != "":
        with open("/etc/crontab", 'a', encoding='utf8', newline='') as f:

            print(args.cron)
            cron_command = ""
            
            for idx in range(len(args.cron)):
                cron_command += args.cron[idx] + " "

            for idx in range(5 - len(args.cron)):
                cron_command += " *"
            
            cron_command += " root python3 /root/work/deltaFetch/watcher.py -u " + args.url
            cron_command += " -j " + args.jobid 

            if len(args.keyword) != 0:
                cron_command += " -k "
                
                for word in args.keyword:
                    cron_command += word + " "

            if args.xpath != "":
                cron_command += " -x " + args.xpath + " " 

            print(cron_command)
            f.write(cron_command)
            f.write("\n")
            f.close()
            # f.write(args.cron +)

    combined_keyword = ""
    for word in args.keyword:
        combined_keyword += word + " "

    urlList = args.url.split()

    for url in urlList:
        # Read previous node from old content
        nodePrev = get_nodes(args.xpath, get_previous_content(args.jobid, url, combined_keyword, args.xpath), args.ignore)
        print(nodePrev)
        # Read current node from current content
        # 301 and 302 redirections are resolved automatically
        r = requests.get(url, headers = { 'user-agent': args.user_agent })
        print(r.status_code)
        if 200 <= r.status_code <= 299 :
            nodeCurrent = get_nodes(args.xpath, r.text, args.ignore)
        else:
            print('Could not fetch %s.' % url)

        # Get different node list 
        nodeDiff = compare_nodes(nodePrev, nodeCurrent)

        # Insert different nodes as text to database
        insert_diff( nodeDiff, combined_keyword, args.xpath, args.jobid )

        # Update task with new content
        update_content( r.text, args.jobid, url, combined_keyword, args.xpath )

        mydb.close()

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
    parser.add_argument('-c', '--cron', default='', type=str, nargs='+', help='Cron Parameters')
    parser.add_argument('-k', '--keyword', default='', nargs='+', type=str, help='Key word list')
    parser.add_argument('-t', '--tolerance', default=0, type=int, help='Number of characters which have to differ between cached- and new content to trigger a notification')
    parser.add_argument('-x', '--xpath', default='//h4', type=str, help="XPath expression designating the elements to watch")
    parser.add_argument('-i', '--ignore', default='', type=str, nargs='+', help="One or multiple XPath expressions designating the elements to ignore")
    parser.add_argument('-ua', '--user-agent', default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36', type=str, help='User agent header to include in requests (available shortcuts: "firefox")')
    parser.add_argument('--adapter', default='stdout', type=str, help='Send method to use. See "adapters" for all available')

    args, remaining_args = parser.parse_known_args()

    main(*parser.parse_known_args())

