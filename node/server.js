var zerorpc = require("zerorpc");

var endpoint = process.argv[2];

var server = new zerorpc.Server({
	echo: function(v, reply) {
        console.log("echo %s <%s>", typeof(v), v);
		reply(null, v);
	},

	quit: function(reply) {
		console.log("exiting...");
		reply(null, null);
		server.close();
	},
});

server.bind(endpoint);

server.on("error", function(error) {
	console.error("RPC server error:", error);
});

console.log("Server started %s", endpoint);
