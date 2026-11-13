<?php

$feeds = [
    [
        'name' => 'New York Times Health',
        'url' => 'http://www.nytimes.com/services/xml/rss/nyt/Health.xml'
    ],
    [
        'name' => 'BBC Health News',
        'url' => 'http://feeds.bbci.co.uk/news/health/rss.xml?edition=us'
    ],
    [
        'name' => 'ABC News - Health',
        'url' => 'http://feeds.abcnews.com/abcnews/healthheadlines'
    ],
    [
        'name' => 'Chicago Tribune - Health',
        'url' => 'http://www.chicagotribune.com/lifestyles/health/rss2.0.xml'
    ],
    [
        'name' => 'NY Daily News - Health',
        'url' => 'http://www.nydailynews.com/lifestyle/health/index_rss.xml'
    ],
    [
        'name' => "Men's Health",
        'url' => 'https://www.menshealth.com/rss/all.xml/'
    ],
    [
        'name' => 'New Scientist - Health',
        'url' => 'http://feeds.newscientist.com/health'
    ],
    [
        'name' => 'Time - Health',
        'url' => 'http://time.com/health/feed/'
    ],
    [
        'name' => 'Mayo Clinic Health Information',
        'url' => 'http://www.mayoclinic.org/rss/all-health-information-topics'
    ],
    [
        'name' => 'BuzzFeed News - Health',
        'url' => 'http://www.buzzfeed.com/health.xml'
    ],
    [
        'name' => 'Lifehacker',
        'url' => 'http://vitals.lifehacker.com/rss'
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

$cacheFile = $path . '/health.json';
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
