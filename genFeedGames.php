<?php

$feeds = [
    [
        'name' => 'Kotaku RSS Feed',
        'url' => 'https://kotaku.com/rss'
    ],
    [
        'name' => 'VG247 RSS Feed',
        'url' => 'https://www.vg247.com/feed'
    ],
    [
        'name' => 'GameSpot RSS Feed',
        'url' => 'https://www.gamespot.com/feeds/mashup'
    ],
    [
        'name' => 'Polygon RSS Feed',
        'url' => 'https://www.polygon.com/rss/index.xml'
    ],
    [
        'name' => 'PC Gamer RSS Feed',
        'url' => 'https://www.pcgamer.com/rss/'
    ],
    [
        'name' => 'Gamers Heroes RSS Feed',
        'url' => 'https://www.gamersheroes.com/feed/'
    ],
    [
        'name' => 'IGN RSS Feed',
        'url' => 'https://www.ign.com/'
    ],
    [
        'name' => 'GameHaunt RSS Feed',
        'url' => 'https://gamehaunt.com/feed/'
    ],
    [
        'name' => 'Indie DB RSS Feed',
        'url' => 'https://rss.indiedb.com/headlines/feed/rss.xml'
    ],
    [
        'name' => 'Kabalyero RSS Feed',
        'url' => 'https://www.kabalyero.info/feeds/posts/default?alt=rss'
    ],
    [
        'name' => 'Game Developer RSS Feed',
        'url' => 'https://www.gamedeveloper.com/rss.xml'
    ],
    [
        'name' => 'Shacknews RSS Feed',
        'url' => 'https://www.shacknews.com/feed/rss'
    ],
    [
        'name' => 'Gaming Debugged RSS Feed',
        'url' => 'https://www.gamingdebugged.com/feed/'
    ],
    [
        'name' => 'Siliconera RSS Feed',
        'url' => 'https://www.siliconera.com/feed/'
    ],
    [
        'name' => 'Push Square RSS Feed',
        'url' => 'https://www.pushsquare.com/feeds/latest'
    ],
    [
        'name' => 'MP3s and NPCs RSS Feed',
        'url' => 'https://mp3sandnpcs.com/home?format=rss'
    ],
    [
        'name' => 'VideoGamer.com RSS Feed',
        'url' => 'https://www.videogamer.com/feed/'
    ],
    [
        'name' => 'The Tech Game RSS Feed',
        'url' => 'https://www.thetechgame.com/rss.php'
    ],
    [
        'name' => 'Console Creatures RSS Feed',
        'url' => 'https://www.consolecreatures.com/feed/'
    ],
    [
        'name' => 'Rock Paper Shotgun RSS Feed',
        'url' => 'https://www.rockpapershotgun.com/feed'
    ],
    [
        'name' => 'Twinfinite RSS Feed',
        'url' => 'https://twinfinite.net/feed/'
    ],
    [
        'name' => 'Last Word On Gaming RSS Feed',
        'url' => 'https://lastwordongaming.com/feed/'
    ],
    [
        'name' => 'Finding God in Video Games RSS Feed',
        'url' => 'https://findinggodintheworldofvideogames.com/feed/'
    ],
];

$todasNoticias = [];

foreach ($feeds as $feed) {
    libxml_use_internal_errors(true);

    $ch = curl_init($feed['url']);

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_ENCODING => '',  // importante para gzip
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        CURLOPT_HTTPHEADER => [
            'Accept: application/rss+xml, application/xml;q=0.9,*/*;q=0.8'
        ]
    ]);

    $response = curl_exec($ch);

    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    echo "HTTP {$httpCode} - {$feed['url']}\n";

    if (!$response || $httpCode >= 400) {
        echo "Erro ao carregar {$feed['url']}\n";
        continue;
    }

    $xml = simplexml_load_string($response);

    if (!$xml) {
        echo "Erro ao carregar {$feed['url']}\n";
        continue;
    }

    // Detecta se é RSS ou Atom
    $items = [];

    if (isset($xml->channel)) {
        // RSS
        $items = $xml->channel->item;
    } else {
        // Atom
        $items = $xml->entry;
    }

    foreach ($items as $item) {
        $namespaces = $item->getNamespaces(true);

        // ===== Título =====
        $title = strip_tags((string) ($item->title ?? ''));

        // ===== Link =====
        if ($item->link->attributes()->href) {
            // Atom
            $link = (string) $item->link->attributes()->href;
        } else {
            // RSS
            $link = (string) $item->link;
        }

        // ===== Data =====
        $pubDate = (string) ($item->pubDate ?? $item->updated ?? '');

        // ===== Conteúdo =====
        $content = '';

        $contentNs = $item->children('content', true);
        if (isset($contentNs->encoded)) {
            $content = (string) $contentNs->encoded;
        } elseif ($item->content) {
            $content = (string) $item->content;
        } elseif ($item->description) {
            $content = (string) $item->description;
        } elseif ($item->summary) {
            $content = (string) $item->summary;
        }

        // ===== Thumbnail =====
        $thumbnail = null;

        // MRSS
        if (isset($namespaces['media'])) {
            $media = $item->children($namespaces['media']);
            if ($media->thumbnail) {
                $thumbnail = (string) $media->thumbnail->attributes()->url;
            } elseif ($media->content) {
                $thumbnail = (string) $media->content->attributes()->url;
            }
        }

        // Fallback: extrair do HTML
        if (!$thumbnail) {
            $thumbnail = extrairImagemDoContent($content);
        }

        $todasNoticias[] = [
            'title' => $title,
            'link' => $link,
            'pubDate' => $pubDate,
            'content' => $content,
            'thumbnail' => $thumbnail,
            'fonte' => $feed['name']
        ];
    }
}

// Ordenar por data
usort($todasNoticias, function ($a, $b) {
    return strtotime($b['pubDate']) - strtotime($a['pubDate']);
});

$path = __DIR__ . '/feed';  // ou o caminho relativo correto
if (!is_dir($path)) {
    mkdir($path, 0755, true);
}

$cacheFile = $path . '/games.json';
$tempFile = $cacheFile . '.tmp';

file_put_contents($tempFile, json_encode($todasNoticias, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
rename($tempFile, $cacheFile);

function extrairImagemDoContent($html)
{
    if (!$html) {
        return null;
    }

    $html = html_entity_decode($html);

    libxml_use_internal_errors(true);

    $dom = new DOMDocument();
    $dom->loadHTML($html);

    $imgs = $dom->getElementsByTagName('img');

    if ($imgs->length > 0) {
        return $imgs->item(0)->getAttribute('src');
    }

    return null;
}

echo 'Feeds atualizados com sucesso!';
echo __DIR__;
echo count($todasNoticias);
