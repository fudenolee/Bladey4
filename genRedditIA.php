<?php

require __DIR__ . '/BaseFeedReddit.php';

$subs = ['aivideo', 'isthisAI', 'aivids', 'generativeAI', 'aifails', 'Aiimages', 'singularity', 'aiArt', 'aivideos'];

$merged = [];

foreach ($subs as $sub) {
    echo "Subreddit: $sub\n";

    $posts = fetchSubreddit($sub);

    if (!$posts)
        continue;

    foreach ($posts as $post) {
        $merged[] = $post;
    }

    echo "Sub {$sub}: " . count($posts) . " posts\n";
}

$cacheFile = __DIR__ . '/feedReddit/IA.json';
$tempFile = $cacheFile . '.tmp';

$json = json_encode($merged, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

if ($json === false) {
    echo json_last_error_msg();
    exit;
}

file_put_contents($tempFile, $json);
rename($tempFile, $cacheFile);

echo 'Total final: ' . count($merged);
