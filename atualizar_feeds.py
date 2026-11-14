import os
import re
import json
import html
import urllib.request
import urllib.error
import ssl
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

CATEGORIAS = {
    "enter": [
        {"name": "Variety", "url": "https://variety.com/feed/"},
        {"name": "BuzzFeed - TV and Movies", "url": "https://www.buzzfeed.com/tvandmovies.xml"},
        {"name": "ABC News - Entertainment", "url": "https://feeds.abcnews.com/abcnews/entertainmentheadlines"},
        {"name": "Deadline", "url": "https://deadline.com/feed/"},
        {"name": "NBC News - Entertainment", "url": "https://feeds.nbcnews.com/feeds/todayentertainment"},
        {"name": "Esquire - Culture", "url": "https://www.esquire.com/blogs/culture/culture-rss"},
        {"name": "polygon", "url": "https://www.polygon.com/feed/"},
        {"name": "etonline", "url": "https://www.etonline.com/news/rss"},
        {"name": "collider", "url": "https://collider.com/feed/"},
        {"name": "usmagazine", "url": "https://www.usmagazine.com/feed/"},
        {"name": "wonderwall", "url": "https://www.wonderwall.com/feed/"},
        {"name": "hollywoodlife", "url": "https://hollywoodlife.com/feed/"},
        {"name": "screenhub", "url": "https://screenhub.blog/feed/"},
    ],
    "finance": [
        {"name": "Dow Jones", "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
        {"name": "New York Times - Business", "url": "http://rss.nytimes.com/services/xml/rss/nyt/Business.xml"},
        {"name": "The Economist", "url": "http://www.economist.com/feeds/print-sections/77/business.xml"},
        {"name": "Business Standard", "url": "http://www.business-standard.com/rss/latest.rss"},
        {"name": "Huffington Post - Business News", "url": "http://www.huffingtonpost.com/feeds/verticals/business/news.xml"},
    ],
    "games": [
        {"name": "Kotaku RSS Feed", "url": "https://kotaku.com/rss"},
        {"name": "VG247 RSS Feed", "url": "https://www.vg247.com/feed"},
        {"name": "GameSpot RSS Feed", "url": "https://www.gamespot.com/feeds/mashup"},
        {"name": "Polygon RSS Feed", "url": "https://www.polygon.com/rss/index.xml"},
        {"name": "PC Gamer RSS Feed", "url": "https://www.pcgamer.com/rss/"},
        {"name": "Gamers Heroes RSS Feed", "url": "https://www.gamersheroes.com/feed/"},
        {"name": "IGN RSS Feed", "url": "https://www.ign.com/"},
        {"name": "GameHaunt RSS Feed", "url": "https://gamehaunt.com/feed/"},
        {"name": "Indie DB RSS Feed", "url": "https://rss.indiedb.com/headlines/feed/rss.xml"},
        {"name": "Kabalyero RSS Feed", "url": "https://www.kabalyero.info/feeds/posts/default?alt=rss"},
        {"name": "Game Developer RSS Feed", "url": "https://www.gamedeveloper.com/rss.xml"},
        {"name": "Shacknews RSS Feed", "url": "https://www.shacknews.com/feed/rss"},
        {"name": "Gaming Debugged RSS Feed", "url": "https://www.gamingdebugged.com/feed/"},
        {"name": "Siliconera RSS Feed", "url": "https://www.siliconera.com/feed/"},
        {"name": "Push Square RSS Feed", "url": "https://www.pushsquare.com/feeds/latest"},
        {"name": "MP3s and NPCs RSS Feed", "url": "https://mp3sandnpcs.com/home?format=rss"},
        {"name": "VideoGamer.com RSS Feed", "url": "https://www.videogamer.com/feed/"},
        {"name": "The Tech Game RSS Feed", "url": "https://www.thetechgame.com/rss.php"},
        {"name": "Console Creatures RSS Feed", "url": "https://www.consolecreatures.com/feed/"},
        {"name": "Rock Paper Shotgun RSS Feed", "url": "https://www.rockpapershotgun.com/feed"},
        {"name": "Twinfinite RSS Feed", "url": "https://twinfinite.net/feed/"},
        {"name": "Last Word On Gaming RSS Feed", "url": "https://lastwordongaming.com/feed/"},
        {"name": "Finding God in Video Games RSS Feed", "url": "https://findinggodintheworldofvideogames.com/feed/"},
    ],
    "health": [
        {"name": "New York Times Health", "url": "http://www.nytimes.com/services/xml/rss/nyt/Health.xml"},
        {"name": "BBC Health News", "url": "http://feeds.bbci.co.uk/news/health/rss.xml?edition=us"},
        {"name": "ABC News - Health", "url": "http://feeds.abcnews.com/abcnews/healthheadlines"},
        {"name": "Chicago Tribune - Health", "url": "http://www.chicagotribune.com/lifestyles/health/rss2.0.xml"},
        {"name": "NY Daily News - Health", "url": "http://www.nydailynews.com/lifestyle/health/index_rss.xml"},
        {"name": "Men's Health", "url": "https://www.menshealth.com/rss/all.xml/"},
        {"name": "New Scientist - Health", "url": "http://feeds.newscientist.com/health"},
        {"name": "Time - Health", "url": "http://time.com/health/feed/"},
        {"name": "Mayo Clinic Health Information", "url": "http://www.mayoclinic.org/rss/all-health-information-topics"},
        {"name": "BuzzFeed News - Health", "url": "http://www.buzzfeed.com/health.xml"},
        {"name": "Lifehacker", "url": "http://vitals.lifehacker.com/rss"},
    ],
    "music": [
        {"url": "https://www.stereogum.com/feed/", "name": "Stereogum"},
        {"name": "EDM.com", "url": "https://edm.com/.rss/full"},
        {"name": "The Musical Hype", "url": "https://themusicalhype.com/feed"},
        {"name": "NME Magazine", "url": "https://nme.com/feed"},
        {"name": "BrooklynVegan", "url": "https://brooklynvegan.com/feed"},
        {"name": "Okayplayer", "url": "https://okayplayer.com/feeds/feed.rss"},
        {"name": "MTS Management News", "url": "https://mtsmanagementgroup.com/feed"},
        {"name": "Hip-Hop Wired", "url": "https://hiphopwired.com/feed"},
        {"name": "Chaospin", "url": "https://chaospin.com/feed"},
        {"name": "Dansende Beren", "url": "https://dansendeberen.be/feed"},
        {"name": "Dancing Astronaut", "url": "https://dancingastronaut.com/feed"},
        {"name": "Greeblehaus » Music", "url": "https://greeblehaus.com/category/mus.."},
        {"name": "The Groove Cartel", "url": "https://thegroovecartel.com/feed"},
        {"name": "Bong Mines Entertainment", "url": "https://bongminesentertainment.com/feed"},
        {"name": "Muzique Magazine", "url": "https://muziquemagazine.com/feed"},
        {"name": "I Care if You Listen", "url": "https://icareifyoulisten.com/feed"},
        {"name": "PLAYY. Magazine", "url": "https://theplayground.co.uk/feed"},
    ],
    "news": [
        {"name": "BBC News ", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "NBC News RSS Feed", "url": "https://feeds.nbcnews.com/nbcnews/public/news"},
        {"name": "CNBC ", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html"},
        {"name": "ABC News » International RSS Feed", "url": "https://abcnews.go.com/abcnews/internationalheadlines"},
        {"name": "Al Jazeera RSS Feed", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        {"name": "France 24 RSS Feed", "url": "https://www.france24.com/en/rss"},
        {"name": "BuzzFeed ", "url": "https://www.buzzfeed.com/in/world.xml"},
        {"name": "Global News ", "url": "https://globalnews.ca/world/feed/"},
        {"name": "National Public Radio (NPR) ", "url": "https://feeds.npr.org/1004/rss.xml"},
        {"name": "The Washington Times ", "url": "https://www.washingtontimes.com/rss/headlines/news/world"},
        {"name": "The Sydney Morning Herald ", "url": "https://www.smh.com.au/rss/world.xml"},
        {"name": "Sky News ", "url": "https://feeds.skynews.com/feeds/rss/world.xml"},
        {"name": "Los Angeles Times » World & Nation RSS Feed", "url": "https://www.latimes.com/world-nation/rss2.0.xml#nt=1col-7030col1"},
        {"name": "Times of India » World News RSS Feed", "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"},
        {"name": "Russia Today » World News RSS Feed", "url": "https://www.rt.com/rss/news/"},
        {"name": "The Sun » World News RSS Feed", "url": "https://www.thesun.co.uk/news/worldnews/feed/"},
        {"name": "Daily Mirror » World news RSS Feed", "url": "https://www.mirror.co.uk/news/world-news/?service=rss"},
        {"name": "Vox ", "url": "https://www.vox.com/rss/world-politics/index.xml"},
        {"name": "CBN RSS Feed", "url": "https://www1.cbn.com/app_feeds/rss/news/rss.php?section=world&mobile=false&q=cbnnews/world/feed"},
        {"name": "IFP News RSS Feed", "url": "https://ifpnews.com/feed/"},
        {"name": "The World Association of Newspapers - IFRA RSS Feed", "url": "https://wan-ifra.org/news/feed/"},
        {"name": "The Eastern Herald RSS Feed", "url": "https://easternherald.com/feed/"},
        {"name": "Global Press Journal RSS Feed", "url": "https://globalpressjournal.com/feed/"},
        {"name": "USNN World News RSS Feed", "url": "https://www.usnn.news/feed/"},
        {"name": "South China Morning Post RSS Feed", "url": "https://www.scmp.com/rss/91/feed/"},
        {"name": "The Independent ", "url": "http://www.independent.co.uk/news/world/rss"},
        {"name": "The Christian Science Monitor ", "url": "https://rss.csmonitor.com/feeds/world"},
        {"name": "BreakingNews ", "url": "https://feeds.breakingnews.ie/bnworld"},
        {"name": "DER SPIEGEL RSS Feed", "url": "https://www.spiegel.de/international/index.rss"},
        {"name": "Vox RSS Feed", "url": "https://www.vox.com/rss/index.xml"},
        {"name": "The Guardian ", "url": "https://www.theguardian.com/world/rss"},
        {"name": "UPI.com » World News RSS Feed", "url": "https://rss.upi.com/news/tn_int.rss"},
        {"name": "The Hindu BusinessLine » World News RSS Feed", "url": "https://www.thehindubusinessline.com/news/world/feeder/default.rss"},
        {"name": "RFI » International News RSS Feed", "url": "https://www.rfi.fr/en/international/rss"},
        {"name": "IPS News Agency » Global News RSS Feed", "url": "https://www.ipsnews.net/news/regional-categories/global/feed/"},
        {"name": "Washington Times » World News RSS Feed", "url": "https://www.washingtontimes.com/rss/headlines/news/world/"},
        {"name": "SBS News » World News RSS Feed", "url": "https://www.sbs.com.au/news/topic/world/feed"},
        {"name": "International - Actualités, vidéos et infos en direct RSS Feed", "url": "https://www.lemonde.fr/international/rss_full.xml"},
        {"name": "The Indian Express » World News RSS Feed", "url": "https://indianexpress.com/section/world/feed"},
        {"name": "The Hindu » World News RSS Feed", "url": "https://www.thehindu.com/news/international/feeder/default.rss"},
        {"name": "Financial Times ", "url": "https://www.ft.com/world?format=rss"},
        {"name": "The Globe and Mail ", "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/"},
        {"name": "Firstpost » World News RSS Feed", "url": "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml"},
        {"name": "ThePrint ", "url": "https://theprint.in/category/world/feed/"},
        {"name": "The Conversation » World News RSS Feed", "url": "https://theconversation.com/topics/world-news-156028/articles.atom"},
        {"name": "9News » World News RSS Feed", "url": "https://www.9news.com.au/world/rss"},
        {"name": "Alternet.org ", "url": "https://www.alternet.org/feeds/world.rss"},
        {"name": "Morocco World News » International News RSS Feed", "url": "https://www.moroccoworldnews.com/international/feed/"},
        {"name": "KPRC 2 Houston » World News RSS Feed", "url": "https://www.click2houston.com/arc/outboundfeeds/rss/category/news/world/?outputType=xml&size=10"},
        {"name": "The Week » World News RSS Feed", "url": "https://www.theweek.in/news/world.feeds.rss.xml"},
        {"name": "Scripps News » World News RSS Feed", "url": "https://www.scrippsnews.com/world.rss"},
        {"name": "KSHB 41 » World News RSS Feed", "url": "https://www.kshb.com/world-news.rss"},
        {"name": "The Worlds Times RSS Feed", "url": "https://www.theworldstimes.com/feed"},
        {"name": "Fox 4 Now WFTX » World News RSS Feed", "url": "https://www.fox4now.com/world-news.rss"},
        {"name": "CNBCTV 18 » World News RSS Feed", "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/world.xml"},
        {"name": "Hindustan Times", "url": "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml"},
        {"name": "Asia Times ", "url": "https://asiatimes.com/category/world/feed/"},
    ],
    "sports": [
        {"url": "https://api.foxsports.com/v2/content/optimized-rss?partnerKey=MB0Wehpmuj2lUhuRhQaafhBjAJqaPU244mlTDK1i&size=30", "name": "Fox Sports"},
        {"name": "BBC » Sport", "url": "https://feeds.bbci.co.uk/sport/rss.xml"},
        {"name": "New York Times Sports", "url": "http://rss.nytimes.com/services/xml/rss/nyt/Sports.xml"},
        {"name": "BuzzFeed Sports", "url": "http://www.buzzfeed.com/sports.xml"},
        {"name": "Fox News - Sports", "url": "http://feeds.foxnews.com/foxnews/sports"},
        {"name": "LA Times Sports", "url": "http://www.latimes.com/sports/rss2.0.xml"},
        {"name": "Deadspin", "url": "https://deadspin.com/rss"},
        {"name": "SportsLogos.Net News", "url": "https://news.sportslogos.net/feed"},
        {"name": "Sport360", "url": "https://sport360.com/feed"},
        {"name": "Defector", "url": "https://defector.com/feed"},
        {"name": "MLB Trade Rumors", "url": "https://mlbtraderumors.com/feed"},
        {"name": "The Big Lead", "url": "https://thebiglead.com/posts.rss"},
        {"name": "Sportsnet", "url": "https://sportsnet.ca/feed"},
        {"name": "Awful Announcing", "url": "https://awfulannouncing.com/feed"},
        {"name": "CBS Sports", "url": "https://www.cbssports.com/rss/headlines/"},
    ],
    "tech": [
        {"url": "https://www.tomshardware.com/feeds.xml", "name": "Toms Hardware"},
        {"url": "https://www.eetimes.com/feed/", "name": "EE|Times"},
        {"url": "https://hackaday.com/blog/feed/", "name": "HACKADAY"},
        {"url": "https://www.wired.com/feed/rss", "name": "Wired"},
        {"url": "https://www.techradar.com/feeds.xml", "name": "Tech Radar"},
        {"url": "https://www.vox.com/rss/technology/index.xml", "name": "Vox"},
        {"name": "engadget", "url": "https://www.engadget.com/rss.xml"},
        {"name": "theverge", "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "geekwire", "url": "https://www.geekwire.com/feed/"},
        {"name": "cnet", "url": "https://www.cnet.com/rss/all/"},
        {"name": "digitaltrends", "url": "https://www.digitaltrends.com/feed/"},
        {"name": "androidauthority", "url": "https://www.androidauthority.com/feed/"},
    ],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml;q=0.9,*/*;q=0.8",
}

SSL_CONTEXT = ssl._create_unverified_context()


def strip_tags(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text()


def extrair_imagem_do_content(html_content: str):
    if not html_content:
        return None
    decoded = html.unescape(html_content)
    soup = BeautifulSoup(decoded, "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img.get("src")
    return None


def parse_timestamp(pub_date: str) -> float:
    if not pub_date:
        return 0.0
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.timestamp()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def processar_feed(feed: dict) -> list:
    url = feed["url"]
    nome = feed["name"]
    noticias = []

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5, context=SSL_CONTEXT) as resp:
            status_code = resp.getcode()
            raw_data = resp.read()
            print(f"HTTP {status_code} - {url}")
            if not raw_data or status_code >= 400:
                print(f"Erro ao carregar {url}")
                return noticias
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} - {url}")
        print(f"Erro ao carregar {url}")
        return noticias
    except Exception:
        print(f"Erro ao carregar {url}")
        return noticias

    try:
        root = ET.fromstring(raw_data)
    except ET.ParseError:
        print(f"Erro ao carregar {url}")
        return noticias

    root_tag = local_name(root.tag)
    if root_tag == "rss" or root.find("channel") is not None:
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
    else:
        items = [elem for elem in root if local_name(elem.tag) == "entry"]

    for item in items:
        title = ""
        link = ""
        pub_date = ""
        content_encoded = ""
        content_tag = ""
        description = ""
        summary = ""
        thumbnail = None

        for child in item:
            tag = local_name(child.tag)
            ns = child.tag[1:].split("}", 1)[0] if child.tag.startswith("{") else ""
            text_val = (child.text or "").strip()

            if tag == "title" and not title:
                title = strip_tags(text_val)
            elif tag == "link" and not link:
                href = child.attrib.get("href")
                link = href if href else text_val
            elif tag in ("pubDate", "updated") and not pub_date:
                pub_date = text_val
            elif tag == "encoded" and "content" in ns:
                content_encoded = text_val
            elif tag == "content" and not ns:
                content_tag = text_val
            elif tag == "description":
                description = text_val
            elif tag == "summary":
                summary = text_val
            elif "search.yahoo.com/mrss" in ns or ns.endswith("/media"):
                if tag == "thumbnail" and not thumbnail:
                    thumbnail = child.attrib.get("url")
                elif tag == "content" and not thumbnail:
                    thumbnail = child.attrib.get("url")
            elif tag == "enclosure" and not thumbnail:
                thumbnail = child.attrib.get("url")

        content = content_encoded or content_tag or description or summary or ""

        if not thumbnail:
            thumbnail = extrair_imagem_do_content(content)

        noticias.append({
            "title": title,
            "link": link,
            "pubDate": pub_date,
            "content": content,
            "thumbnail": thumbnail,
            "fonte": nome,
        })

    return noticias


def atualizar_categoria(categoria: str, feeds: list, base_dir: str):
    print(f"\n=== Atualizando categoria: {categoria} ===")
    todas_noticias = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futuros = [executor.submit(processar_feed, feed) for feed in feeds]
        for futuro in as_completed(futuros):
            todas_noticias.extend(futuro.result())

    todas_noticias.sort(key=lambda x: parse_timestamp(x["pubDate"]), reverse=True)

    feed_dir = os.path.join(base_dir, "feed")
    os.makedirs(feed_dir, exist_ok=True)

    cache_file = os.path.join(feed_dir, f"{categoria}.json")
    temp_file = f"{cache_file}.tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(todas_noticias, f, indent=4, ensure_ascii=False)

    os.replace(temp_file, cache_file)
    print(f"Categoria '{categoria}' atualizada com sucesso! Total: {len(todas_noticias)} notícias.")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for categoria, feeds in CATEGORIAS.items():
        atualizar_categoria(categoria, feeds, base_dir)
    print("\nTodos os feeds foram atualizados com sucesso!")


if __name__ == "__main__":
    main()
