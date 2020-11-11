<?php
$api_url = "https://periscope.caida.org/api/v2";

// Construct the measurement request
$measurement = [
    "command" => "traceroute",
    "argument" => "192.51.100.7",
    "name" => "ixmaps",
    "hosts" => [
        ["asn" => 45177, "router" => "router2" ]
    ]
];
$data = json_encode($measurement);

# Calculate the HMAC signature
$public_key = 'andrew_clement_utoronto_ca';
$private_key = 'vw2KtF18RYRn0SSPZj0AP1xQm0NAakEKNJvE4ptI';
$signature = base64_encode(hash_hmac('sha256', $data, $private_key, TRUE));

# Set the headers
$headers = [
    'Content-type:application/json; charset=utf-8',
    'X-Public:' . $public_key,
    'X-Hash:' . $signature
];

print "Request headers:";
print_r($headers);
print "Request data:  " . $data . "\n";

# Post the data and headers
$ch = curl_init($api_url . "/measurement");
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
$response = curl_exec($ch);
$response_code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);

print "HTTP response status: " . curl_getinfo($ch, CURLINFO_RESPONSE_CODE) . "\n";
print "HTTP response text:  " . $response . "\n";

if ($response_code == 201) {
    $decoded_response = json_decode($response, 1);
    print "Measurement ID: " . $decoded_response["id"] . "\n";
} else {
    exit(1);
}