# word.camera image-to-text translator
# Copyright  (C) 2015  Ross Goodwin
#  
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  
# You can contact Ross Goodwin at ross.goodwin@gmail.com or address
# physical correspondence to:
#  
# Ross Goodwin c/o ITP
# 721 Broadway
# 4th Floor
# New York, NY 10003

from py.client import ClarifaiApi
import random
from random import choice as rc
from random import sample as rs
from random import randint as ri
#import en
import requests
import collections
from collections import defaultdict
import string
from string import Template
from conceptnet5.language.english import normalize
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort
from werkzeug import secure_filename
import os
import os.path
import subprocess
import PIL
from PIL import Image
import uuid
from base64 import decodestring
from flask.ext.mobility import Mobility
from flask.ext.mobility.decorators import mobilized
from pattern.en import referenced as a_or_an
from pattern.en import parsetree, UNIVERSAL, conjugate
import time
import hashids
from salty import saline
import exifread
import urlparse
from bs4 import BeautifulSoup
# from signal import signal, SIGPIPE, SIG_DFL

app = Flask(__name__)
Mobility(app)

app.config['UPLOAD_FOLDER'] = '/var/www/PhotoSyn/PhotoSyn/static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

SYSPATH = '/var/www/PhotoSyn/PhotoSyn/static/img/'
AUDPATH = '/var/www/PhotoSyn/PhotoSyn/static/aud/'
APPPATH = '/var/www/PhotoSyn/PhotoSyn/'
BASEURL = 'http://word.camera'

MAX_GRAF_DENSITY = 6

api = ClarifaiApi() # Assumes environmental variables have been set

# signal(SIGPIPE,SIG_DFL) # Hope this works

@app.route("/")
def index():
    if request.MOBILE:
        return render_template("mobile.html")
    else:
        return render_template("index.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('fourohfour.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('fivehundred.html'), 500

@app.route("/sitemap")
def sitemap():
    return send_from_directory(APPPATH+'static/assets', 'sitemap.xml')

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/albums")
def albums():
    return render_template("albums.html")


@app.route("/abm")
def abm():
    params = urlparse.parse_qs(request.query_string)
    if 'l' in params:
        hashes = [url.split('/')[-1] for url in params['l']]
    else:
        abort(404)
    if 't' in params:
        title = params['t'][0]
    else:
        title = "Untitled Lexograph Album"
    if 'a' in params:
        author = params['a'][0]
    else:
        author = "anonymous"
    abmInput = [(h, chTitle(h)) for h in hashes]
    tocHtml = render_template("toc.html", albumInput=abmInput, title=title, author=author)

    slug = url_hash()
    tocFilePath = APPPATH+'static/tocs/'+slug+'.html'

    with open(tocFilePath, 'w') as outfile:
        outfile.write(tocHtml)

    proc = subprocess.Popen([
        "ebook-convert",
        tocFilePath,
        APPPATH+"static/epub/"+slug+".epub",
        "--sr1-search=/static/img/",
        "--sr1-replace="+APPPATH+"/static/img/",
        "--sr2-search=#F2F1EF",
        "--sr2-replace=#FFFFFF",
        "--sr3-search=Tweet",
        "--sr3-replace=",
        "--cover="+APPPATH+"/static/assets/album_cover.jpg",
        "--title="+title,
        "--authors="+author,
        "--publisher=word.camera"
        ])

    proc.communicate()

    return redirect(BASEURL+"/a/"+slug)

@app.route("/a/<slug>")
def album(slug):
    if os.path.isfile(APPPATH+"static/epub/"+slug+".epub"):
        tocFile = open(APPPATH+"static/tocs/"+slug+".html")
        tocText = tocFile.read()
        soup = BeautifulSoup(tocText)
        try:
            title = soup.find(id="title").string
            byline = soup.find(id="byline").string
        except:
            title = "Untitled Lexograph Album"
            byline = "by anonymous"
        return render_template("a.html", s=slug, t=title, b=byline)
    else:
        abort(404)


@app.route("/i/<slug>")
def userpage(slug):
    return send_from_directory(APPPATH+'static/output', slug+'.html')

@app.route("/img", methods=["GET", "POST"])
def img():
    if request.method == 'POST':
        newFilename = ""

        try:
            dtopUpload = request.form['IfYouScriptThisForm'] == 'GnomesWillEatYourLungs'
        except:
            dtopUpload = False
        if request.MOBILE or dtopUpload:
            f = request.files['file']
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Resize image and generate unique filename
                newFilename = resizeImage(filename)
        else:
            f = False
            fstring = request.form['base64img']
            newFilename = str(uuid.uuid4())+'.jpeg'
            fh = open(SYSPATH+newFilename, "wb")
            fh.write(fstring.decode('base64'))
            fh.close()

        if newFilename:
            # Generate Text
            photoText = main([newFilename])
            # with open(APPPATH+"output/"+newFilename+".txt", "w") as outfile:
            #     outfile.write(photoText)
            photoText = photoText.replace("\n", "<br />")

            # oggName = filename.split(".")[0]+".ogg"
            # mp3Name = filename.split(".")[0]+".mp3"
            # proc = subprocess.Popen(["say", "-o", AUDPATH+oggName], stdin=subprocess.PIPE)
            # proc.communicate(photoText)

            # proc2 = subprocess.Popen(["ffmpeg", "-i", AUDPATH+oggName, "-acodec", "libmp3lame", AUDPATH+mp3Name])
            # proc2.communicate()

            imgPath = "/static/img/"+newFilename
            # audioPath = "/static/aud/"+mp3Name
            # return render_template("result.html", imgUrl=imgPath, imgText=photoText)

            # NEW PART
            html = render_template("result.html", imgUrl=imgPath, imgText=photoText)
            slug = url_hash()
            with open(APPPATH+"static/output/"+slug+".html", "w") as outfile:
                outfile.write(html)

            return redirect(BASEURL+"/i/"+slug)
        else:
            abort(500)
    else:
        abort(404)


def chTitle(hi):
    htmlFile = open(APPPATH+'static/output/'+hi+'.html', 'r')
    html = htmlFile.read()
    htmlFile.close()
    soup = BeautifulSoup(html)
    text = "\n".join([unicode(i) for i in soup.p.contents]).replace("<br/>", "\n")
    s = parsetree(text)
    nounPhrases = []
    for sentence in s:
        for chunk in sentence.chunks:
            if chunk.type == "NP":
                nounPhrases.append(chunk.string)
    selectNPs = rs([np for np in nounPhrases if not "&" in np], ri(1,2))

    articles = ["a", "an", "the"]

    nps = []

    for np in selectNPs:
        if startsWithCheck(np, articles):
            nps.append(np)
        else:
            nps.append(a_or_an(np))

    if len(selectNPs) == 1:
        title = titlecase(nps[0])
    elif len(selectNPs) == 2:
        title = titlecase(" and ".join(nps))
    # elif len(selectNPs) == 3:
    #     title = titlecase("%s, %s, and %s" % tuple(nps))

    return title.encode('ascii', 'xmlcharrefreplace')


def titlecase(s):
    words = s.split()
    capwords = [string.capitalize(w) for w in words]
    return " ".join(capwords)


def url_hash():
    millis = int(round(time.time() * 1000))
    hi = hashids.Hashids(salt=salty.saline)
    return hi.encode(millis)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def resizeImage(fn):
    longedge = 1000
    orientDict = {
        1: (0, 1),
        2: (0, PIL.Image.FLIP_LEFT_RIGHT),
        3: (-180, 1),
        4: (0, PIL.Image.FLIP_TOP_BOTTOM),
        5: (-90, PIL.Image.FLIP_LEFT_RIGHT),
        6: (-90, 1),
        7: (90, PIL.Image.FLIP_LEFT_RIGHT),
        8: (90, 1)
    }

    imgOriList = []
    try:
        f = open(SYSPATH+fn, "rb")
        exifTags = exifread.process_file(f, details=False, stop_tag='Image Orientation')
        if 'Image Orientation' in exifTags:
            imgOriList.extend(exifTags['Image Orientation'].values)
    except:
        pass

    img = Image.open(SYSPATH+fn)
    w, h = img.size
    newName = str(uuid.uuid4())+'.jpeg'
    if w >= h:
        wpercent = (longedge/float(w))
        hsize = int((float(h)*float(wpercent)))
        img = img.resize((longedge,hsize), PIL.Image.ANTIALIAS)
    else:
        hpercent = (longedge/float(h))
        wsize = int((float(w)*float(hpercent)))
        img = img.resize((wsize,longedge), PIL.Image.ANTIALIAS)

    for val in imgOriList:
        if val in orientDict:
            deg, flip = orientDict[val]
            img = img.rotate(deg)
            if flip != 1:
                img = img.transpose(flip)

    img.save(SYSPATH+newName, format='JPEG')
    os.remove(SYSPATH+fn)
    
    return newName

def extractTags(filenames):
    imgFiles = [open(SYSPATH+fn) for fn in filenames]
    data = api.tag_images(imgFiles)

    for f in imgFiles:
        f.close()

    tags_probs = []
    for r in data['results']:
        try:
            obj = r['result']['tag']
            tags_probs.extend(zip(obj['classes'], obj['probs']))
        except KeyError:
            pass

    return sorted(tags_probs, key=lambda x: x[1])

# def a_or_an(word):
#     #return en.noun.article(word)
#     if word[0].lower() in ['a', 'e', 'i', 'o', 'u']:
#         return "an" + " " + word
#     else:
#         return "a" + " " + word

def uniqify(seq, idfun=None): 
    if idfun is None:
       def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
       marker = idfun(item)
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
    return result

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def conceptNet(start):
    endpt = "http://127.0.0.1:8084/data/5.3%s" % start
    payload = {
        "start": start,
        "limit": 999
    }
    r = requests.get(endpt, params=payload)
    try:
        return r.json()
    except ValueError:
        return {}

def startsWithCheck(toCheck, wordList):
    return any(toCheck.lower().startswith(word+" ") for word in wordList)

def verbConjugate(lemma, rel, aan):
    relAvoid = ["/r/CapableOf", "/r/PartOf", "/r/MemberOf"
                "/r/IsA", "/r/HasA", "/r/TranslationOf",
                "/r/HasProperty"]
    if not rel in relAvoid:
        s = parsetree(lemma, relations=True)
        try:
            vb = s[0].verbs[0].words[0].string
            result = lemma.replace(vb, conjugate(vb, "part"))
        except:
            result = lemma
        else:
            if vb in ["to", "can"]:
                result = lemma

        # if not aan:
        #     try:
        #         firstWord = s[0].chunks[0].words[0].string
        #         reconjugated = conjugate(firstWord, "part")
        #         result = lemma.replace(firstWord, reconjugated)
        #     except:
        #         result = lemma

    else:
        result = lemma
        
    return result

def explodeTag(tag):
    relDict = {
        "/r/RelatedTo": ["evokes", False],
        "/r/IsA": ["is", True],
        "/r/PartOf": ["appertains to", True],
        "/r/MemberOf": ["belongs to", True],
        "/r/HasA": ["has", True],
        "/r/UsedFor": ["is for", False],
        "/r/CapableOf": ["may", False],
        #"/r/AtLocation": [False, False],
        "/r/Causes": ["causes", True],
        "/r/HasSubevent": ["manifests", False],
        "/r/HasFirstSubevent": ["began with", True],
        "/r/HasLastSubevent": ["ends with", True],
        "/r/HasPrerequisite": ["requires", True],
        "/r/HasProperty": ["is", False],
        "/r/MotivatedByGoal": ["dreams of", False],
        "/r/ObstructedBy": ["struggles with", True],
        "/r/Desires": ["yearns for", False],
        "/r/CreatedBy": ["resulted from", True],
        "/r/Synonym": ["is also known as", True],
        "/r/Antonym": ["is not", True],
        "/r/DerivedFrom": ["is made from", True],
        "/r/TranslationOf": ["is known to some as", False],
        "/r/DefinedAs": ["remains", True]
    }
    articleList = ["a", "an", "the"]
            
    candidates = defaultdict(list)

    normalizedTag = normalize(tag)
    start = "/c/en/"+normalizedTag

    try:
        edges = conceptNet(start)["edges"]
    except KeyError:
        edges = []

    for edge in edges:
        endLemma = edge["end"].split("/")[-1].replace("_", " ")
        rel = edge["rel"]
        try:
            verb, aan = relDict[rel]
        except KeyError:
            verb = False
        else:
            unmodified = endLemma
            endLemma = verbConjugate(unmodified, rel, aan)

        if verb and len(endLemma) > 1 and not unmodified in [tag, normalizedTag]:
            if aan and not startsWithCheck(endLemma, articleList):
                candidates[verb].append(a_or_an(endLemma))
            else:
                candidates[verb].append(endLemma)

    return candidates




def open_template(x):
    f = open(APPPATH+"tem/template_%s.txt" % str(x), 'r') # THERE IS A REASON FOR NOT USING %i
    text = f.read()
    templ = Template(text)
    f.close()
    return templ


def replacementDict(tc, dc, cc, tr):
    MAX_PREDICATES = 3
    repl = {}
    for i in range(len(tc)):
        repl["tag_%i"%i] = tc[i]
        repl["tag_%i_aan"%i] = a_or_an(tc[i])

        if dc[i]:
            if len(dc[i].keys()) < MAX_PREDICATES:
                relVerbs = dc[i].keys()
                lemmas = [rc(dc[i][relVerb]) for relVerb in relVerbs]
                for j in range(MAX_PREDICATES - len(relVerbs)):
                    useAgain = rc(dc[i].keys())
                    relVerbs.append(useAgain)
                    lemmas.append(rc(dc[i][useAgain]))
            else:
                relVerbs = rs(dc[i].keys(), MAX_PREDICATES)
                lemmas = [rc(dc[i][relVerb]) for relVerb in relVerbs]

            zipped = zip(relVerbs, lemmas)
            for j in range(MAX_PREDICATES):
                repl["tag_%i_predicate_%i"%(i,j)] = " ".join(zipped[j])

            dump = []
            for rv in dc[i].keys():
                for lemma in dc[i][rv]:
                    dump.append("%s it %s %s." % (rc(tr), rv, lemma))
            random.shuffle(dump)
            repl["tag_%i_dump"%i] = dump
        else:
            for j in range(MAX_PREDICATES):
                repl["tag_%i_predicate_%i"%(i,j)] = "remains unknown"
            repl["tag_%i_dump"%i] = []

    return repl


def grafBuilder(exploDictsConf):
    MAX_TRANSITIONS = 7

    tags, exploDicts, confs = zip(*exploDictsConf)

    confMean = float(sum(confs))/len(confs)

    grafs = []

    templates = [open_template(n) for n in range(1,7)]

    transFile = open(APPPATH+'lists/transitions.txt', 'r')
    transitions = [l.strip() for l in transFile.readlines()]
    transFile.close()

    i = 0
    for tagsChunk in chunks(tags, MAX_GRAF_DENSITY):
        dictsChunk = exploDicts[i:i+len(tagsChunk)]
        confsChunk = confs[i:i+len(tagsChunk)]

        replDict = replacementDict(tagsChunk, dictsChunk, confsChunk, transitions)

        transes = rs(transitions, MAX_TRANSITIONS)
        for j in range(MAX_TRANSITIONS):
            replDict["transition_%i"%j] = transes[j]

        for j in range(len(tagsChunk)):
            for k in range(2,5,2):
                if len(replDict["tag_%i_dump"%j]) > k:
                    replDict["tag_%i_dump%i"%(j,k)] = " ".join(rs(replDict["tag_%i_dump"%j], k+1))
                else:
                    replDict["tag_%i_dump%i"%(j,k)] = ""

        templNo = len(tagsChunk)
        grafs.append(templates[templNo-1].substitute(**replDict))

        i+=len(tagsChunk)

    return grafs


def main(filenames):
    raw = extractTags(filenames)
    concepts = uniqify(raw, idfun=lambda x: x[0]) # ascending order of confidence
    exploDicts = [(tag, explodeTag(tag), conf) for tag, conf in concepts] # LIST OF DICTS
    grafs = "\n\n".join(grafBuilder(exploDicts)).encode('ascii', 'xmlcharrefreplace')
    return grafs


if __name__ == '__main__':
    app.run()

# for i in range(6):
#     print main([i])+"\n"


# def sceneDesc(numList):
#     # Multiple images will result in one scene.
#     # If multiple scenes desired, separate images into groups
#     # for each scene & run through sceneDesc independently
#     raw = extractTags(numList)
#     concepts = uniqify(raw, idfun=lambda x: x[0]) # ascending order of confidence
#     paragraphs = []

#     conf = [y for x, y in concepts]

#     if conf:
#         confMean = float(sum(conf))/len(conf)
#         i = 0
#         for tag in concepts[::-1]:
#             if conf[i] > confMean:
#                 itIs = "It is %s." % a_or_an(tag)
#             else:
#                 itIs = "Is it %s?" % a_or_an(tag)
#             paragraphs.append(itIs + " " + explodeTag(tag))

#             i += 1

#         return paragraphs

#     else:
#         return ""


# for i in range(1,34):
#     printable = u"\n\n\n".join(sceneDesc([i])).encode('utf-8')
#     outfile = open("%i-final.txt" % i, 'w')
#     outfile.write(printable)
#     outfile.close()

# print printable