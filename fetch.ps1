$TOKEN="1cc1e0a3b9756c6d357b1b7db80bc4806b263a92"

#curl -i -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/catalog/api/books/



#curl -i -X POST -H "Authorization: Token $TOKEN"  -H "Content-Type: application/json" -d '{"title":"Per Anhalter durch die Galaxis","author":1,"summary":"Antwort: 42.","isbn":"9783548234106"}' http://127.0.0.1:8000/catalog/api/books/


#curl -i -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/catalog/api/books/


$headers = @{ Authorization = "Token $TOKEN" }
$body = '{"title":"Per Anhalter durch die Galaxis","author":1,"summary":"Antwort: 42.","isbn":"9783548234107"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/catalog/api/books/ -Headers $headers -ContentType "application/json" -Body $body