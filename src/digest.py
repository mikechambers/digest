import argparse
import sys
import requests
from readability import Document
import browsercookie
import re
import os
from datetime import datetime

BASE_URL = "https://www.economist.com"
WEEKLY_URL = f"{BASE_URL}/weeklyedition/"
VERSION = "0.85.1"

INDEX_TEMPLATE = "index.html"
ARTICLE_TEMPLATE = "article.html"

user_agent = f"Digest/{VERSION}"
verbose = False

SECTION_INFO = [
    {"title": "The World This Week", "slug": "/the-world-this-week/"},
    {"title": "Leaders", "slug": "/leaders/"},
    {"title": "By Invitation", "slug": "/by-invitation/"},
    {"title": "Briefing", "slug": "/briefing/"},
    {"title": "United States", "slug": "/united-states/"},
    {"title": "The Americas", "slug": "/the-americas/"},
    {"title": "China", "slug": "/china/"},
    {"title": "Middle East and Africa", "slug": "/middle-east-and-africa/"},
    {"title": "Europe", "slug": "/europe/"},
    {"title": "Britain", "slug": "/britain/"},
    {"title": "International", "slug": "/international/"},
    {"title": "Special Report", "slug": "/special-report/"},
    {"title": "Business", "slug": "/business/"},
    {"title": "Finance and Economics", "slug": "/finance-and-economics/"},
    {"title": "Science and Technology", "slug": "/science-and-technology/"},
    {"title": "Culture", "slug": "/culture/"},
    {"title": "Economic and Financial Indicators", "slug": "/economic-and-financial-indicators/"},
    {"title": "Obituary", "slug": "/obituary/"}
]

SECTION_INFO = [{"title": "The Americas", "slug": "/the-americas/"}]

session = None

edition_date = None

def main():

    init_session()

    sections = parse_sections()

    sections = load_articles(sections)

    build_index(sections)

def load_articles(sections):

    for section in sections:
        articles = []
        for u in section["urls"]:
            u = f"{BASE_URL}{u}"
            
            article = load_url(u)

            doc = Document(article["text"])
            title = doc.title()
            content = doc.summary()

            articles.append({
                "title":title, 
                "content":content,
                "url":u,
                "file_name":u.split('/')[-1]
            })

        section["articles"] = articles

    return sections

def build_index(sections):

    output = ""
    for section in sections:
        print(section)
        output += f"<h2>{section['section']['title']}</h2>\n"

        output += "<div><ul>"
        for article in section['articles']:
            #{url.split('/')[-1]}
            title = article["title"]
            file_name = article["file_name"]
            dir = section['section']['slug'].strip('/')
            output += f"<li><a href='{dir}/{file_name}.html'>{title}</a></li>\n"

        output += "</ul></div>\n"

    template = load_template(INDEX_TEMPLATE)
    
    output = template.format(content = output, title=edition_date)
    print(output)


def parse_sections():
    global edition_date

    weekly = load_url(WEEKLY_URL)

    weekly_date = extract_date_from_url(weekly["url"])

    if weekly_date is None:
        edition_date = "Weekly Edition"
    else:
        edition_date = f"Weekly Edition : {weekly_date}"


    if weekly is None:
        print("Could not load weekly edition info from the Economist. Aborting")
        sys.exit(1)

    sections = []

    for section in SECTION_INFO:
        pattern = fr'href="({section['slug']}[^\"]+)"'
        found_urls = re.findall(pattern, weekly["text"])

        #remove duplicates
        found_urls = list(set(found_urls))

        sections.append({"section": section, "urls":found_urls})

    return sections

def extract_date_from_url(url):
    # Use a regular expression to extract the date part from the URL
    match = re.search(r'/(\d{4}-\d{2}-\d{2})', url)
    if match:
        date_str = match.group(1)  # Extracted date string in the format YYYY-MM-DD
        # Convert the date string into a datetime object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Format the datetime object into the desired format
        formatted_date = date_obj.strftime('%B %d, %Y')
        return formatted_date
    else:
        None

def load_url(url):
    response = session.get(url)

    if response.status_code == 200:
        return {"text":response.text, "url":response.url}
    else:
        return None

def init_session():
    global session
    cookies = browsercookie.firefox()
    session = requests.Session()
    session.cookies.update(cookies)

    headers = {
        'User-Agent': user_agent
    }

    session.headers.update(headers)
    
def load_template(template):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the full path to the file relative to the script
    file_path = os.path.join(script_dir, template)

    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    
    return file_content
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Add current weeks articles in The Economist to Safari reading list."
    )

    parser.add_argument(
        '--version',
        dest='version', 
        action='store_true', 
        help='display current version'
    )

    parser.add_argument(
        '--verbose',
        dest='verbose', 
        action='store_true', 
        help='display additional information as script runs'
    )
    
    parser.add_argument(
        "--user-agent",
        dest="user_agent",
        required=False, 
        help="the user agent to use when retrieving pages from the Economist website"
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        dest="output_dir",
        required=True, 
        help='The path to the directory'
    )

    args = parser.parse_args()

    if args.version:
        print(f"Dispatch version : {VERSION}")
        print("https://github.com/mikechambers/dispatch")
        sys.exit()

    if args.user_agent != None:
        user_agent = args.user_agent

    verbose = args.verbose

    main()