import os
import sys
import re

import selenium
from selenium import webdriver

import time

MAX_DELAY_SEC = 120
MIN_DELAY_SEC = 5
# webdriver.Firefox(executable_path='/usr/local/bin/geckodriver')
web = None
log_file = os.path.expanduser("~/deepl.log")


def close_web():
    global web
    if web:
        web.close()
        web = None


def init_web():
    global web
    # opt.set_headless()
    prof = webdriver.FirefoxProfile()
    prof.set_preference("dom.webdriver.enabled", False)
    prof.set_preference('useAutomationExtension', False)
    prof.update_preferences()

    print('Opening web browser.')
    with open(log_file, 'a') as lf:
        lf.write("web open")
    web = webdriver.Firefox(
        firefox_profile=prof,
        desired_capabilities=webdriver.DesiredCapabilities.FIREFOX)

    print('Loading deepl website.')
    web.get('https://www.deepl.com/translator?il=en#ja/en/')
    time.sleep(10)
    try:
        cookieBtn = web.find_element_by_class_name(
            'dl_cookieBanner--buttonClose')
        cookieBtn.click()
    except selenium.common.exceptions.NoSuchElementException:
        pass
    return web


def process_text(text):
    inputarea = web.find_element_by_class_name('lmt__source_textarea')
    outputarea = web.find_element_by_id('target-dummydiv')

    inputarea.clear()
    inputarea.send_keys(text)
    time.sleep(MIN_DELAY_SEC)
    for i in range(MAX_DELAY_SEC - MIN_DELAY_SEC):
        time.sleep(1)
        translated = outputarea.get_attribute('innerHTML')
        if translated.count('[...]') > 1:
            continue
        if translated and outputarea.is_enabled() and inputarea.is_enabled():
            break
    return translated


def translate(input_file, output_file, paid=False):
    with open(input_file, 'r') as r:
        filecontent = r.read()
    if paid:
        LIMIT = 5000
    else:
        LIMIT = 3800
    lines = filecontent.splitlines()
    content = ''
    tl_doc = ''
    print(f'TRANSLATION: {len(lines)} lines file.')
    with open(log_file, 'a') as lf:
        lf.write(f'TRANSLATION: {len(lines)} lines file.\n')
    for i, line in enumerate(lines, start=1):
        if len(content) > LIMIT:
            tl_doc += process_text(content) + '\n'
            print(f'{i} lines completed...')
            content = ''
        else:
            content += line + '\n'

    tl_doc += process_text(content)
    tl_doc = re.sub(r'\n+ *', '\n\n', tl_doc)
    with open(output_file, 'w') as w:
        w.write(tl_doc)
    print(f'Written to {output_file}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input file> <output file>")
        sys.exit(0)
    init_web()
    translate(sys.argv[1], sys.argv[2])
    close_web()
