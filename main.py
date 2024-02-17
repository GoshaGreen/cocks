import pickle
import os
import sys
import requests
from html.parser import HTMLParser
import asyncio
from pyppeteer import launch

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_PICKLE_PATH = os.path.join(SCRIPT_DIR, 'cocs_pi')
BASE_CARD_HTML_PATH = os.path.join(SCRIPT_DIR, 'cocs_html')
BASE_CARD_JPG_PATH = os.path.join(SCRIPT_DIR, 'cocs_card')
DEL = ','
INGRS_FILE = os.path.join(SCRIPT_DIR, 'finder', 'data.js')

def getPhoto(link):
    res = b''
    try:
        pass
        res = requests.get(link).content
    except Exception as e:
        print(f'not loaded: {link}')
    return res

class GetPhoto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.photo = b''
        self.photolink = ''
    def getIt(self):
        return self.photolink, self.photo
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if 'class' == a[0] and 'common-image-frame' in a[1]:
                for a2 in attrs:
                    if a2[0] == 'lazy-bg':
                        self.photolink = a2[1]
                        self.photo = getPhoto(a2[1])
                if self.photolink != '': break
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        pass

class GetRecipe(HTMLParser):
    def __init__(self):
        super().__init__()
        self.recipe = []
        self.reciepenabled = False
    def getIt(self):
        return self.recipe
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if 'itemprop' == a[0] and 'recipeInstructions' in a[1]:
                self.reciepenabled = True
                break
    def handle_endtag(self, tag):
        if self.reciepenabled:
            if tag == 'ul':
                self.reciepenabled = False
    def handle_data(self, data):
        if self.reciepenabled:
            self.recipe.append(data)

class Ingridientos:
    def __init__(self):
        self.name = ''
        self.amount = 0
        self.unit = ''
        self.photoLink = ''
        self.photo = b''
    def __str__(self):
        return f'{self.name} - {self.amount} {self.unit} [{self.photoLink}]'
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return abs(hash(self.name)) % (10 ** 8)

class GetIngredients(HTMLParser):
    def __init__(self):
        super().__init__()
        ing = Ingridientos()
        self.ingridients = [ing]
        thx = Ingridientos()
        self.things = [thx]
        self.tablesEnable = False
        self.tableIngEn = False
        self.tableThxEn = False
        self.NameEnable = False
        self.AmountEnable = False
        self.UnitEnable = False

    def getIt(self):
        return self.ingridients[1:-1], self.things[1:-1]
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if 'class' == a[0] and 'ingredient-tables' in a[1]:
                self.tablesEnable = True
                break
            if self.tablesEnable and 'class' == a[0]:
                if 'name' in a[1]:
                    self.NameEnable = True
                elif 'amount' in a[1]:
                    self.AmountEnable = True
                elif 'unit' in a[1]:
                    self.UnitEnable = True

    def handle_endtag(self, tag):
        if self.tablesEnable:
            if tag == 'div':
                self.tablesEnable = False
                self.tableIngEn = False
                self.tableThxE = False
                self.NameEnable = False
                self.AmountEnable = False
                self.UnitEnable = False

                return
            if tag == 'td':
                self.NameEnable = False
                self.AmountEnable = False
                self.UnitEnable = False
                return
            if tag == 'tr':
                ing = Ingridientos()
                if self.tableIngEn:
                    self.ingridients.append(ing)
                elif self.tableThxEn:
                    self.things.append(ing)
                return
            if tag == 'table':
                self.tableIngEn = False
                self.tableThxE = False
                self.NameEnable = False
                self.AmountEnable = False
                self.UnitEnable = False

    def handle_data(self, data):
        if self.tablesEnable:
            if data == 'Необходимые ингредиенты':
                self.tableIngEn = True
                return
            elif data == 'Необходимые штучки':
                self.tableThxEn = True
                return

            if self.tableIngEn:
                s = self.ingridients 
            elif self.tableThxEn:
                s = self.things
            else:
                return

            if self.NameEnable:
                s[-1].name += data
                return
            if self.AmountEnable:
                s[-1].amount = int(data)
                return
            if self.UnitEnable:
                s[-1].unit += data
                return


class GetIngsPhotos(HTMLParser):
    def __init__(self, ings, tupe):
        super().__init__()
        self.ings = ings
        self.tupe = tupe
        self.prevsEn = False
        self.photoesEn = False
        self.idx = 0

    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if tag == 'ul' and 'class' == a[0] and self.tupe in a[1]:
                self.photoesEn = True
                break
            if self.photoesEn:
                if 'lazy-bg' == a[0]:
                    if self.idx >= len(self.ings):
                        print('error'*200)
                        return
                    self.ings[self.idx].photoLink = a[1]
                    self.ings[self.idx].photo = getPhoto(a[1])
                    self.idx += 1
    def handle_endtag(self, tag):
        if tag in ['ul']:
            self.photoesEn = False
    def handle_data(self, data):
        pass

class GetTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.tagsEn = False
        self.tagEn = False

    def getIt(self):
        return self.tags
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if 'class' == a[0] and 'tags' in a[1]:
                self.tagsEn = True
                break
            if self.tagsEn and 'class' == a[0] and 'tag' in a[1]:
                self.tagEn = True
                break
    def handle_endtag(self, tag):
        self.tagEn = False
        if tag == 'ul':
            self.tagsEn = False
    def handle_data(self, data):
        if self.tagEn:
            self.tags.append(data)

class GetName(HTMLParser):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.name_ru = ''
        self.nruEn = False
        self.nEn = False

    def getIt(self):
        return self.name, self.name_ru
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if 'class' == a[0] and 'common-name' in a[1]:
                self.nruEn = True
                break
            if 'class' == a[0] and 'name-en' in a[1]:
                self.nEn = True
                break
    def handle_endtag(self, tag):
        self.nruEn = False
        self.nEn = False
    def handle_data(self, data):
        if self.nruEn:
            self.name_ru = data
        elif self.nEn:
            self.name = data

class GetStoryLink(HTMLParser):
    def __init__(self):
        super().__init__()
        self.link = ''

    def getIt(self):
        return self.link
    def handle_starttag(self, tag, attrs):
        for a in attrs:
            if tag == 'a' and 'class' == a[0] and 'article' in a[1] and 'hot' in a[1]:
                for a2 in attrs:
                    if 'href' == a2[0]:
                        self.link = a2[1]
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        pass

class Cock:
    def __init__(self, link):
        self.id = int(link.split('/')[-1].split('-')[0])
        self.link = link
        self.name = '_'.join(link.split('/')[-1].split('-')[1:])
        self.name_ru = ''
        self.photo = b''
        self.photoLink = ''
        self.tags = []
        self.ingridients = []
        self.instruments = []
        self.recipe = []
        self.storyLink = ''
        self.story = []
        self.getHtml()

    def getHtml(self):
        self.html = ''
        try:
            self.html = requests.get(self.link).content.decode('utf-8', errors='replace')
            self.html = self.html.replace('="/','="https://ru.inshaker.com/')

            parser = GetName()
            parser.feed(self.html)
            self.name, self.name_ru = parser.getIt()

            parser = GetTags()
            parser.feed(self.html)
            self.tags = parser.getIt()

            parser = GetPhoto()
            parser.feed(self.html)
            self.photoLink, self.photo = parser.getIt()

            parser = GetRecipe()
            parser.feed(self.html)
            self.recipe = parser.getIt()

            parser = GetIngredients()
            parser.feed(self.html)
            self.ingridients, self.instruments = parser.getIt()
            parser = GetIngsPhotos(self.ingridients, 'ingredients')
            parser.feed(self.html)
            parser = GetIngsPhotos(self.instruments, 'tools')
            parser.feed(self.html)

            parser = GetStoryLink()
            parser.feed(self.html)
            self.storyLink = parser.getIt()

            print(
                self.id,
                self.name, 
                self.name_ru, 
                # self.tags,
                # self.storyLink,
                #   self.photo, 
                #   self.recipe, 
                # self.ingridients, 
                #   self.instruments
                )

        except Exception as e:
            print(e)

    def __str__(self):
        return f'{self.id} {self.name} ings:{len(self.ingridients)}'
    def __repr__(self):
        return self.__str__()

def dumpImgs(coc: Cock):
    with open(os.path.join(SCRIPT_DIR, 'cocs', f'{"_".join(coc.name.split())}.jpg'), 'wb') as fout:
        fout.write(coc.photo)
    for ing in coc.ingridients:
        with open(os.path.join(SCRIPT_DIR, 'cocs', f'{"_".join(coc.name.split())}__{ing.name}.jpg'), 'wb') as fout:
            fout.write(ing.photo)
    for ing in coc.instruments:
        with open(os.path.join(SCRIPT_DIR, 'cocs', f'{"_".join(coc.name.split())}__{ing.name}.jpg'), 'wb') as fout:
            fout.write(ing.photo)

def dumpCoc(coc: Cock):
    filenam = os.path.join(BASE_PICKLE_PATH, f'{coc.id}_{'_'.join(coc.name.split())}.pickle')
    filenam.replace('Léon', 'Leon')
    with open(filenam, 'wb') as fout:
        pickle.dump(coc, fout, protocol=pickle.HIGHEST_PROTOCOL)

def readCock(filePath) -> Cock:
    with open(filePath, 'rb') as fin:
        pick = pickle.load(fin)
        return pick
def readCockCi(id: int) -> Cock | None:
    picks_fn = [f for f in os.listdir(BASE_PICKLE_PATH) if os.path.isfile(os.path.join(BASE_PICKLE_PATH, f))]
    for pick_fn in picks_fn:
        if pick_fn.split('_')[0] == str(id) and not pick_fn.endswith('_.pickle'):
            filePath = os.path.join(BASE_PICKLE_PATH, pick_fn)
            print(filePath)
            return readCock(filePath)
    return None
def readCocks(n=None):
    cocs = []
    coc_files = [os.path.join(BASE_PICKLE_PATH, f) for f in os.listdir(BASE_PICKLE_PATH) if os.path.isfile(os.path.join(BASE_PICKLE_PATH, f))]
    if n != None:
        coc_files = coc_files[:n]
    for coc_file in coc_files:
        print(coc_file)
        coc = readCock(coc_file)
        cocs.append(coc)
    return cocs

def genCardHtml(coc: Cock):
    style = '''
body {
    height: 1350px;
    width: 900px;
    margin: 0;
}
.container {
    position: absolute;
    height: 100%;
    width: 100%;
    font-family: PT Sans, Arial, Tahoma, sans-serif;
}
.cocHeader {
    position: absolute;
    top: 0px;
    left:0px;
    height: 75px;
    width: 900px;
}

.cocHeader h1 {
    position: absolute;
    margin: 0;
    top: 10px;
    left: 15px;
}
.cocHeader h2 {
    position: absolute;
    left: 15px;
    top: 32px;
    font-size: 16px;
    color: gray;
}
.cocHeader h3 {
    position:absolute;
    top: 32px; 
    right: 15px;
    font-size: 16px;
    color: gray;
}

.cocImg {
    position: absolute;
    width: 900px;
    height: 600px;
    top: 75px;
}
.cocImg img {
    width: 900px;
    height: 600px;
    object-fit: cover;
}

.hdr {
    font-size: 28px;
    border-bottom: 3px solid gray;
    margin-bottom: 5px;
}

.cocRecipe {
    position: absolute;
    top: 675px;
    left: 0px;
    height: 675px;
    width: 450px;
    padding-left: 30px;
    padding-right: 30px;
    box-sizing: border-box;
    font-size: 22px;
    overflow: hidden;
}
.cocRecipe li {
    border-bottom: 1px solid lightgray;
    margin-top: 10px;
    padding-bottom: 10px;
}

.cocIngrs {
    position: absolute;
    top: 675px;
    left: 450px;
    height: 675px;
    width: 450px;
    padding-left: 30px;
    padding-right: 30px;
    box-sizing: border-box;
    font-size: 22px;
    overflow: hidden;
}
.cocIngrs .ingrsImgs {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
}
.cocIngrs .ingrsImgs img {
    width: 45px;
    height: 45px;
    margin-left: 5px;
    margin-top: 5px;
    border-radius: 5px;
}
.cocIngrs table {
    margin-top:10px;
    border-collapse: collapse;
    font-size: 22px;
}
.cocIngrs tr {
    border-bottom: 1px solid lightgray;
}
.cocIngrs .ingrName {
    width: 325px;
}
.cocIngrs .ingrAmount {
    padding-right: 5px;
    width: 25px;
    text-align:right;
}
.cocIngrs .ingrUnit {
    width: 25px;
}
.cocIngrs .instrName {
    width: 375px;
    box-sizing: border-box;
}
'''
    htmltxt =  f'''
<html><head><style>{style}</style></head><body><div class="container">
<div class="cocHeader">
    <h1>{coc.name_ru}</h1>
    <h2>{coc.name}</h2>
    <h3>{' / '.join(coc.tags)}</h3>
</div>
<div class="cocImg">
    <img src="../cocs/{'_'.join(coc.name.split())}.jpg">
</div>
<div class="cocRecipe">
    <p class="hdr">Рецепт <b>{coc.name_ru}</b></p>
    <ol>{''.join(['<li>'+ x +'</li>' for x in coc.recipe])}</ol>
</div>
<div class="cocIngrs">
    <p class="hdr">Ингридиенты</p>
    <div class="ingrsImgs">
        {''.join(['<img src="../cocs/'+ '_'.join(coc.name.split())+ '__' + x.name +'.jpg">' for x in coc.ingridients])}
    </div>
    <table>
    {''.join(['<tr>' + 
    '<td class="ingrName"> • ' + x.name + '</td>' +
    '<td class="ingrAmount">' + str(x.amount) + '</td>' +
    '<td class="ingrUnit">' + x.unit + '</td>' +
    '</tr>' for x in coc.ingridients
    ])}
    </table>
    <p class="hdr">Другое</p>
    <div class="ingrsImgs">
        {''.join(['<img src="../cocs/'+ '_'.join(coc.name.split())+ '__' + x.name +'.jpg">' for x in coc.instruments])}
    </div>
    <table>
    {''.join(['<tr>' + 
    '<td class="instrName"> • ' + x.name + '</td>' +
    '</tr>' for x in coc.instruments
    ])}
    </table>
</div>
</div></body></html>'''
    coc.name
    return htmltxt

def saveCard(coc: Cock):
    filenam = os.path.join(BASE_CARD_HTML_PATH, f'{coc.id}_{'_'.join(coc.name.split())}.html')
    html_txt = genCardHtml(coc)
    with open(filenam, 'w',encoding='utf-8') as f:
        f.write(html_txt)
    filenamCard = os.path.join(BASE_CARD_JPG_PATH, f'{coc.id}_{'_'.join(coc.name.split())}.jpg')

    async def mmn():
        browser = await launch()
        page = await browser.newPage()
        await page.goto(filenam)
        await page.screenshot({'path': filenamCard, 'fullPage': 'true'})
        await browser.close()

    asyncio.get_event_loop().run_until_complete(mmn())

def geco(urllis):
    try:
        coc = Cock(urllis)
        if coc.name_ru == '':
            return False
        dumpCoc(coc)
    except Exception as e:
        print(ci, e)
        return False
    return True

def geco2(ci):
    try:
        coc = readCockCi(ci)
        if coc.name_ru == '':
            raise
    except Exception as e:
        print(ci, e)
        urllis = f'https://ru.inshaker.com/cocktails/{ci}'
        geco(urllis)

from typing import Dict, List, Optional
def genJsData(cocs: List[Cock]):
    tools = set()
    ingrs = list()
    for coc in cocs:
        for t in coc.instruments:
            tool = Ingridientos()
            tool.name = t.name
            tool.photo = t.photo
            tools.add(tool)
        for i in coc.ingridients:
            ingr = Ingridientos()
            ingr.name = i.name
            ingr.photo = i.photo
            ingr.unit = i.unit
            ingr.amount = 1
            if ingr in ingrs:
                ingrs[ingrs.index(ingr)].amount += 1
                continue
            ingrs.append(ingr)
    # sort based on popularity
    ingrs.sort( key=lambda k: -k.amount)
    # [print(x.name, x.amount) for x in ingrs]
    coclist = list()
    for coc in cocs:
        coclist.append([
            coc.id,
            coc.name_ru,
            []
        ])
        for i in coc.ingridients:
            ingr = Ingridientos()
            ingr.name = i.name
            ingr.photo = i.photo
            ingr.unit = i.unit
            coclist[-1][2].append(ingrs.index(ingr))
    # [print(x) for x in coclist]
    stingos = ''
    stingos += 'const data = [' 
    stingos += ''.join(
        [f'[false,0,"{x.name.replace('\"', '\'')}","{x.amount}"],' for x in ingrs]
    )

    stingos += '];\n'

    stingos += 'const coctails = ['
    stingos += ''.join(
        [f'[{x[0]},"{x[1].replace('\"', '\'')}",{x[2]}],' for x in coclist]
    )
    stingos += '];\n'
    return stingos

COCS = [
    988, # espresso, # martini
    52, # otvertka
    1098, # aperol, # shprits
    57, # mohito
    55, # negroni
    887, # tommi, # di, # sauer
    39, # margarita
    368, # dzhin, # tonik
    22, # daykiri
    53, # old, # feshen
    15, # belyy, # russkiy
    58, # moskovskiy, # mul
    35, # long, # aylend, # ays, # ti
    19, # gimlet
    281, # vodka, # martini
    54, # nikerboker
    34, # kuznechik
    26, # irlandskiy, # kofe
    48, # rzhavyy, # gvozd
    164, # b, # 52
    29, # kosmopoliten
    31, # krovavaya, # meri
    17, # bellini
    18, # viski, # sauer
    1086, # penitsillin
    814, # seks, # na, # plyazhe
]
COCS = range(1, 1174)
# COCS = range(151, 200)
# COCS = [52, 58]
COCS = [257]

if __name__ == '__main__':
    for ci in COCS:
        geco2(ci)
    # exit()
    
    # import concurrent.futures

    # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    #     # future_to_url = {executor.submit(geco, urllis): urllis for urllis in [f'https://ru.inshaker.com/cocktails/{ci}' for ci in COCS]}
    #     future_to_url = {executor.submit(geco2, ci): ci for ci in COCS }
    #     for future in concurrent.futures.as_completed(future_to_url):
    #         url = future_to_url[future]
    #         if not url:
    #             print(url)
    # exit()

    cocs = list()
    cocs = readCocks()#[1:2] or readCocks(10)

    # for ci in COCS:
    #     coc = readCockCi(ci)
    #     cocs.append(coc)

    # generate data for js checker
    with open(INGRS_FILE, 'w', encoding='utf-8') as f:
        f.write(genJsData(cocs))

    # st = ''
    # st = 'CocName' + DEL + f'{DEL}'.join([f'{i.name}({i.unit})' for i in ingrs]) + '\n'
    # for coc in cocs:
    #     soso = [0] * len(ingrs)
    #     st += f'{coc.name_ru}'
    #     for ing in coc.ingridients:
    #         idx = ingrs.index(ing)
    #         soso[idx] += ing.amount

    #     for so in soso:
    #         st += f'{DEL}{so}'

    #     st += '\n'
    # print(st)

    # ingrList = [0] * len(ingrs)
    # for coc in cocs:
    #     for ing in coc.ingridients:
    #       

    # for coc in cocs:
    #     print('='*80, '\n', f'{coc.id} {coc.name}')
    #     dumpImgs(coc)
    #     saveCard(coc)

    # CHECK FOR BROCKEN DATA

