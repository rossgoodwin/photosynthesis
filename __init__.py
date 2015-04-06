from py.client import ClarifaiApi
import random
from random import choice as rc
from random import sample as rs
#import en
import requests
import collections
from collections import defaultdict
import string
from string import Template
from conceptnet5.language.english import normalize
from flask import Flask, render_template, request, redirect, url_for
from werkzeug import secure_filename
import os
import subprocess
import PIL
from PIL import Image
import uuid
# from signal import signal, SIGPIPE, SIG_DFL

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = '/var/www/PhotoSyn/PhotoSyn/static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

SYSPATH = '/var/www/PhotoSyn/PhotoSyn/static/img/'
AUDPATH = '/var/www/PhotoSyn/PhotoSyn/static/aud/'
APPPATH = '/var/www/PhotoSyn/PhotoSyn/'
#BASEURL = 'http://127.0.0.1:5000'

MAX_GRAF_DENSITY = 6

api = ClarifaiApi() # Assumes environmental variables have been set

# signal(SIGPIPE,SIG_DFL) # Hope this works

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/img", methods=["GET", "POST"])
def img():
    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Resize image and generate unique filename
            newFilename = resizeImage(filename)

            # Generate Text
            photoText = main([newFilename])
            with open(APPPATH+"output/"+newFilename+".txt", "w") as outfile:
                outfile.write(photoText)
            photoText = photoText.replace("\n", "<br />")

            # oggName = filename.split(".")[0]+".ogg"
            # mp3Name = filename.split(".")[0]+".mp3"
            # proc = subprocess.Popen(["say", "-o", AUDPATH+oggName], stdin=subprocess.PIPE)
            # proc.communicate(photoText)

            # proc2 = subprocess.Popen(["ffmpeg", "-i", AUDPATH+oggName, "-acodec", "libmp3lame", AUDPATH+mp3Name])
            # proc2.communicate()

            imgPath = "/static/img/"+newFilename
            # audioPath = "/static/aud/"+mp3Name
            return render_template("result.html", imgUrl=imgPath, imgText=photoText)
    else:
        return "You didn't say the magic word."

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def resizeImage(fn):
    longedge = 1000
    img = Image.open(SYSPATH+fn)
    w, h = img.size
    newName = str(uuid.uuid4())+'.jpeg'
    if w >= h:
        wpercent = (longedge/float(w))
        hsize = int((float(h)*float(wpercent)))
        img = img.resize((longedge,hsize), PIL.Image.ANTIALIAS)
        img.save(SYSPATH+newName, format='JPEG')
    else:
        hpercent = (longedge/float(h))
        wsize = int((float(w)*float(hpercent)))
        img = img.resize((wsize,longedge), PIL.Image.ANTIALIAS)
        img.save(SYSPATH+newName, format='JPEG')
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

def a_or_an(word):
    #return en.noun.article(word)
    if word[0].lower() in ['a', 'e', 'i', 'o', 'u']:
        return "an" + " " + word
    else:
        return "a" + " " + word

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
    return any(toCheck.startswith(word+" ") for word in wordList)

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
        "/r/MotivatedByGoal": ["yearns for", False],
        "/r/ObstructedBy": ["struggles with", True],
        "/r/Desires": ["wants", False],
        "/r/CreatedBy": ["resulted from", True],
        "/r/Synonym": ["is also known as", True],
        "/r/Antonym": ["is not", True],
        "/r/DerivedFrom": ["was made from", True],
        "/r/TranslationOf": ["known to some as", False],
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
        if verb and len(endLemma) > 1 and not endLemma in [tag, normalizedTag]:
            if aan and not startsWithCheck(endLemma, articleList):
                candidates[verb].append(a_or_an(endLemma))
            else:
                candidates[verb].append(endLemma)

    return candidates




def open_template(x):
    f = open(APPPATH+"tem/template_%s.txt" % str(x), 'r')
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