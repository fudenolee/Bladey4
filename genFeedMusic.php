<?php

$feeds = [
    [
        'url' => 'https://www.stereogum.com/feed/',
        'name' => 'Stereogum'
    ],
    [
        'name' => 'EDM.com',
        'url' => 'https://edm.com/.rss/full'
    ],
    [
        'name' => 'The Musical Hype',
        'url' => 'https://themusicalhype.com/feed'
    ],
    [
        'name' => 'NME Magazine',
        'url' => 'https://nme.com/feed'
    ],
    [
        'name' => 'BrooklynVegan',
        'url' => 'https://brooklynvegan.com/feed'
    ],
    [
        'name' => 'Okayplayer',
        'url' => 'https://okayplayer.com/feeds/feed.rss'
    ],
    [
        'name' => 'MTS Management News',
        'url' => 'https://mtsmanagementgroup.com/feed'
    ],
    [
        'name' => 'The Line of Best Fit',
        'url' => 'https://feeds.feedburner.com/theline..'
    ],
    [
        'name' => 'Hip-Hop Wired',
        'url' => 'https://hiphopwired.com/feed'
    ],
    [
        'name' => 'Chaospin',
        'url' => 'https://chaospin.com/feed'
    ],
    [
        'name' => 'Dansende Beren',
        'url' => 'https://dansendeberen.be/feed'
    ],
    [
        'name' => 'Dancing Astronaut',
        'url' => 'https://dancingastronaut.com/feed'
    ],
    [
        'name' => 'Greeblehaus » Music',
        'url' => 'https://greeblehaus.com/category/mus..'
    ],
    [
        'name' => 'Aquarium Drunkard',
        'url' => 'https://feeds.feedburner.com/AnAquar..'
    ],
    [
        'name' => 'The Groove Cartel',
        'url' => 'https://thegroovecartel.com/feed'
    ],
    [
        'name' => 'Nialler9',
        'url' => 'https://feeds.feedburner.com/nialler..'
    ],
    [
        'name' => 'Bong Mines Entertainment',
        'url' => 'https://bongminesentertainment.com/feed'
    ],
    [
        'name' => 'Muzique Magazine',
        'url' => 'https://muziquemagazine.com/feed'
    ],
    [
        'name' => 'I Care if You Listen',
        'url' => 'https://icareifyoulisten.com/feed'
    ],
    [
        'name' => 'Metal Underground.com',
        'url' => 'https://feeds.feedburner.com/metalun..'
    ],
    [
        'name' => 'PLAYY. Magazine',
        'url' => 'https://theplayground.co.uk/feed'
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

$cacheFile = $path . '/music.json';
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
