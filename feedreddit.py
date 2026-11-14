import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


def extrair_media(html_content: str) -> dict | None:
    if not html_content:
        return None

    # Vídeo Reddit
    match_video = re.search(
        r'<video.+?src="([^"]+)"', html_content, re.IGNORECASE
    )
    if match_video:
        return {
            "type": "video",
            "url": html.unescape(match_video.group(1)),
            "aspectClass": "aspect-video",
        }

    # Imagem
    match_img = re.search(r'<img.+?src="([^"]+)"', html_content, re.IGNORECASE)
    if match_img:
        return {"type": "image", "url": html.unescape(match_img.group(1))}

    # GIF
    match_gif = re.search(r"\.(gif)", html_content, re.IGNORECASE)
    if match_gif:
        return {"type": "image", "url": match_gif.group(0)}

    return None


def fetch_subreddit(sub: str) -> list | None:
    url = f"https://www.reddit.com/r/{sub}/.rss"
    req = urllib.request.Request(
        url, headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
}
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw_data = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Erro na requisição ({sub}): {e}")
        return None

    print(f"RSS carregado: {len(raw_data)} bytes")

    try:
        root = ET.fromstring(raw_data)
    except ET.ParseError:
        print(f"Erro lendo RSS {sub}")
        return None

    print("XML carregado")

    # Namespace padrão do feed Atom do Reddit
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    print(f"Entries encontradas: {len(entries)}")

    posts = []
    for entry in entries:
        title_el = entry.find("atom:title", ns)
        link_el = entry.find("atom:link", ns)
        content_el = entry.find("atom:content", ns)

        title = (
            title_el.text if (title_el is not None and title_el.text) else ""
        )
        link = link_el.attrib.get("href", "") if link_el is not None else ""
        content = (
            content_el.text
            if (content_el is not None and content_el.text)
            else ""
        )

        media = extrair_media(content)

        if not media:
            print("Sem mídia")
            continue

        post_id = hashlib.md5(link.encode("utf-8")).hexdigest()

        posts.append({
            "id": post_id,
            "title": title,
            "url": link,
            "ups": 0,
            "comments": 0,
            "type": media["type"],
            "media": media["url"],
            "aspectClass": media.get("aspectClass", "aspect-video"),
        })

    return posts


def main():
    categorias = {
        "Amazing": [
            "nextfuckinglevel",
            "BeAmazed",
            "interestingasfuck",
            "mildlyinteresting",
            "satisfying",
            "Satisfyingasfuck",
        ],
        "Happy": [
            "funny",
            "shitposting",
            "interesting",
            "MemeVideos",
            "funnyvideos",
            "memes",
            "meme",
            "dankmemes",
            "Damnthatsinteresting",
            "interestingasfuck",
            "mildlyinteresting",
        ],
        "IA": [
            "aivideo",
            "isthisAI",
            "aivids",
            "generativeAI",
            "aifails",
            "Aiimages",
            "singularity",
            "aiArt",
            "aivideos",
        ],
        "Memes": ["memes", "dankmemes", "okbuddyretard", "TikTokCringe"],
        "Nature": [
            "NatureIsFuckingLit",
            "natureporn",
            "AllAboutNature",
            "natureisterrible",
            "natureismetal",
            "natureisbeautiful",
        ],
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "feedReddit")
    os.makedirs(output_dir, exist_ok=True)

    # Evita buscar o mesmo subreddit duas vezes caso ele apareça em mais de uma categoria
    cache_requisicoes = {}

    for categoria, subs in categorias.items():
        print(f"\n==========================================")
        print(f"Iniciando categoria: {categoria}")
        print(f"==========================================")

        merged = []

        for sub in subs:
            print(f"\nSubreddit: {sub}")

            if sub in cache_requisicoes:
                print(f"Usando dados em cache da execução atual para r/{sub}")
                posts = cache_requisicoes[sub]
            else:
                posts = fetch_subreddit(sub)
                cache_requisicoes[sub] = posts

                # Pausa de 3 segundos para evitar bloqueio do Reddit (Rate Limit)
                print("Aguardando 50 segundos...")
                time.sleep(50)

            if not posts:
                continue

            merged.extend(posts)
            print(f"Sub {sub}: {len(posts)} posts")

        cache_file = os.path.join(output_dir, f"{categoria}.json")
        temp_file = f"{cache_file}.tmp"

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=4, ensure_ascii=False)

            os.replace(temp_file, cache_file)
            print(f"\n--> Total final ({categoria}): {len(merged)} posts salvos.")
        except Exception as e:
            print(f"Erro ao salvar JSON de {categoria}: {e}")


if __name__ == "__main__":
    main()