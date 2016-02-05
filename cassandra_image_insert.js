var request = require('request');
var cheerio = require('cheerio');
var cassandra = require('cassandra-driver');
var client = new cassandra.Client({contactPoints: ['172.31.18.149'], keyspace: 'userinterests'});
var crypto = require('crypto');
var fs = require('fs');

var spawn = require('child_process').spawn
var cmd = spawn('python',['/home/ubuntu/machine-learning-incollab/article_retriever.py']);

cmd.stdout.on('data',function(data){
    var parsed_data = JSON.parse(data);
    var image = parsed_data["image"];
    var article_id = parsed_data["article_id"];
    var current_count = parsed_data["current"];
    var total_count = parsed_data["total"];
    if (current_count == total_count)
    {
        console.log("\n\nFinished execution! Total \t" + total_count + " articles\n\n");
        process.exit(0);
    }
    console.log('[' + current_count + '/' + total_count + ']\tPrinting image:\t' + image);
    console.log('[' + current_count + '/' + total_count + ']\tPrinting article id:\t' + article_id);
    var base64image = base64_encode(image);
    insertimage(article_id, base64image, function(err) {
        if(!err)
        {
            console.log("Inserted image into Cassandra!");
	}
        else
        {
            console.log("ERROR!");
	}
    });
});

cmd.stderr.on('data',function(data){
    console.log('Stderr Python Prints:\n' + data);
});

var insertimage = function(articleid, articleimage, callback) {
    var str = "Insert into articleimage(articleid, articleimage) values (" + articleid + ", textAsBlob('" + articleimage + "'))";
    client.execute(str, function(err,result){
        if(!err){
            console.log("Image insert successful!");
        } else{
            console.log(err);
        }
    callback(err);
    });
};

function base64_encode(file) {
    // read binary data
    var bitmap = fs.readFileSync(file);
    // convert binary data to base64 encoded string
    return new Buffer(bitmap).toString('base64');
}


