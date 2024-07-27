# Copyright (c) 2024 Mike Chambers
# https://github.com/mikechambers/dispatch
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import sys
import requests
import browsercookie
import re
import os
from datetime import datetime
import shutil
from datetime import datetime, timezone
import readtime
import uuid
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

BASE_URL = "https://www.economist.com"
WEEKLY_URL = f"{BASE_URL}/weeklyedition/"
VERSION = "0.85.2"

INDEX_TEMPLATE = "index.html"
ARTICLE_TEMPLATE = "article.html"
PODCAST_TEMPLATE = "podcast.xml"
PODCAST_ITEM_TEMPLATE = "item.xml"

STYLE_FILE = "style.css"

user_agent = f"Digest/{VERSION}"
verbose = False
cookie_source = "firefox"

SECTION_INFO = [
    {"title": "The World This Week", "slug": "/the-world-this-week/"},
    {"title": "Leaders", "slug": "/leaders/"},
    {"title": "Letters", "slug": "/letters/"},
    {"title": "By Invitation", "slug": "/by-invitation/"},
    {"title": "Briefing", "slug": "/briefing/"},
    {"title": "United States", "slug": "/united-states/"},
    {"title": "The Americas", "slug": "/the-americas/"},
    {"title": "Asia", "slug": "/asia/"},
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

session = None

dir_slug = None
edition_date = None
output_dir = None
weekly_url = None

reading_rate = 250

env = None

def main():
    global output_dir, env

    env = Environment(loader=FileSystemLoader('templates'))

    output_dir = os.path.abspath(output_dir)
    create_dir(output_dir)

    init_session()

    sections = parse_sections()

    output_dir = os.path.join(output_dir, dir_slug)
  
    if verbose:
        print(f"Writing to {output_dir}")

    create_dir(output_dir, True)

    sections = load_articles(sections)

    build_index(sections)
    build_sections(sections)
    build_podcast(sections)

    if verbose:
        print(f"Copying CSS file")
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

def build_podcast(sections):

    if verbose:
        print(f"Generating podcast file")

    #item_template = load_template(PODCAST_ITEM_TEMPLATE)

    second = 59
    minute = 59
    now = datetime.now(timezone.utc)

    items = []
    index = 1

    for section in sections:
        for article in section["articles"]:

            mp3 = article["mp3"]

            if not mp3:
                continue

            now = now.replace(minute = minute, second=second, microsecond=0)
            build_date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
            second -= 1

            if second < 1:
                second = 59
                minute -= 1
            
            items.append({
                "title" : f"{section["section"]["title"]} : {article["title"]}",
                "description":article["subtitle"] or "",
                "mp3" : mp3,
                "build_date" : build_date,
                "index" : index,
                "url" : article["url"],
                "uuid" : uuid.uuid4()
            })

            """
            items.append(
                item_template.format(
                    title = title,
                    mp3 = mp3,
                    build_date = build_date,
                    index = index,
                    url = url
                )
            )
            """

            index += 1


    #template = load_template(PODCAST_TEMPLATE)

    template = env.get_template(PODCAST_TEMPLATE)


    if verbose:
        print(f"Found {len(items)} mp3s")

    id = uuid.uuid4()

    context = {
        "edition_date" : edition_date,
        "build_date" : build_date,
        "uuid" : id,
        "items" : items
    }

    output = template.render(context)

    if verbose:
        print(f"Saving podcast file")

    write_file(output_dir, PODCAST_TEMPLATE, output)


def build_sections(sections):
    
    if verbose:
        print(f"Generating article files")

    template = env.get_template(ARTICLE_TEMPLATE)

    items = []

    for section in sections:
        for article in section["articles"]:
            items.append({"article":article, "section":section})

    num_articles = len(items)
    for i in range(num_articles):
        article = items[i]["article"]
        section = items[i]["section"]
        content = article['content']
        title = article['title']
        
        prev_title = "Index"
        prev_url = "../index.html"
        next_title = "Index"
        next_url = "../index.html"

        # Get previous and next articles
        prev_article = items[i-1]["article"] if i > 0 else None
        next_article = items[i+1]["article"] if i < num_articles - 1 else None

        if prev_article:
            #prev_article = prev_article["article"]
            prev_title = prev_article["title"]
            prev_url = f"../{prev_article["dir"]}/{prev_article["file_name"]}"

        if next_article:
            #next_article = next_article["article"]
            next_title = next_article["title"]
            next_url = f"../{next_article["dir"]}/{next_article["file_name"]}"


        read_time = readtime.of_html(''.join(content), wpm=reading_rate)

        context = {
            'content': content,
            'section_title': section["section"]["title"],
            'title': title,
            'prev_title': prev_title,
            'prev_url': prev_url,
            'next_title': next_title,
            'next_url': next_url,
            'economist_url': article["url"],
            'read_time': read_time,
            'subtitle': article["subtitle"],
            'section_blurb': article["section_blurb"]
        }


        # Add previous and next titles to the output
        output = template.render(context)
    
        write_file(article["dir"], article["file_name"], output)


def write_file(dir, file_name, data):

    section_dir = os.path.join(output_dir, dir)
    create_dir(section_dir)

    file_path = os.path.join(section_dir, file_name)

    if verbose:
        print(f"Writing file to : {file_path}")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(data)

def load_articles(sections):

    if verbose:
        print(f"Retrieving articles")

    for section in sections:
        articles = []
        for u in section["urls"]:
            u = f"{BASE_URL}{u}"
            
            root = load_url(u)
            soup = BeautifulSoup(root["text"], 'html.parser')
            
            article = soup.find('section', {'data-body-id': 'cp2'})

            if article is None:
                article = soup.find('section', {'class':"css-k2wbwk e13topc91"})

            title_regex = re.compile(r'css-(1p83fk8|3swi83) e1r8fcie0')
            title = soup.find('h1', {'class': title_regex})
            title = title.decode_contents()

            subtitle_regex = re.compile(r'css-(1ms10sa|1ss9ydi) eg03uz0')
            subtitle_tag = soup.find('h2', {'class' : subtitle_regex})
     
            subtitle = ""
            if subtitle_tag:
                subtitle = subtitle_tag.decode_contents()

            section_blurb_tag = soup.find('span', {'class':'css-rjcumh e1vi1cqp0'})

            pre_section_tag = soup.find('section', {'class':'css-1ugvd2u e18wk22u0'})

            pre_section_figure_tag = None
            if pre_section_tag:
                pre_section_figure_tag = pre_section_tag.find('figure')

            content = []
            if pre_section_figure_tag:
                img_html = soup_img_from_figure(pre_section_figure_tag)

                if img_html:
                    content.append(img_html)

            section_blurb = ""
            if section_blurb_tag:
                match = re.search(r'<!-- -->\s*(.*)', section_blurb_tag.decode_contents())

                if match:
                    section_blurb = str(match.group(1))


            #remove aside tags

            for s in article.select('aside'):
                s.extract()

            tags = article.find_all(lambda tag: 
                     (tag.name == 'p' and tag.get('data-component') == 'paragraph') or 
                     tag.name == 'figure')

            for idx, tag in enumerate(tags):
                if tag.name == 'p':
                    #content_body += str(tag)
                    #content_body += f"<p>{tag.decode_contents()}</p>\n"
                    content.append(tag.decode_contents())
                elif tag.name == 'figure':
                    #img_tag = tag.find('img')

                    img_html = soup_img_from_figure(tag)

                    if img_html:
                        content.append(img_html)

            audio = soup.find('audio')

            mp3 = None
            if audio:
                mp3 = audio["src"]

            articles.append({
                "title":title, 
                "content":content,
                "url":u,
                "file_name": f"{u.split('/')[-1]}.html",
                "dir": section['section']['slug'].strip('/'),
                "mp3":mp3,
                "subtitle":subtitle,
                "section_blurb":section_blurb
            })

        section["articles"] = articles

    return sections

def soup_img_from_figure(tag):
    img_tag = tag.find('img')

    if img_tag and 'src' in img_tag.attrs:
        img_url = img_tag['src']

        return f"<img src='{img_url}' class='parsed_image' />"
    else:
        return None
                    
def build_index(sections):

    if verbose:
        print(f"Generating index")

    template = env.get_template(INDEX_TEMPLATE)

    context = {
        "sections":sections,
        "title":edition_date,
        "weekly_url":weekly_url
    }

    output = template.render(context)

    write_file(output_dir, "index.html", output)

def parse_sections():

    if verbose:
        print(f"Retrieving weekly edition")

    global edition_date
    global weekly_url

    weekly = load_url(WEEKLY_URL)

    weekly_url = weekly["url"]
    weekly_date = extract_date_from_url(weekly_url)

    if weekly_date is None:
        edition_date = "Weekly Edition"
    else:
        edition_date = f"Weekly Edition : {weekly_date}"


    if weekly is None:
        print("Could not load weekly edition info from the Economist. Aborting")
        sys.exit(1)

    sections = []

    article_count = 0
    for section in SECTION_INFO:
        pattern = fr'href="({section['slug']}[^\"]+)"'
        found_urls = re.findall(pattern, weekly["text"])

        #remove duplicates
        #found_urls = list(set(found_urls))
        found_urls = remove_duplicate_strings(found_urls)

        article_count += len(found_urls)
        sections.append({"section": section, "urls":found_urls})

    if verbose:
        print(f"Found {article_count} articles in {len(sections)} sections")

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

        dir_slug = f"{date_str}"
        # Convert the date string into a datetime object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Format the datetime object into the desired format
        formatted_date = date_obj.strftime('%B %d, %Y')
        return formatted_date
    else:
        None

def load_url(url):

    if verbose:
        print(f"Retrieving URL {url}")

    response = session.get(url)

    code = response.status_code
    if code == 200:
        return {"text":response.text, "url":response.url}
    else:
        raise Exception(f"Non 200 Status code returned ({code}) : {url}")

def init_session():
    global session

    cookies = get_browser_cookies(cookie_source)

    if verbose:
        print(f"Using cookies from {cookie_source}")

    session = requests.Session()
    session.cookies.update(cookies)

    headers = {
        'User-Agent': user_agent
    }

    if verbose:
        print(f"Making requests with User Agent : {user_agent}")

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
        "--reading-rate",
        dest="reading_rate",
        required=False,
        type=int,
        help=f"Words per minute read to determine reading length for articles. Default {reading_rate}"
    )

    parser.add_argument(
        "--cookie-source",
        dest="cookie_source",
        required=False, 
        help="The browser that cookies will be retrieved from for the Economist. Must be logged into economist.com and have access to digital edition. Options are firefox (default), chrome, edge, opera."
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        dest="output_dir",
        help='The path to the directory that the digest will be created'
    )

    args = parser.parse_args()

    if not args.version and not args.output_dir:
        parser.error('--output-dir is required unless --version is specified')

    if args.version:
        print(f"Digest version : {VERSION}")
        print("https://github.com/mikechambers/dispatch")
        sys.exit()

    if args.user_agent:
        user_agent = args.user_agent

    if args.cookie_source:
        cookie_source = args.cookie_source

    if args.reading_rate:
        reading_rate = args.reading_rate

    verbose = args.verbose
    output_dir = args.output_dir

    try:
        main()
    except Exception as e:
        print(f"An error occurred. Aborting : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)