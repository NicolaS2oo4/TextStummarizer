from flask import Flask, render_template, request, send_file
from bs4 import BeautifulSoup
import string, os
from nltk.tokenize import word_tokenize, sent_tokenize
from heapq import nlargest
from langdetect import detect
from stop_words import get_stop_words
from urllib.request import Request, urlopen
from gtts import gTTS
from io import BytesIO

app = Flask(__name__, template_folder='templates')

@app.route("/", methods=["POST","GET"])
def index():
    global contenuto
    global riassunto
    contenuto = riassunto = ""
    if request.method == "POST":
        
        #estraggo il contenuto della pagina web
        req = Request(
            url = request.form['testo_link'], 
            headers = {'User-Agent': 'Mozilla/5.0'}
        )
        text = urlopen(req).read()
        
        #elimino tutti i tag e mantengo solo il contenuto dei tag <p>
        soup = BeautifulSoup(text, "html.parser")
        paragrafi = soup.find_all('p')       
        for p in paragrafi:  
            contenuto += p.text 

        #identifico la lingua e scarico le stopwords relative
        frasi = sent_tokenize(contenuto)
        
        try:
            stopWords = get_stop_words(detect(frasi[1]))
        except:
            return render_template("index.html", originale = contenuto, riassunto = "Lingua non disponibile" )
        
        #creo e riempio la tabella di frequenza
        parole = word_tokenize(contenuto)
        punteggiatura = string.punctuation + '\n'
        tabellaFrequenza = {}
        for p in parole:
            if p.lower() not in stopWords and p.lower() not in punteggiatura:
                if p not in tabellaFrequenza.keys():
                    tabellaFrequenza[p] = 1
                else:
                    tabellaFrequenza[p] += 1
        
        #assegno un peso ad ogni valore della tabella di frequenza        
        frequenzaMax = max(tabellaFrequenza.values())
        for parole in tabellaFrequenza.keys():
            tabellaFrequenza[parole] /= frequenzaMax
        
        #assegno il peso di ogni frase del testo
        frasi = sent_tokenize(contenuto)
        pesoFrasi = {}
        for f in frasi:
            parole = f.split(" ")
            for p in parole:        
                if p.lower() in tabellaFrequenza.keys():
                    if f not in pesoFrasi.keys():
                        pesoFrasi[f] = tabellaFrequenza[p.lower()]
                    else:
                        pesoFrasi[f] += tabellaFrequenza[p.lower()]
        
        #creo il riassunto finale
        
        lunghezza = int(len(frasi) * 0.3)
        riassunto = nlargest(lunghezza, pesoFrasi, key = pesoFrasi.get)
        riassuntoFinale = [parole for parole in riassunto]
        riassunto = ' '.join(riassuntoFinale)
        
        
        f = open('./file/riassunto.txt', 'w', encoding='utf-8')
        f.write(riassunto)
        f.close()

    return render_template("index.html", originale = contenuto, riassunto = riassunto)

@app.route('/download')
def download():
    path = r'C:\Users\Nicolas\Desktop\progetto\file\riassunto.txt'
    return send_file(path, as_attachment=True)
    