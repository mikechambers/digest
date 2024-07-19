import argparse
import sys
import requests
from readability import Document
import browsercookie
import re
import os
from datetime import datetime
import shutil

BASE_URL = "https://www.economist.com"
WEEKLY_URL = f"{BASE_URL}/weeklyedition/"
VERSION = "0.85.1"

INDEX_TEMPLATE = "index.html"
ARTICLE_TEMPLATE = "article.html"
STYLE_FILE = "style.css"

user_agent = f"Digest/{VERSION}"
verbose = False
cookie_source = "firefox"

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

#SECTION_INFO = [{"title": "The Americas", "slug": "/the-americas/"}]

session = None

dir_slug = None
edition_date = None

output_dir = None

def main():

    global output_dir
    output_dir = os.path.abspath(output_dir)
    create_dir(output_dir)

    init_session()
    sections = parse_sections()

    output_dir = os.path.join(output_dir, dir_slug)
  
    create_dir(output_dir, True)

    sections = load_articles(sections)

    build_index(sections)
    build_sections(sections)

    shutil.copy2(
        os.path.abspath(STYLE_FILE),
        os.path.join(output_dir, STYLE_FILE)
    )


def create_dir(path, delete=False):
    if os.path.exists(path):
        if delete:
            shutil.rmtree(path)
        else:
            return

    os.makedirs(path)

def build_sections(sections):
    
    template = load_template(ARTICLE_TEMPLATE)

    articles = []
    for section in sections:
        articles.extend(section["articles"])

    #articles = section["articles"]
    num_articles = len(articles)

    for i in range(num_articles):
        article = articles[i]
        content = article['content']
        title = article['title']
        
        # Get previous and next articles
        prev_article = articles[i-1] if i > 0 else None
        next_article = articles[i+1] if i < num_articles - 1 else None
        
        prev_title = "Index"
        prev_url = "../index.html"
        next_title = "Index"
        next_url = "../index.html"

        if prev_article:
            prev_title = prev_article["title"]
            prev_url = f"../{prev_article["dir"]}/{prev_article["file_name"]}"

        if next_article:
            next_title = next_article["title"]
            next_url = f"../{next_article["dir"]}/{next_article["file_name"]}"

        # Add previous and next titles to the output
        output = template.format(
            content=content,
            title=title,
            prev_title=prev_title,
            prev_url = prev_url,
            next_title=next_title,
            next_url = next_url
        )
    
        write_file(article["dir"], article["file_name"], output)


def build_sections2(sections):
    
    template = load_template(ARTICLE_TEMPLATE)

    for section in sections:
        for article in section["articles"]:

            content = article['content']
            title=article['title']
            output = template.format(content = content, title=title)
        
            write_file(article["dir"], article["file_name"], output)

def write_file(dir, file_name, data):
    section_dir = os.path.join(output_dir, dir)
    create_dir(section_dir)

    file_path = os.path.join(section_dir, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(data)


def load_articles(sections):

    for section in sections:
        articles = []
        for u in section["urls"]:
            u = f"{BASE_URL}{u}"
            
            article = load_url(u)

            doc = Document(article["text"])
            title = doc.title()
            content = doc.summary(html_partial=True)

            articles.append({
                "title":title, 
                "content":content,
                "url":u,
                "file_name": f"{u.split('/')[-1]}.html",
                "dir": section['section']['slug'].strip('/')
            })

        section["articles"] = articles

    return sections

def build_index(sections):

    output = ""
    for section in sections:

        output += f"<h2>{section['section']['title']}</h2>\n"

        output += "<div><ul class='section-list'>"
        for article in section['articles']:
            #{url.split('/')[-1]}
            title = article["title"]
            file_name = article["file_name"]
            dir = article["dir"]
            output += f"<li><a href='{dir}/{file_name}'>{title}</a></li>\n"

        output += "</ul></div>\n"

    template = load_template(INDEX_TEMPLATE)
    
    output = template.format(content = output, title=edition_date)

    write_file(output_dir, "index.html", output)


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
        #found_urls = list(set(found_urls))
        found_urls = remove_duplicate_strings(found_urls)

        sections.append({"section": section, "urls":found_urls})

    return sections

def remove_duplicate_strings(items):
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items

def extract_date_from_url(url):

    global dir_slug
    # Use a regular expression to extract the date part from the URL
    match = re.search(r'/(\d{4}-\d{2}-\d{2})', url)
    if match:
        date_str = match.group(1)  # Extracted date string in the format YYYY-MM-DD

        dir_slug = f"economist-{date_str}"
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

    cookies = get_browser_cookies(cookie_source)
    session = requests.Session()
    session.cookies.update(cookies)

    headers = {
        'User-Agent': user_agent
    }

    session.headers.update(headers)
    
def get_browser_cookies(browser_name):
    if browser_name.lower() == 'chrome':
        return browsercookie.chrome()
    elif browser_name.lower() == 'firefox':
        return browsercookie.firefox()
    elif browser_name.lower() == 'edge':
        return browsercookie.edge()
    elif browser_name.lower() == 'opera':
        return browsercookie.opera()
    else:
        raise ValueError("Unsupported --cookie-source name. Supported browsers: 'chrome', 'firefox', 'edge', 'opera'.")


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
        "--cookie-source",
        dest="cookie_source",
        required=False, 
        help="The browser that cookies will be retried from for the Economist. Must be logged into the economist. Options are firefox (default), chrome, edge, opera."
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

    if args.cookie_source != None:
        cookie_source = args.cookie_source

    verbose = args.verbose
    output_dir = args.output_dir

    main()