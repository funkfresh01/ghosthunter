
# create index
 curl -XPUT http://localhost:9200/email_transactions/ '{
    "settings" : {
        "index" : {
            "number_of_shards" : 3,
            "number_of_replicas" : 2,
            "ttl" : { "enabled" : true, "default" : "90d" }
        }
    }
}'

# default expiration date MAPPING
 curl -XPUT 'http://localhost:9200/email_transactions/transactions/_mapping' -d '
{
    "expiration" : {
        "_ttl" : { "enabled" : true, "default" : "90d" }
    }

}
'
