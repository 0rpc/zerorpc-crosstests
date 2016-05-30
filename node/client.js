const assert = require('assert');
var zerorpc = require("zerorpc");

var endpoint = process.argv[2];

var client = new zerorpc.Client();
client.connect(endpoint)

client.on("error", function(error) {
	console.error("RPC client error:", error);
	process.exit(-1);
});

var test_vals = [
	42,
	42.42,
	new Buffer('random bytes', 'ascii'),
	"unicode string",
];

var next_test = function() {
	if (test_vals.length == 0) {
		return quit_stage();
	}
	var v = test_vals.shift();
    console.log("sending %s <%s>", typeof(v), v);
	client.invoke("echo", v, function(error, r) {
		if(error) {
			console.error(error);
			process.exit(-1);
		} else {
			console.log("received %s <%s>", typeof(r), r);
			if (typeof(v) == 'object') {
				console.log("buffer equality");
				assert.ok(v.equals(r));
			} else {
				console.log("strict equality");
				assert.strictEqual(v, r);
			}
			next_test();
		}
	});
}
next_test();

function quit_stage() {
	client.invoke("quit", function(error, r) {
		if(error) {
			console.error(error);
			process.exit(-1);
		} else {
			console.log("All tests passed.");
			client.close();
		}
	});
}
