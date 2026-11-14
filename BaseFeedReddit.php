<?php

function fetchSubreddit($sub)
{
    $url = "https://www.reddit.com/r/{$sub}/.rss";

    $ch = curl_init($url);

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_USERAGENT => 'php:reddit-rss-aggregator:v1.0',
    ]);

    $response = curl_exec($ch);

    if ($response === false) {
        echo curl_error($ch);
        return null;
    }

    echo 'RSS carregado: ' . strlen($response) . " bytes\n";

    libxml_use_internal_errors(true);
    $xml = simplexml_load_string($response);

    if (!$xml) {
        echo "Erro lendo RSS {$sub}\n";
        return null;
    }

    echo "XML carregado\n";

    $posts = [];

    echo 'Entries encontradas: ' . count($xml->entry) . "\n";

    foreach ($xml->entry as $entry) {
        $title = (string) $entry->title;
        $link = (string) $entry->link['href'];
        $content = (string) $entry->content;

        $media = extrairMedia($content);

        if (!$media) {
            echo "Sem mídia\n";
        }

        if (!$media)
            continue;

        $posts[] = [
            'id' => md5($link),
            'title' => $title,
            'url' => $link,
            'ups' => 0,
            'comments' => 0,
            'type' => $media['type'],
            'media' => $media['url'],
            'aspectClass' => $media['aspectClass'] ?? 'aspect-video'
        ];
    }

    return $posts;
}

function extrairMedia($html)
{
    if (!$html)
        return null;

    // vídeo reddit
    if (preg_match('/<video.+?src="([^"]+)"/i', $html, $m)) {
        return [
            'type' => 'video',
            'url' => html_entity_decode($m[1]),
            'aspectClass' => 'aspect-video'
        ];
    }

    // imagem
    if (preg_match('/<img.+?src="([^"]+)"/i', $html, $m)) {
        return [
            'type' => 'image',
            'url' => html_entity_decode($m[1])
        ];
    }

    // gif
    if (preg_match('/\.(gif)/i', $html, $m)) {
        return [
            'type' => 'image',
            'url' => $m[0]
        ];
    }

    return null;
}
