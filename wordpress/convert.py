import re
from xml.etree import ElementTree

import datetime
import pathlib

import os

import sys
from bs4 import BeautifulSoup

from PostModel import PostModel
from review_converter import ReviewConverter
from known_labels import known_labels, normalized_labels

BASE_DIR = '../content'

review_category = [
    "review",
    "reviews",
    "cdreview",
    "cdreviews",
    "vinylreview",
    "vinylreviews",
    "vinyl-reviews",
    "tapereviews",
    "tapereview",
    "fanzinereview",
    "fanzinereviews",
]

interview_category = [
    'interview',
    'interviews'
]

blog_category = [
    'interview',
    'blog',
    'special',
    'specials'
]
download_category = [
    'download-dungeon',
    'download'
]

bandcamp_category = ['bandcamp']
news_category = ['news']
concert_category = ['konzert-reviews']

NS_WP = '{http://wordpress.org/export/1.2/}'
NS_DC = '{http://purl.org/dc/elements/1.1/}'
NS_CONTENT = '{http://purl.org/rss/1.0/modules/content/}'

slug_replace = {
    '%e2%80%93': '-',
    '%e2%80%a2': '',
    '%ef%bb%bf': '',
    '%e2%80%8e': '',
    '%c2%b2': '2',
    '%e0%a4%97%e0%a4%a3%e0%a5%87%e0%a4%b6-': ''
}

redirect_data = ''
trash_bin = ''
authors = {}
meta_content = ''

def process_content_generic(post):
    content = post.content
    content = content.replace('<strong>', '**')
    content = content.replace('</strong>', '**')
    content = content.replace('<b>', '**')
    content = content.replace('</b>', '**')
    content = content.replace('<em>', '_')
    content = content.replace('</em>', '_')
    content = content.replace('<i>', '_')
    content = content.replace('</i>', '_')
    content = content.replace('<hr>', '---')
    content = content.replace('<hr/>', '---')
    content = content.replace('<hr />', '---')
    post.content = content
    return post


def process_content_review(post):
    return ReviewConverter(known_labels, normalized_labels).convert(post)


def extract_bandcamp_player(post):
    soup = BeautifulSoup(post.content, 'lxml')
    iframes = soup.find_all('iframe')
    if len(iframes) == 1:
        if 'bandcamp' in iframes[0].get('src'):
            post.player = iframes[0]
            post.content = decompose_iframes(post.content)
    return post


def decompose_iframes(content):
    soup = BeautifulSoup(content, 'lxml')
    soup.find('iframe').decompose()
    return str(soup.body).replace('<body>', '').replace('</body>', '')


def extract_cover(post):
    soup = BeautifulSoup(post.content, 'lxml')
    img = soup.find_all('img')
    if img:
        post.image = img[0].get('src')
        post.content = decompose_cover(post.content)
    return post


def decompose_cover(content):
    soup = BeautifulSoup(content, 'lxml')
    img = soup.find('img')
    if img:
        img.decompose()
    return str(soup.body).replace('<body>', '').replace('</body>', '')


def process(node):
    post = PostModel()

    date = datetime.datetime.strptime(node.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z')
    date_str = date.strftime('%Y')
    link = node.find('link').text

    categories = node.findall('category')
    category = extract_category(categories)

    destination_dir = mkdir(category, date_str)

    post.title = node.find('title').text
    post.author = authors[node.find(NS_DC+'creator').text]
    post.date = date
    post.slug = get_slug(node)
    post.content = node.find(NS_CONTENT + 'encoded').text

    post.original_content = node.find(NS_CONTENT + 'encoded').text

    post.tags = get_tags(categories)
    post.category = category

    post = process_content_generic(post)
    if category == 'reviews':
        post = extract_bandcamp_player(post)
        post = extract_cover(post)
        post = process_content_review(post)

    abs_file = os.path.join(destination_dir, post.slug + '.md')
    post.dumps(abs_file)

    if post.raw_meta:
        global meta_content
        for line in post.raw_meta.splitlines():
            if not re.match('\d{1,} (Lieder|Songs) [\/-] .*( [mM]in\?.)?', line):
                meta_content += line +'\n'

    if 'trash' != category:
        create_redirect(category, date_str, link, post.slug)
    else:
        global trash_bin
        trash_bin += '{0}\n'.format(abs_file)


def get_tags(categories):
    tags = []
    for c in categories:
        if c.get('domain') == 'post_tag':
            tags.append(c.text)
    return tags


def create_redirect(category, date_str, link, slug):
    # new_url = 'https://necrcoslaughter.de/{0}/{1}'.format(category, slug)
    new_url = 'https://necrcoslaughter.de/{0}/{1}/{2}'.format(category, date_str, slug)
    global redirect_data
    redirect_data += 'Redirect 301 {0} {1}\n'.format(link[len('https://necroslaughter.de'):], new_url)


def get_slug(node):
    title = node.find(NS_WP + 'post_name').text
    for key in slug_replace:
        title = title.replace(key, slug_replace[key])
    return title


def extract_category(categories):
    cat_list = []
    for c in categories:
        cat_list.append(c.get('nicename').lower())

    if any(c in concert_category for c in cat_list):
        return 'concert'
    elif any(c in review_category for c in cat_list):
        return 'reviews'
    elif any(c in interview_category for c in cat_list):
        return 'interviews'
    elif any(c in bandcamp_category for c in cat_list):
        return 'bandcamp'
    elif any(c in news_category for c in cat_list):
        return 'news'
    elif any(c in download_category for c in cat_list):
        return 'trash'
    elif any(c in blog_category for c in cat_list):
        return 'blog'


# print('{0}: {1} @ {2}: {1}'.format(node.find('title').text, c.get('domain'), c.get('nicename'), c.text))


def mkdir(cat, datestring):
    base = os.path.dirname(os.path.abspath(__file__))
    content = BASE_DIR
    destination = os.path.join(base, content, cat, datestring)
    # destination = os.path.join(base, content, datestring)
    # print(destination)
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
    return destination


def process_meta():
    pass
    new_meta = ''
    for line in meta_content.splitlines():
        if not line.startswith('<a') and not line.startswith('http') and not line.startswith('---') and not line.strip() == '' and not line.startswith('**Info'):
            new_meta += line + '\n'
    #print(new_meta)
    base = os.path.dirname(os.path.abspath(__file__))
    abs_file = os.path.join(base, 'labels.txt')
    with open(abs_file,'w') as f:
        f.write(new_meta)


with open('necroslaughterde.xml', 'r') as f:
    root = ElementTree.parse(f).getroot()
    for author_node in root.find('channel').findall(NS_WP+'author'):
        login = author_node.find(NS_WP+'author_login').text
        display_name = author_node.find(NS_WP+'author_display_name').text
        authors[login]=display_name.replace(' -', '')
    for child in root.find('channel').findall('item'):
        process(child)
        # print(redirect_data)

    #process_meta()

