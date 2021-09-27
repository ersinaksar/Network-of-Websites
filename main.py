import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import mgclient
import sys
import colorama
import random
import time

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

total_urls_visited = 0

node_lilst = []
line = []

start_url = ""
end_url = ""
depth = 2
flag = True

connection = mgclient.connect(host='127.0.0.1', port=7687)
connection.autocommit = True
cursor = connection.cursor()

def findDepth(start_url):
    links = get_all_website_links(start_url)
    global depth
    global distance
    global node_id
    node_id = 0
    global layer
    layer = 0
    global connection
    global cursor

    connection.cursor().execute("""CREATE (n:StartURL)
			   SET n.id = '{id}'
			   SET n.distance = '{distance}'
			   SET n.url = '{url}'
               SET n.depth = '{depth}'
			   """.format(id=0, distance=0, url=start_url, depth = depth))

    for link in links:
        distance = 1
        node_id = node_id + 1
        connection.cursor().execute("""CREATE (n:xLayer)
				   SET n.id = '{id}'
				   SET n.distance = '{distance}'
				   SET n.url = '{url}'
                   SET n.parent = '{parent}'
				   """.format(id=node_id, distance=1, url=link, parent= 0))
        query = """
		MATCH (n1:StartURL {id: """ + str(0) + """})
        MATCH (n2:xLayer {id: """ + str(node_id) + """})
        CREATE (n1)-[:Inside]->(n2) """
        connection.cursor().execute(query)
        parent_node_id = node_id
        recursive_connection(link, parent_node_id)
def recursive_connection(link, parent_node_id):
    # start_url => 1. node
    # link => 2. node
    # rec_link => 3. node
    global depth
    global flag
    global node_id
    global distance
    global connection
    global cursor
    distance = distance + 1
    depth = depth - 1
    rec_links = get_all_website_links(link)
    for rec_link in rec_links:
        node_id = node_id + 1
        connection.cursor().execute("""CREATE (n:xLayer)
				   SET n.id = '{id}'
				   SET n.distance = '{distance}'
				   SET n.url = '{url}'
                   SET n.parent = '{parent}'
				   """.format(id=node_id, distance=distance, url=rec_link, parent = parent_node_id))
        query = """
		MATCH (n1:xLayer {id: """ + str(parent_node_id) + """})
        MATCH (n2:xLayer {id: """ + str(node_id) + """})
        CREATE (n1)-[:Inside]->(n2) """
        connection.cursor().execute(query)
        depth = depth - 1
        if depth < 0:
            flag = False
            break
        if flag == True:
            parent_node_id = node_id
            depth = depth + 1
            recursive_connection(link, parent_node_id)
def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)
def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    request_time = random.uniform(0.1,0.8)
    time.sleep(request_time)
    urls = set()
    domain_name = urlparse(url).netloc
    try:
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
    except:
        #print("​WebsiteNotFoundError(URL)")
        sys.exit()
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            continue
        if href in internal_urls:
            continue
        if domain_name not in href:
            if href not in external_urls:
                #print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        #print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls
def find_url_path():
    global end_url
    global start_url
    global connection
    global cursor
    q = "MATCH (n :StartURL) RETURN n AS nodes"
    cursor.execute(q)
    myresult = cursor.fetchall()
    if len(myresult) == 0:
        raise Exception("​WebsiteNotFoundError(URL)")
    n = myresult[0]
    n0 = n[0]
    depth = n0.properties['depth']
    qx = """MATCH (n :xLayer) RETURN n AS nodes"""
    cursor.execute(qx)
    myresultx = cursor.fetchall()
    global url_path_list
    url_path_list = []
    index = 0
    for node in myresultx:
        index = index + 1
        nx = node[0]
        urlx = nx.properties['url']
        if urlx == end_url:
            url_path_list.append(nx)
    solution_list = []
    solution_list.append(end_url)
    global idx_parent
    if(len(url_path_list) > 1 ):
        length_list = []
        for node in url_path_list:
            dis = int(node.properties['distance'])
            length_list.append(dis)
        best_dis = min(length_list)
        node_index = length_list.index(best_dis) #index of shortest way for multi solution path
        nx = url_path_list[node_index]
    parent_node_ID = int(nx.properties['parent'])
    end_url_depth = int(nx.properties['distance'])
    if(parent_node_ID != 0):
        for i in range(end_url_depth):
            for node in myresultx:
                nx = node[0]
                idx = nx.properties['id']
                idx_parent = nx.properties['parent']
                if parent_node_ID != idx:
                    continue
                if parent_node_ID == idx:
                    solution_list.append(nx)
                    break
            parent_node_ID = idx_parent
        solution_list.append(start_url)
        ordered_solution_list = list(reversed(solution_list))
        ordered_solution_list_URL = []
        for i in ordered_solution_list:
            if i == start_url:
                ordered_solution_list_URL.append(i)
            elif i == end_url:
                ordered_solution_list_URL.append(i)
            else:
                xurl = i.properties['url']
                ordered_solution_list_URL.append(xurl)
        print("Shortest Path: ", len(ordered_solution_list_URL) - 1, "clicks" )
        count = 0
        for i in ordered_solution_list_URL:
            print(count, " - ", i)
            count = count + 1

    else:
        solution_list.append(start_url)
        ordered_solution_list = list(reversed(solution_list))
        ordered_solution_list_URL = []
        for i in ordered_solution_list:
            if i == start_url:
                ordered_solution_list_URL.append(i)
            elif i == end_url:
                ordered_solution_list_URL.append(i)
            else:
                xurl = i.properties['url']
                ordered_solution_list_URL.append(xurl)
        print("Shortest Path: ", len(ordered_solution_list_URL) - 1, "clicks" )
        count = 0
        for i in ordered_solution_list_URL:
            print(count, " - ", i)
            count = count + 1

def deleteAll():
    connection.cursor().execute("""MATCH (n) DETACH DELETE n""")

if __name__ == "__main__":
    """
    Example Run
    python main.py delete
    python main.py network https://memgraph.com
    python main.py path https://memgraph.com https://discourse.memgraph.com

    """
    for arg in sys.argv:
        print(arg, " ", end="")
        line.append(arg)
    print()
    if ( len(line) == 5):
        depth = int(line[4])
    else:
        depth = 2

    if (line[1] == "network"):
        start_url = line[2]
        findDepth(start_url)

    if(len(line) == 4 ):
        if(line[1] == "path"):
            start_url = line[2]
            end_url = line[3]
            find_url_path()

    if (line[1] == "delete"):
        deleteAll()
